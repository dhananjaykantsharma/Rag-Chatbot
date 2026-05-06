from fastapi import APIRouter, Depends
from fastapi import HTTPException
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from supabase import create_client, Client
from database import get_db
from utils.auth_utils import get_current_user
from sqlalchemy.orm import Session
from models import Datasource
import tempfile
import os
import httpx
import urllib.parse
from dotenv import load_dotenv
from embeddings import get_embeddings

load_dotenv()

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "rag-chatbot")  

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY, )

@router.post("/ingestion")
async def ingestion(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    
    datasources = (
        db.query(Datasource)
        .filter(
            Datasource.user_id == user_id,
            Datasource.status == "to_ingest" 
        )
        .all()
    )

    if not datasources:
        return {"message": "No new datasources to ingest."}
    
    supported_extensions = {"pdf", "txt"}
    all_chunks = []
    processed_ids = []
    failed_files = []

    for ds in datasources:
        # DB se full path aur ID lo
        full_url = ds.file_path 
        file_id = ds.id
        
        # Extension nikalo
        ext = full_url.split(".")[-1].split("?")[0].lower()
        if ext not in supported_extensions:
            print(f"Skipping unsupported: {full_url}")
            continue

        # URL decode karke storage path nikalo (Jaisa humne delete logic mein kiya tha)
        # Assuming URL contains bucket name
        try:
            path_in_bucket = urllib.parse.unquote(full_url.split(f"{SUPABASE_BUCKET}/")[-1])
            
            # Download using signed URL
            signed = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(
                path=path_in_bucket,
                expires_in=120
            )
            download_url = signed["signedURL"]

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as temp:
                temp_path = temp.name
                async with httpx.AsyncClient() as client:
                    response = await client.get(download_url)
                    response.raise_for_status()
                    temp.write(response.content)

            # Processing (PDF/Text)
            if ext == "pdf":
                loader = PyPDFLoader(temp_path)
            else:
                loader = TextLoader(temp_path)

            documents = loader.load()
            for doc in documents:
                doc.metadata["user_id"] = user_id
                doc.metadata["datasource_id"] = str(file_id) # ID track karne ke liye

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, 
                chunk_overlap=200
            )
            chunks = text_splitter.split_documents(documents)
            all_chunks.extend(chunks)
            
            processed_ids.append(file_id) # Success IDs list
            print(f"[OK] Processed: {ds.file_name}")

        except Exception as e:
            print(f"[ERROR] Failed {ds.file_name}: {e}")
            failed_files.append(ds.file_name)
        finally:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)

    if all_chunks:
        try:
            embeddings = get_embeddings()
            collection_name = f"user_{user_id}"
            Chroma.from_documents(
                documents=all_chunks,
                embedding=embeddings,
                persist_directory="./chroma_db",
                collection_name=collection_name
            )
            
            db.query(Datasource).filter(Datasource.id.in_(processed_ids)).update(
                {"status": "ingested"}, 
                synchronize_session=False
            )
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Vector DB/Status Update error: {str(e)}")

    return {
        "message": "Ingestion complete",
        "ingested_count": len(processed_ids),
        "failed_files": failed_files
    }    