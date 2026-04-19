# backend/models.py
from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_otp_verified = Column(Integer, default=0)  # 0 for False, 1 for True
    created_at = Column(DateTime, default=datetime.utcnow)