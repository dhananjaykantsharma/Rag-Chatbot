from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from embeddings import get_embeddings
from utils.auth_utils import get_current_user
from utils.redis_util import get_chat_history
from utils.chat_utils import map_history, generate_answer
from models import ChatHistory
from operator import itemgetter
from database import SessionLocal
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

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/ask")
async def chat(
    request: ChatRequest, 
    current_user: dict = Depends(get_current_user)
):
    print(f"Received question: {request.question} from user_id: {current_user['user_id']}")
    db = SessionLocal()
    try:
        user_id = current_user["user_id"]
        history = get_chat_history(user_id)

        print(f"Retrieved history for user_id {user_id}: {history}")
        
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

        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", 
             """
            Given a chat history and a latest user question,
            rewrite the question into a standalone question.

            Do not Answer the question,
            just rewrite it in a way that it can be understood without the chat history.

            If question is already standalone, just return the same question.
            """),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ])
        
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

        print("Chat chain setup complete. Starting streaming response...", prompt)

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