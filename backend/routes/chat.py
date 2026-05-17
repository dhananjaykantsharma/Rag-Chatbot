import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from utils.auth_utils import get_current_user
from utils.redis_util import get_chat_history
from utils.chat_utils import map_history, generate_answer
from services.rag_service import (
    rewrite_question,
    retrieve_documents,
    generate_citations,
    build_rag_chain
)
from services.chat_db_service import create_chat_history, update_chat_history_answer


class ChatRequest(BaseModel):
    question: str


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask")
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Chat endpoint that processes user questions using RAG (Retrieval-Augmented Generation).
    
    Flow:
    1. Retrieve chat history from Redis
    2. Create chat history entry in database
    3. Rewrite question for context awareness
    4. Retrieve relevant documents from vector database
    5. Generate citations from retrieved documents
    6. Build and stream RAG chain response
    7. Save answer to Redis and database
    
    Returns:
        StreamingResponse with newline-delimited JSON containing citations and answer chunks
    """
    
    print(
        f"Received question: {request.question} "
        f"from user_id: {current_user['user_id']}"
    )

    try:
        user_id = current_user["user_id"]

        # Step 1: Get chat history from Redis
        history = get_chat_history(user_id)
        print(f"Retrieved history for user_id {user_id}: {history}")

        # Step 2: Create initial chat history entry in database
        chat_id = create_chat_history(user_id, request.question)

        # Step 3: Convert chat history to LangChain format
        formatted_history = map_history(history)

        # Step 4: Rewrite question to be standalone
        standalone_question = await rewrite_question(
            request.question, 
            formatted_history
        )
        print("Standalone question:", standalone_question)

        # Step 5: Retrieve relevant documents from vector database
        docs = await retrieve_documents(standalone_question, user_id)

        # Step 6: Generate citations from retrieved documents
        citations = generate_citations(docs)

        # Step 7: Build RAG chain for streaming
        print("Chat chain setup complete. Starting streaming response...")
        rag_chain = build_rag_chain()

        # Step 8: Start streaming chunks from OpenAI
        chunks = rag_chain.astream({
            "docs": docs,
            "question": request.question,
            "history": formatted_history
        })

        # Step 9: Define streaming response with citations and answer
        async def stream_with_citations_wrapper():
            # Send citations first as structured JSON
            yield json.dumps({"type": "citations", "data": citations}) + "\n"
            
            # Stream the answer tokens with database/Redis persistence
            async for chunk in generate_answer(
                chunks,
                chat_id,
                user_id,
                request.question
            ):
                yield json.dumps({"type": "text", "data": chunk}) + "\n"

        return StreamingResponse(
            stream_with_citations_wrapper(),
            media_type="application/x-ndjson"
        )

    except Exception as e:
        print(f"Setup Error: {e}")
        return {
            "error": f"Could not initiate chat: {str(e)}"
        }