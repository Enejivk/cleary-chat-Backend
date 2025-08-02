from pydantic import BaseModel
from datetime import datetime


class EmbedBotBase(BaseModel):
    embed_code: str
    is_active: bool = True


class EmbedBotCreate(EmbedBotBase):
    document_id: str


class EmbedBotOut(EmbedBotBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
