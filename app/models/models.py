import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, ForeignKey, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

# --- Association Table for ChatBot <-> Document (Many-to-Many) ---
chatbot_document_association = Table(
    "chatbot_document_association",
    Base.metadata,
    Column("chatbot_id", String, ForeignKey("chat_bots.id"), primary_key=True),
    Column("document_id", String, ForeignKey("documents.id"), primary_key=True),
)

# ----------------------- User Model -----------------------
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    chatbots = relationship("ChatBot", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")


# ----------------------- Document Model -----------------------
class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="documents")
    chatbots = relationship("ChatBot", secondary=chatbot_document_association, back_populates="documents")


# ----------------------- ChatMessage Model -----------------------
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    text = Column(Text, nullable=False)
    sender = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    chatbot_id = Column(String, ForeignKey("chat_bots.id"), nullable=True)

    user = relationship("User", back_populates="chat_messages")
    chatbot = relationship("ChatBot", backref="chat_messages")

# ----------------------- ChatBot Model -----------------------
class ChatBot(Base):
    __tablename__ = "chat_bots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    system_prompt = Column(Text, nullable=False)
    welcome_message = Column(Text, nullable=False)
    theme = Column(String, nullable=False)
    primary_color = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_trained = Column(DateTime, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="chatbots")
    documents = relationship("Document", secondary=chatbot_document_association, back_populates="chatbots")
