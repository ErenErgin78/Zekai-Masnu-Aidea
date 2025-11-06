from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import HTTPException, status, Depends
from typing import Annotated
from . import database as db

SECRET_KEY = "n3J9kL8mN7oPqR5sT6uVwXyZ1aBcDeFgHiJkLmNoPqRsTuVwXyZ1aBcDeFgHiJk"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(user_password, hashed_password):
    return pwd_context.verify(user_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_decode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_decode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_decode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"})
    try:
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        username: str = payload.get("sub")
        if username is None:
            
            raise credentials_exception
        
    except InvalidTokenError as e:
        raise credentials_exception
    user = db.get_user(username)
    if user is None:
        print(f"User not found: {username}")  # Debug için
        raise credentials_exception
    print(f"User found: {user}")  # Debug için
    return user

