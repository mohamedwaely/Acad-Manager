from datetime import timedelta, datetime
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SEC_KEY')
ALGORITHM = "HS256"
USER_ACCESS_TOKEN_EXPIRE_MINUTES = 360  # Expiration time for regular users
ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES = 720  # Expiration time for admins (12 hours)
SUPERVISOR_ACCESS_TOKEN_EXPIRE_MINUTES = 720  # Expiration time for supervisors (12 hours)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def getHashedPassword(password: str):
    return pwd_context.hash(password)

def create_access_token(data: dict, is_admin: bool = False, is_supervisor: bool = False, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        if is_admin:
            expire_minutes = ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES
        elif is_supervisor:
            expire_minutes = SUPERVISOR_ACCESS_TOKEN_EXPIRE_MINUTES
        else:
            expire_minutes = USER_ACCESS_TOKEN_EXPIRE_MINUTES
        expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    to_encode.update({
        "exp": expire,
        "is_admin": is_admin,
        "is_supervisor": is_supervisor
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

