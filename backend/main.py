from fastapi import FastAPI
from routes.ingestion import router as ingestion_router
from routes.chat import router as chat_router
from routes.auth import router as auth_router


app = FastAPI()


@app.get("/")
def health_check():
    return {"message": "RAG Chatbot API is running!"}


app.include_router(ingestion_router)
app.include_router(chat_router)
app.include_router(auth_router)