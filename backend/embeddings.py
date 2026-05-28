import os
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings

load_dotenv()

embeddings = None


def get_embeddings():
    global embeddings
    hf_api_key = os.getenv("HUGGING_FACE_API_KEY")
    if hf_api_key is None:
        raise ValueError("HUGGING_FACE_API_KEY environment variable is not set")
    if embeddings is None:
        print("[startup] loading HuggingFace embeddings model...")
        embeddings = HuggingFaceInferenceAPIEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            api_key=hf_api_key
        )
        print("[startup] HuggingFace embeddings model loaded")
    return embeddings


def init_embeddings():
    return get_embeddings()
