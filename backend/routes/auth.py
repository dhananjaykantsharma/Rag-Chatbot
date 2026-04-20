from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from utils.auth_utils import (
    generate_password_hash, 
    verify_password, 
    check_existing_user, 
    create_user,
    create_access_token,
    send_otp_email,
)
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup")
async def signup(data: UserCreate, db: Session = Depends(get_db)):
    """This endpoint check for existing user and if not exist create new user with hashed password"""
    try:

        if check_existing_user(data.email, db):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
        hashed_password = generate_password_hash(data.password)

        new_user = create_user(data, hashed_password, db)

        await send_otp_email(new_user.email, new_user.generated_otp)

        return {"message": "User created successfully", "user_data": new_user}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/login")
async def login(data: UserLogin, db: Session = Depends(get_db)):
    """This endpoint verify user credentials and return access token if validated"""
    try:
        user = db.query(User).filter(User.email == data.email).first()

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        
        access_token = create_access_token(data={"user_id": user.id, "email": user.email})

        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
