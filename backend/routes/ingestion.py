from fastapi import APIRouter, Depends
from fastapi import HTTPException
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from supabase import create_client, Client
from utils.auth_utils import get_current_user
import tempfile
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "rag-chatbot")  

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY, )

embeddings  = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={ "device": "cpu" }
)

@router.post("/ingestion")
async def ingestion(
    current_user: dict = Depends(get_current_user)
    ):
    user_id = current_user["user_id"]
    folder_path = f"datasource/{user_id}"

    # get all the datasource of a user from supabase
    try:
        files = supabase.storage.from_(SUPABASE_BUCKET).list(folder_path)
        print(f"[DEBUG] Files found: {[f['name'] for f in files]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching datasource: {str(e)}")
    
    if not files:
        raise HTTPException(status_code=404, detail="No datasource found for the user.")
    
    supported_extensions = {"pdf", "txt"}
    all_chunks = []
    processed_files = []
    failed_files = []

    for file in files:
        file_name = file["name"]
        ext = file_name.split(".")[-1].lower()
        if ext not in supported_extensions:
            print(f"Skipping unsupported file type: {file_name}")
            continue

        file_path = f"{folder_path}/{file_name}"

    
        # Download the file from Supabase
        try:
            signed = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(
                path=file_path,
                expires_in=120
            )
            download_url = signed["signedURL"]

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f".{ext}",
                prefix=f"user_{user_id}_"
            ) as temp:
                temp_path = temp.name
                response = httpx.get(download_url)
                response.raise_for_status()
                temp.write(response.content)
        
        except:
            print(f"[ERROR] Download failed for {file_name}: {e}")
            failed_files.append(file_name)
            continue

        # load document and split
        try:
            if ext == "pdf":
                loader = PyPDFLoader(temp_path)
            else:
                loader = TextLoader(temp_path)

            documents = loader.load()

            for doc in documents:
                doc.metadata["user_id"] = user_id
                doc.metadata["source_file"] = file_name

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", "", " "]
            )
            chunks = text_splitter.split_documents(documents)
            all_chunks.extend(chunks)
            processed_files.append(file_name)
            print(f"[OK] {file_name} → {len(chunks)} chunks")

        except Exception as e:
            print(f"[ERROR] Processing failed for {file_name}: {e}")
            failed_files.append(file_name)

        finally:
            # ── Step 4: Temp file hamesha delete karo ────────────────────────
            if os.path.exists(temp_path):
                os.remove(temp_path)

        # store the user to the chroma collection
        try:

            collection_name = f"user_{user_id}"

            Chroma.from_documents(
                documents=all_chunks,
                embedding=embeddings,
                persist_directory="./chroma_db",
                collection_name=collection_name
            )
            print(f"[OK] Ingested {len(all_chunks)} chunks into collection '{collection_name}'")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Vector DB error: {str(e)}")

    return {
        "message": "Ingestion complete",
        "collection": f"user_{user_id}",
        "processed_files": processed_files,
        "failed_files": failed_files,
        "total_chunks": len(all_chunks),
        "failed_files": failed_files
    }
                

        