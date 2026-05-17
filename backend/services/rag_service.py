"""
RAG Service Module

This module contains all RAG (Retrieval-Augmented Generation) related operations:
- Question rewriting for context awareness
- Document retrieval from vector database
- Citation generation from retrieved documents
- RAG chain construction and execution
"""

from operator import itemgetter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

from embeddings import get_embeddings
from utils.llm_config import (
    get_question_rewriter_llm,
    get_final_answer_llm,
    PromptTemplates,
    RAGConfig
)


async def rewrite_question(question: str, chat_history: list) -> str:
    """
    Rewrite a user question into a standalone question using chat history context.
    
    Args:
        question: The original user question
        chat_history: List of previous messages in LangChain format
        
    Returns:
        Standalone question rewritten for clarity without chat history context
    """
    rewrite_llm = get_question_rewriter_llm()
    
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", PromptTemplates.CONTEXTUALIZE_QUESTION_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ])
    
    question_rewriter_chain = (
        contextualize_q_prompt
        | rewrite_llm
        | StrOutputParser()
    )
    
    standalone_question = await question_rewriter_chain.ainvoke({
        "question": question,
        "history": chat_history
    })
    
    return standalone_question


async def retrieve_documents(question: str, user_id: int) -> list:
    """
    Retrieve relevant documents from the vector database using the question.
    
    Args:
        question: The standalone question to use for retrieval
        user_id: User ID to access their personal collection
        
    Returns:
        List of retrieved documents with metadata
    """
    embeddings = get_embeddings()
    
    vectors_db = Chroma(
        persist_directory=RAGConfig.VECTOR_DB_PERSIST_DIR,
        embedding_function=embeddings,
        collection_name=f"user_{user_id}"
    )
    
    retriever = vectors_db.as_retriever(
        search_kwargs={"k": RAGConfig.RETRIEVER_SEARCH_K}
    )
    
    docs = await retriever.ainvoke(question)
    
    return docs


def generate_citations(docs: list) -> list:
    """
    Generate structured citations from retrieved documents.
    
    Args:
        docs: List of retrieved documents with metadata
        
    Returns:
        List of citation dictionaries with source info and snippets
    """
    citations = []
    
    for i, doc in enumerate(docs):
        citation = {
            "source_index": i + 1,
            "file_name": doc.metadata.get("file_name", "Unknown"),
            "snippet": _truncate_snippet(doc.page_content)
        }
        citations.append(citation)
    
    return citations


def _truncate_snippet(content: str, max_length: int = RAGConfig.CITATION_SNIPPET_LENGTH) -> str:
    """
    Truncate document content to a maximum length.
    
    Args:
        content: The document content
        max_length: Maximum length of the snippet
        
    Returns:
        Truncated content with ellipsis if needed
    """
    if len(content) > max_length:
        return content[:max_length] + "..."
    return content


def format_docs(docs: list) -> str:
    """
    Format a list of documents into a single string for use in prompts.
    
    Args:
        docs: List of document objects
        
    Returns:
        Formatted documents as newline-separated content
    """
    return "\n\n".join(doc.page_content for doc in docs)


def build_rag_chain():
    """
    Build the RAG (Retrieval-Augmented Generation) chain.
    
    The chain takes pre-fetched documents and streams the answer while
    incorporating context from those documents.
    
    Returns:
        A LangChain runnable chain for RAG operations
    """
    llm = get_final_answer_llm()
    
    answer_prompt = ChatPromptTemplate.from_messages([
        ("system", PromptTemplates.ANSWER_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")
    ])
    
    # RAG chain with pre-fetched docs
    rag_chain = (
        {
            "context": itemgetter("docs") | RunnableLambda(format_docs),
            "question": itemgetter("question"),
            "history": itemgetter("history")
        }
        | answer_prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain
