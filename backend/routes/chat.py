from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
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

class ChatRequest(BaseModel):
    question: str

llm = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0.1,
    api_key=os.getenv("OPENAI_API_KEY"),
    streaming=True
)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# FIX: Converts Redis history (dicts/tuples) into LangChain Message Objects
import json # Ensure this is imported at the top

def map_history(history_list):
    messages = []
    for msg in history_list:
        # 1. AGAR MESSAGE PEHLE SE HI LANGCHAIN OBJECT HAI (Fix for your error)
        if isinstance(msg, BaseMessage):
            messages.append(msg)
            continue

        # 2. AGAR MESSAGE DICTIONARY HAI
        try:
            if isinstance(msg, str):
                data = json.loads(msg)
            elif isinstance(msg, dict):
                data = msg
            else:
                print(f"Unknown message type: {type(msg)}")
                continue
            
            role = data.get("role")
            content = data.get("content")
            
            if role in ["human", "user"]:
                messages.append(HumanMessage(content=content))
            elif role in ["ai", "assistant"]:
                messages.append(AIMessage(content=content))
        except Exception as e:
            print(f"Error parsing history message: {e}")
            continue
            
    return messages


async def generate_answer(chunks, chat_id, user_id, question):
    full_answer = ""
    db = SessionLocal()
    try:
        async for content in chunks:
            # Note: StrOutputParser makes 'content' a direct string
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
        yield f"\n[Error: {str(e)}]"
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
        history = get_chat_history(user_id)
        
        # 1. Initial entry
        chat_history = ChatHistory(
            user_id=user_id,
            question=request.question,
            answer="", 
            status="in_progress"
        )
        db.add(chat_history)
        db.commit()
        db.refresh(chat_history)
        chat_id = chat_history.id
        
        # 2. Vector DB & Chain setup
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

        # FIX: Added itemgetter for retriever and history mapping
        rag_chain = (
            {
                "context": itemgetter("question") | retriever | format_docs, 
                "question": itemgetter("question"),
                "history": lambda x: map_history(history)
            }
            | prompt
            | llm
            | StrOutputParser()
        )

        # 3. Stream start
        chunks = rag_chain.astream({"question": request.question})

        # 4. Response return
        return StreamingResponse(
            generate_answer(chunks, chat_id, user_id, request.question),
            media_type="text/plain"
        )

    except Exception as e:
        print(f"Setup Error: {e}")
        return {"error": f"Could not initiate chat: {str(e)}"}
    finally:
        db.close()