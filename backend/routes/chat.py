from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from embeddings import get_embeddings
from utils.auth_utils import get_current_user
from models import ChatHistory
from database import SessionLocal
import asyncio
import os
import dotenv

dotenv.load_dotenv()

hugging_face_api_key = os.getenv("HUGGING_FACE_API_KEY")

class ChatRequest(BaseModel):
    question: str

# Step 1: Create the endpoint with task="conversational" to match
# what featherless-ai supports for this model
llm = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0.1,
    api_key=os.getenv("OPENAI_API_KEY"),
    streaming=True
)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

async def generate_answer(chunks, chat_id):
    # Streaming ke sath sath hum answer build karenge
    full_answer = ""
    db = SessionLocal()
    try:
        async for chunk in chunks:
            full_answer += chunk
            yield chunk
            # Thoda sleep taaki frontend par "typing" effect dikhe
            await asyncio.sleep(0.02) 

        # --- Success Case ---
        # Jab loop successfully khatam ho jaye
        chat_entry = db.query(ChatHistory).filter(ChatHistory.id == chat_id).first()
        if chat_entry:
            chat_entry.answer = full_answer
            chat_entry.status = "completed"
            db.commit()

    except Exception as e:
        # --- Fail Case ---
        print(f"Streaming Error: {e}")
        chat_entry = db.query(ChatHistory).filter(ChatHistory.id == chat_id).first()
        if chat_entry:
            chat_entry.answer = "An error occurred while generating the answer."
            chat_entry.status = "error"
            db.commit()
        yield "\n[Error: Connection Interrupted]"
        
    finally:
        db.close()


router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/ask")
async def chat(
    request: ChatRequest, 
    current_user: dict = Depends(get_current_user)
):
    db = SessionLocal()
    try:
        user_id = current_user["user_id"]
        
        # 1. Initial entry (Status: in_progress)
        chat_history = ChatHistory(
            user_id=user_id,
            question=request.question,
            answer="", 
            status="in_progress"
        )
        db.add(chat_history)
        db.commit()
        db.refresh(chat_history)
        chat_id = chat_history.id # Unique ID save karli
        
        # 2. Vector DB & Chain setup (Existing logic)
        embeddings = get_embeddings()
        vectors_db = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings,
            collection_name=f"user_{user_id}"
        )
        retriever = vectors_db.as_retriever(search_kwargs={"k": 3})

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Context: {context}"),
            ("human", "{question}"),
        ])

        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        # 3. Stream start karein
        chunks = rag_chain.astream(request.question)

        # 4. Response return karein, DB update generator ke andar hoga
        return StreamingResponse(
            generate_answer(chunks, chat_id),
            media_type="text/plain"
        )

    except Exception as e:
        print(f"Setup Error: {e}")
        return {"error": "Could not initiate chat."}
    finally:
        db.close()