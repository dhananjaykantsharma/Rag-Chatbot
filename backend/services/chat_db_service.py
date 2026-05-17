"""
Chat Database Service Module

This module handles all database operations related to chat history,
including creating, retrieving, and updating chat records.
"""

from models import ChatHistory
from database import SessionLocal


def create_chat_history(user_id: int, question: str) -> str:
    """
    Create a new chat history entry in the database.
    
    Args:
        user_id: The user ID
        question: The user's question
        
    Returns:
        The ID of the created chat history entry
    """
    db = SessionLocal()
    
    try:
        chat_history = ChatHistory(
            user_id=user_id,
            question=question,
            answer="",
            status="in_progress"
        )
        
        db.add(chat_history)
        db.commit()
        db.refresh(chat_history)
        
        return chat_history.id
    finally:
        db.close()


def update_chat_history_answer(chat_id: str, answer: str) -> bool:
    """
    Update a chat history entry with the answer and mark it as completed.
    
    Args:
        chat_id: The chat history ID
        answer: The generated answer
        
    Returns:
        True if update was successful, False otherwise
    """
    db = SessionLocal()
    
    try:
        chat_entry = db.query(ChatHistory).filter(ChatHistory.id == chat_id).first()
        
        if chat_entry:
            chat_entry.answer = answer
            chat_entry.status = "completed"
            db.commit()
            return True
        
        return False
    finally:
        db.close()


def get_chat_history_by_id(chat_id: str) -> ChatHistory or None:
    """
    Retrieve a chat history entry by its ID.
    
    Args:
        chat_id: The chat history ID
        
    Returns:
        ChatHistory object or None if not found
    """
    db = SessionLocal()
    
    try:
        return db.query(ChatHistory).filter(ChatHistory.id == chat_id).first()
    finally:
        db.close()
