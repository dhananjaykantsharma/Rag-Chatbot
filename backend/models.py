import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_otp_verified = Column(Integer, default=0) 
    generated_otp = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship: Ek user ke pas bahut saari files ho sakti hain
    # back_populates ensures ki dono taraf se data sync rahe
    datasources = relationship("Datasource", back_populates="owner", cascade="all, delete-orphan")

class Datasource(Base):
    __tablename__ = "datasources"

    # UUID ko string me convert karke primary key banana best practice hai
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign Key: User table ki id se link kiya
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Back relationship to User
    owner = relationship("User", back_populates="datasources")