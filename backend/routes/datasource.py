from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from database import get_db
from utils.auth_utils import get_current_user
from supabase import create_client, Client
from models import Datasource
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