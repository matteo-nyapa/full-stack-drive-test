from datetime import datetime
from pydantic import BaseModel


class FileOut(BaseModel):
    id: str
    name: str
    size: int
    mime_type: str
    upload_date: datetime
    path: str

    class Config:
        orm_mode = True


class FileRename(BaseModel):
    name: str
