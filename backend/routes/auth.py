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
    check_otp_verified,
    get_current_user
)
from pydantic import BaseModel, EmailStr
from fastapi.security import OAuth2PasswordRequestForm

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserSignupResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_otp_verified: bool

    class Config:
        from_attributes = True

class UserSchema(BaseModel):
    user_id: str
    email: EmailStr

    class Config:
        from_attributes = True

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

        return {"message": "User created successfully", "user_data": UserSignupResponse.from_orm(new_user)}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/login")
async def login(data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """This endpoint verify user credentials and return access token if validated"""
    try:
        user = db.query(User).filter(User.email == data.username).first()

        if not user or not check_otp_verified(user):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="OTP verification pending. Please verify your email."
            )

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        
        access_token = create_access_token(data={"user_id": user.id, "email": user.email})

        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.post("/verify-otp")
async def verify_otp(email: EmailStr, otp: str, db: Session = Depends(get_db)):
    """This endpoint verify otp and update user record if otp valid"""
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        if user.generated_otp != otp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")
        
        user.is_otp_verified = 1
        user.generated_otp = None
        db.commit()
        db.refresh(user)
        return {"message": "OTP verified successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

@router.get("/me")
async def me(current_user: UserSchema = Depends(get_current_user), db: Session = Depends(get_db)):
    """This endpoint return current user details based on access token"""
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserSignupResponse.from_orm(user)