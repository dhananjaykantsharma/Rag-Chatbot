from fastapi import APIRouter, UploadFile, File
from fastapi import HTTPException
import shutil
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/upload")
def upload_file(file: UploadFile = File(...)):
    # Here you would handle the file upload and processing logic
    file_type = file.filename.split(".")[-1].lower()
    print(f"Received file: {file.filename} of type: {file_type}")
    if not file or file_type not in ["pdf", "txt"]:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type, only PDF, DOCX and TEXT are allowed."
        )

    temp_file = f"temp_{file.filename}"

    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Load the document using the appropriate loader based on file type
        if file_type == "pdf":
            loader = PyPDFLoader(temp_file)
        elif file_type == "txt":
            loader = TextLoader(temp_file, encoding='utf-8')

        documents = loader.load()
        print(f"Loaded {len(documents)} documents from {file.filename}")

        # Optionally, you can split the documents into smaller chunks using a text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

        chunk = text_splitter.split_documents(documents)
        
        print(f"Split into {len(chunk)} chunks")

        # creating the embeddings for the chunks
        embeddings  = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={ "device": "cpu" }
        )

        vectors_db = Chroma.from_documents(
            documents=chunk,
            embedding=embeddings,
            persist_directory="./chroma_db",
            collection_name="documents"
        )

        print("Documents ingested and embeddings created successfully.", vectors_db)
        return {
            "message": f"File '{file.filename}' uploaded and processed successfully.",
            "num_documents": len(documents),
            "num_chunks": len(chunk)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
