from pydantic import BaseModel,ConfigDict,BeforeValidator,Field
from typing import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class UserBase(BaseModel):
    full_name: str
    username: str

class UserCreate(UserBase):
    password: str
   

class UserInDB(UserBase):
    hashed_password: str
    

class UserPublic(UserBase):

    id: PyObjectId = Field(alias="_id")
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

class UserToken(BaseModel):
    username: str | None = None 