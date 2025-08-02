from pydantic import BaseModel
from datetime import datetime


class ChatBase(BaseModel):
    question: str
    answer: str


class ChatCreate(ChatBase):
    document_id: str


class ChatOut(ChatBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
