from passlib.context import CryptContext
from models import User
import jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from random import randint
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def check_existing_user(email: str, db) -> bool:
    user = db.query(User).filter(User.email == email).first()
    return user is not None

def create_user(data, hashed_password, db):

    otp = generate_otp()
    new_user = User(
        full_name=data.full_name,
        email=data.email,
        hashed_password=hashed_password,
        is_otp_verified=0 ,
        generated_otp=otp
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def create_access_token(data: dict, expires_delta: int = 30):
    to_encode = data.copy()
    expire_in = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire_in})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def generate_otp() -> str:
    """Generate a 6 digit OTP"""
    return str(randint(100000, 999999))

async def send_otp_email(email: str, otp: str):
    """Send the OTP to the user's email address using FastAPI-Mail"""
    message = MessageSchema(
        subject="Your OTP for Rag Chatbot",
        recipients=[email],
        body=f"Your OTP for Rag Chatbot is: {otp}",
        subtype="plain"
    )

    await FastMail(conf).send_message(message=message)

def check_otp_verified(user: User) -> bool:
    """Check if the user's OTP is verified"""
    return user.is_otp_verified == 1

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        if user_id is None or email is None:
            raise credentials_exception
        return {"user_id": user_id, "email": email}
    except:
        raise credentials_exception