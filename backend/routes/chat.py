from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from embeddings import get_embeddings
from utils.auth_utils import get_current_user
from utils.redis_util import get_chat_history, add_message_to_history
from models import ChatHistory
from operator import itemgetter
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

async def generate_answer(chunks, chat_id, user_id, question):
    full_answer = ""
    db = SessionLocal()
    try:
        async for chunk in chunks:
            # Chunk ko string mein convert karne ka sabse safe tarika
            if isinstance(chunk, dict):
                # Agar chunk dictionary hai, toh usme se text nikalne ki koshish karein
                content = chunk.get("content", "") or chunk.get("text", "") or str(chunk)
            elif hasattr(chunk, "content"):
                content = chunk.content # AIMessageChunk case
            else:
                content = str(chunk)

            if content:
                full_answer += content
                yield content
                await asyncio.sleep(0.01)

        # Success: Redis and DB storage
        add_message_to_history(user_id, "human", question)
        add_message_to_history(user_id, "ai", full_answer)

        chat_entry = db.query(ChatHistory).filter(ChatHistory.id == chat_id).first()
        if chat_entry:
            chat_entry.answer = full_answer
            chat_entry.status = "completed"
            db.commit()

    except Exception as e:
        print(f"Streaming Error inside generator: {e}")
        # Error handling code...
        yield f"\n[Error: {str(e)}]"

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/ask")
async def chat(
    request: ChatRequest, 
    current_user: dict = Depends(get_current_user)
):
    db = SessionLocal()
    try:
        user_id = current_user["user_id"]

        history = get_chat_history(user_id)
        print(f"Chat history for user {user_id}: {history}")
        
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
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ])

        print("prompt:", prompt)

        rag_chain = (
            {
                "context": retriever | format_docs, 
                "question": itemgetter("question"),
                "history": lambda x: history
            }
            | prompt
            | llm
            | StrOutputParser()
        )

        # 3. Stream start karein
        chunks = rag_chain.astream(
            {
                "question": request.question,
            }
        )

        # 4. Response return karein, DB update generator ke andar hoga
        return StreamingResponse(
            generate_answer(chunks, chat_id, user_id, request.question),
            media_type="text/plain"
        )

    except Exception as e:
        print(f"Setup Error: {e}")
        return {"error": "Could not initiate chat."}
    finally:
        db.close()