import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

embeddings = None


def get_embeddings():
    global embeddings
    if embeddings is None:
        print("[startup] loading HuggingFace embeddings model...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
        print("[startup] HuggingFace embeddings model loaded")
    return embeddings


def init_embeddings():
    return get_embeddings()
