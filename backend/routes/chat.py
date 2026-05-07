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

# Step 2: Wrap it with ChatHuggingFace so LangChain treats it as
# a chat model (handles message formatting internally)
# llm = ChatHuggingFace(llm=endpoint)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

async def generate_answer(chunks):
    try:
        async for chunk in chunks:
            yield chunk
            await asyncio.sleep(0.05)
    except Exception as e:
        print(f"Error generating answer: {e}")
        yield "An error occurred while generating the answer."


router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/ask")
def chat(
    request: ChatRequest, 
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user["user_id"]
        embeddings = get_embeddings()
        collection_name = f"user_{user_id}"
        vectors_db = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings,
            collection_name=collection_name
        )

        retriever = vectors_db.as_retriever(
            search_kwargs={"k": 3}
        )

        # Step 3: Use ChatPromptTemplate (not PromptTemplate) since
        # ChatHuggingFace expects structured messages, not raw strings
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a helpful assistant. Use the following context to answer the question. "
                "If the answer is not in the context, say you don't know.\n\n"
                "Context: {context}"
            )),
            ("human", "{question}"),
        ])

        rag_chain = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough(),
            }
            | prompt
            | llm
            | StrOutputParser()
        )

        chunks = rag_chain.astream(request.question)

        return StreamingResponse(
            generate_answer(chunks),
            media_type="text/plain"
        )
    
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return {"error": "An error occurred while processing your request."}