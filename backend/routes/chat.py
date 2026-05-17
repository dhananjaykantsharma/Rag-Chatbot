import os
from operator import itemgetter
import json
import dotenv

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

from embeddings import get_embeddings
from utils.auth_utils import get_current_user
from utils.redis_util import get_chat_history
from utils.chat_utils import map_history, generate_answer
from models import ChatHistory
from database import SessionLocal

dotenv.load_dotenv()


class ChatRequest(BaseModel):
    question: str


# Final answer LLM - streaming enabled
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    api_key=os.getenv("OPENAI_API_KEY"),
    streaming=True
)


# Question rewriting LLM - streaming disabled
rewrite_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),
    streaming=False
)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask")
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    print(
        f"Received question: {request.question} "
        f"from user_id: {current_user['user_id']}"
    )

    db = SessionLocal()

    try:
        user_id = current_user["user_id"]

        # Get chat history from Redis
        history = get_chat_history(user_id)

        print(f"Retrieved history for user_id {user_id}: {history}")

        # 1. Create initial chat history entry in DB
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

        # 2. Contextual question rewriting prompt
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                Given a chat history and the latest user question,
                rewrite the question into a standalone question.

                Do not answer the question.
                Just rewrite it in a way that it can be understood
                without the chat history.

                If the question is already standalone,
                return the same question.
                """
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ])

        question_rewriter_chain = (
            contextualize_q_prompt
            | rewrite_llm
            | StrOutputParser()
        )

        # 3. Rewrite latest user question into standalone question
        formatted_history = map_history(history)

        standalone_question = await question_rewriter_chain.ainvoke({
            "question": request.question,
            "history": formatted_history
        })

        print("Standalone question:", standalone_question)

        # 4. Vector DB setup & Single Retrieval Fetch
        embeddings = get_embeddings()

        vectors_db = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings,
            collection_name=f"user_{user_id}"
        )

        retriever = vectors_db.as_retriever(
            search_kwargs={"k": 3}
        )
        
        # Fetch the relevant documents from Chroma once
        docs = await retriever.ainvoke(standalone_question)
        
        # Safely compile the citations list
        citations = []
        for i, doc in enumerate(docs):
            citations.append({
                "source_index": i + 1,
                "file_name": doc.metadata.get("file_name", "Unknown"),
                "snippet": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            })

        # 5. Final answer prompt
        answer_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                You are a helpful assistant.

                Use the following context to answer the user's question.

                Context:
                {context}

                If the answer is not available in the context, say:
                "I don't have enough information in the uploaded documents."
                """
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}")
        ])

        print("Chat chain setup complete. Starting streaming response...")

        # 6. Final RAG chain (Receives pre-fetched 'docs')
        rag_chain = (
            {
                # We use RunnableLambda to make format_docs compatible with the | operator
                "context": itemgetter("docs") | RunnableLambda(format_docs),
                "question": itemgetter("question"),
                "history": itemgetter("history")
            }
            | answer_prompt
            | llm
            | StrOutputParser()
        )

        # 7. Start streaming chunks from OpenAI
        chunks = rag_chain.astream({
            "docs": docs,
            "question": request.question,
            "history": formatted_history
        })

        # 8. Define the wrapper to stream citations first, then words
        async def stream_with_citations_wrapper():
            # Packet 1: Send citations structured as a single line JSON string
            yield json.dumps({"type": "citations", "data": citations}) + "\n"
            
            # Packet 2+: Stream the answer tokens as they arrive
            async for chunk in generate_answer(
                chunks,
                chat_id,
                user_id,
                request.question
            ):
                yield json.dumps({"type": "text", "data": chunk}) + "\n"

        # Return streaming response with newline-delimited JSON media type
        return StreamingResponse(
            stream_with_citations_wrapper(),
            media_type="application/x-ndjson"
        )

    except Exception as e:
        print(f"Setup Error: {e}")

        return {
            "error": f"Could not initiate chat: {str(e)}"
        }

    finally:
        db.close()