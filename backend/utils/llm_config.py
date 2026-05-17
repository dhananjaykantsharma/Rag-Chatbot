"""
LLM Configuration and Constants

This module contains all LLM configurations, model settings, and constants
used across the chatbot application.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


class LLMConfig:
    """Configuration for LLM models"""
    
    MODEL_NAME = "gpt-4o-mini"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Final answer LLM configuration - streaming enabled
    FINAL_ANSWER_LLM_CONFIG = {
        "model": MODEL_NAME,
        "temperature": 0.1,
        "api_key": OPENAI_API_KEY,
        "streaming": True
    }
    
    # Question rewriting LLM configuration - streaming disabled
    QUESTION_REWRITER_LLM_CONFIG = {
        "model": MODEL_NAME,
        "temperature": 0,
        "api_key": OPENAI_API_KEY,
        "streaming": False
    }


class PromptTemplates:
    """Prompt templates for RAG operations"""
    
    CONTEXTUALIZE_QUESTION_SYSTEM_PROMPT = """
Given a chat history and the latest user question,
rewrite the question into a standalone question.

Do not answer the question.
Just rewrite it in a way that it can be understood
without the chat history.

If the question is already standalone,
return the same question.
"""

    ANSWER_SYSTEM_PROMPT = """
You are a helpful assistant.

Use the following context to answer the user's question.

Context:
{context}

If the answer is not available in the context, say:
"I don't have enough information in the uploaded documents."
"""


class RAGConfig:
    """Configuration for RAG operations"""
    
    VECTOR_DB_PERSIST_DIR = "./chroma_db"
    RETRIEVER_SEARCH_K = 3
    MAX_CHAT_HISTORY_LIMIT = 10
    CITATION_SNIPPET_LENGTH = 200


def get_final_answer_llm():
    """Get the final answer LLM instance"""
    return ChatOpenAI(**LLMConfig.FINAL_ANSWER_LLM_CONFIG)


def get_question_rewriter_llm():
    """Get the question rewriter LLM instance"""
    return ChatOpenAI(**LLMConfig.QUESTION_REWRITER_LLM_CONFIG)
