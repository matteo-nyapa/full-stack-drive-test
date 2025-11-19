from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FileOut(BaseModel):
    id: str
    name: str
    size: int
    mime_type: str
    upload_date: datetime
    path: str
    folder: Optional[str] = None  # folder is optional
    owner: str

    class Config:
        orm_mode = True


class FileRename(BaseModel):
    name: str


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class UserLogin(UserBase):
    password: str


class UserInDB(UserBase):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
# ---------- AUTH MODELS ----------

class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class UserLogin(UserBase):
    password: str


class UserInDB(UserBase):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- FOLDER MODELS ----------

class FolderBase(BaseModel):
    name: str
    parent_id: Optional[str] = None  # null = raíz


class FolderCreate(FolderBase):
    pass


class FolderOut(FolderBase):
    id: str
    owner: str
    created_at: datetime