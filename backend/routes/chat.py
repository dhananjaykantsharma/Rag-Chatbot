from fastapi import APIRouter
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint, ChatHuggingFace
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import os
import dotenv

dotenv.load_dotenv()

hugging_face_api_key = os.getenv("HUGGING_FACE_API_KEY")

class ChatRequest(BaseModel):
    question: str

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)

# Step 1: Create the endpoint with task="conversational" to match
# what featherless-ai supports for this model
llm = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0.1,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Step 2: Wrap it with ChatHuggingFace so LangChain treats it as
# a chat model (handles message formatting internally)
# llm = ChatHuggingFace(llm=endpoint)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/ask")
def chat(request: ChatRequest):
    vectors_db = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings,
        collection_name="documents"
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

    answer = rag_chain.invoke(request.question)

    return {"answer": answer}