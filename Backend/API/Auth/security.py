from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import HTTPException, status, Depends
from typing import Annotated
from . import database as db
import os
from dotenv import load_dotenv

# .env dosyasından ortam değişkenlerini yükle
load_dotenv()

# JWT token için güvenlik anahtarları - .env dosyasından alınır
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # Varsayılan değer: HS256
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# SECRET_KEY kontrolü - eğer .env'de yoksa hata ver
if not SECRET_KEY:
    raise ValueError("SECRET_KEY .env dosyasında tanımlı değil! Lütfen .env dosyasına SECRET_KEY ekleyin.")

# OAuth2 şema yapılandırması
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")

# Şifre hashleme için context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(user_password, hashed_password):
    """Kullanıcı şifresini doğrular"""
    return pwd_context.verify(user_password, hashed_password)

def get_password_hash(password):
    """Şifreyi hashler"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """JWT access token oluşturur"""
    to_decode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_decode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_decode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """Token'dan kullanıcı bilgisini alır ve doğrular"""
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
    except Exception as e:
        raise credentials_exception
    
    user = db.get_user(username)
    if user is None:
        raise credentials_exception
    return user
