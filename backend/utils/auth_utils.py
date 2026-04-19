from passlib.context import CryptContext
from models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def check_existing_user(email: str, db) -> bool:
    user = db.query(User.filter(User.email == email)).first()
    return user is not None

def create_user(data, hashed_password, db):
    new_user = User(
        full_name=data.full_name,
        email=data.email,
        hashed_password=hashed_password,
        otp_verified=0  
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
