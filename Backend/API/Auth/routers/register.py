from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from ..schemas import UserCreate, UserPublic, UserInDB
from ..security import get_password_hash
from .. import database as Db

router = APIRouter(prefix="/register", tags=["Auth"])



@router.post("")
async def create_user(user_data: UserCreate) -> UserPublic:
    db_user = Db.get_user(user_data.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten kayıtlı.")
    hashed_password = get_password_hash(user_data.password)
    user_in_db = UserInDB(**user_data.model_dump(), hashed_password=hashed_password)
    Db.add_user(**user_in_db.model_dump())
    user_dict = Db.get_user(user_data.username)
    return UserPublic(**user_dict) if user_dict else None
