from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class DocumentBase(BaseModel):
    filename: str


class DocumentCreate(DocumentBase):
    filepath: str
    user_id: UUID


class DocumentOut(DocumentBase):
    id: str
    filepath: str
    uploaded_at: datetime

    class Config:
        from_attributes = True
