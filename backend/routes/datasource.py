from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from numpy import rint
from sqlalchemy.orm import Session
from database import get_db
from utils.auth_utils import get_current_user
from supabase import create_client, Client
from models import Datasource
from langchain_chroma import Chroma
from embeddings import get_embeddings
import urllib.parse
import uuid
import os
import dotenv

dotenv.load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "rag-chatbot")  # ✅ Not hardcoded

print(f"[DEBUG] KEY starts with: {SUPABASE_KEY[:20] if SUPABASE_KEY else 'NONE'}")
print(f"[DEBUG] URL: {SUPABASE_URL}")
print(f"[DEBUG] BUCKET: {SUPABASE_BUCKET}")

MAX_FILE_SIZE_MB = 10
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter(prefix="/datasource", tags=["Datasource"])

@router.post("/upload")
async def upload_datasource(
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    # ✅ Validate file type early, before reading content
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}",
        )

    file_content = await file.read()

    # ✅ Enforce file size limit
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if len(file_content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_MB}MB",
        )

    user_id = current_user["user_id"]
    name, ext = os.path.splitext(file.filename)
    unique_name = f"{name}_{uuid.uuid4()}{ext}"
    file_path = f"datasource/{user_id}/{unique_name}"

    # ✅ Upload to Supabase
    supabase.storage.from_(SUPABASE_BUCKET).upload(
        path=file_path,
        file=file_content,
        file_options={"content-type": file.content_type},
    )

    # ✅ Safely extract the URL string
    public_url_response = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_path)
    file_url = (
        public_url_response
        if isinstance(public_url_response, str)
        else public_url_response.get("publicURL") or public_url_response.get("publicUrl", "")
    )

    # ✅ Rollback DB on failure to avoid orphaned Supabase files going untracked
    try:
        new_ds = Datasource(
            user_id=user_id,
            file_name=file.filename,
            file_path=file_url,
            file_type=file.content_type,
            file_size=len(file_content),
        )
        db.add(new_ds)
        db.commit()
    except Exception as db_error:
        db.rollback()
        # Supabase file is now orphaned — log this for manual cleanup
        print(f"[ERROR] DB commit failed after upload. Orphaned path: {file_path}. Error: {db_error}")
        raise HTTPException(status_code=500, detail="File uploaded but database record failed.")

    return {"message": "Success", "url": file_url}

@router.get("/list-datasources")
async def list_datasources(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    datasources =  db.query(Datasource).filter(Datasource.user_id == user_id).all()
    if datasources is None:
        raise HTTPException(status_code=404, detail="No datasources found for user.")
    return datasources

@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_datasource(
    datasource_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]

    datasource = (
        db.query(Datasource)
        .filter(Datasource.id == datasource_id, Datasource.user_id == user_id)
        .first()
    )

    if not datasource:
        raise HTTPException(status_code=404, detail="Datasource not found.")

    try:
        # --- NEW: VECTOR DB SE CHUNKS DELETE KARNA ---
        embeddings = get_embeddings()
        collection_name = f"user_{user_id}"
        vector_db = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        # Metadata filter use karke delete karein
        # Note: Ingestion mein humne datasource_id ko string banaya tha: str(file_id)
        vector_db.delete(where={"datasource_id": str(datasource_id)})
        print(f"[DEBUG] Chunks deleted for datasource_id: {datasource_id}")
        # ---------------------------------------------

        # 2. Supabase Storage se file delete karna
        full_url = datasource.file_path 
        path_in_bucket = full_url.split(f"{SUPABASE_BUCKET}/")[-1]
        decoded_path = urllib.parse.unquote(path_in_bucket)
        
        storage_response = supabase.storage.from_(SUPABASE_BUCKET).remove([decoded_path])

        # 3. SQL Database se record delete karna
        db.delete(datasource)
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))