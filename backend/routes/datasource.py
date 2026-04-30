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

supabase : Client = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter(prefix="/datasource", tags=["Datasource"])

@router.post("/upload")
async def upload_datasource(
    db: Session = Depends(get_db), 
    file: UploadFile = File(...), 
    current_user: dict = Depends(get_current_user)
    ):
    try:
        print(f"[DEBUG] upload_datasource started")
        file_content = await file.read()
        
        # User ID check (Logs ke mutabik 'user_id' key hai)
        user_id = current_user['user_id'] 
        
        # Aapki requirement: datasource/{user_id}/filename_uuid
        # Hum filename se extension nikal kar beech mein uuid daalenge
        name, ext = os.path.splitext(file.filename)
        unique_name = f"{name}_{uuid.uuid4()}{ext}"
        file_path = f"datasource/{user_id}/{unique_name}"

        print(f"[DEBUG] Target Path: {file_path}")

        # ISSUE FIX: Sirf upload call karein, .text ya .data use na karein
        supabase.storage.from_("rag-chatbot").upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file.content_type}
        )

        # URL nikalne ka sahi tarika
        response_url = supabase.storage.from_("rag-chatbot").get_public_url(file_path)
        file_url = str(response_url)

        # Database entry
        new_ds = Datasource(
            user_id=user_id,
            file_name=file.filename,
            file_path=file_url,
            file_type=file.content_type,
            file_size=len(file_content)
        )

        db.add(new_ds)
        db.commit()

        return {"message": "Success", "url": file_url}

    except Exception as e:
        print(f"[DEBUG] Error details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))