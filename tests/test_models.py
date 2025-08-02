from app.models.models import User, Document, ChatMessage, EmbedBot
from sqlalchemy.orm import Session

import uuid
def test_create_user(db_session: Session):
    user = User(email="test@example.com", hashed_password="hashed123")
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.email == "test@example.com"

def test_create_document_and_chat(db_session: Session):
    user = User(email="docuser@example.com", hashed_password="123")
    db_session.add(user)
    db_session.commit()

    doc = Document(
        user_id=user.id,
        filename="example.pdf",
        filepath="/uploads/example.pdf"
    )
    db_session.add(doc)
    db_session.commit()

    chat = ChatMessage(
        document_id=doc.id,
        question="What is this about?",
        answer="This is a test PDF."
    )
    db_session.add(chat)
    db_session.commit()

    assert chat.id is not None
    assert chat.document_id == doc.id
    assert doc.chats[0].question == "What is this about?"

def test_embed_bot(db_session: Session):
    user = User(email="embed@example.com", hashed_password="123")
    db_session.add(user)
    db_session.commit()

    doc = Document(
        user_id=user.id,
        filename="embed.pdf",
        filepath="/uploads/embed.pdf"
    )
    db_session.add(doc)
    db_session.commit()

    bot = EmbedBot(
        document_id=doc.id,
        embed_code="<iframe>bot123</iframe>"
    )
    db_session.add(bot)
    db_session.commit()

    assert bot.document_id == doc.id
    assert doc.embed_bots[0].embed_code.startswith("<iframe>")

def test_update_user_profile(db_session: Session):
    # First create a user
    user = User(email="updatetest@example.com", hashed_password="hashed123")
    db_session.add(user)
    db_session.commit()
    
    # Update the user's profile
    user.name = "Test User"
    user.bio = "This is my bio"
    db_session.commit()
    
    # Fetch the user again to verify changes
    updated_user = db_session.query(User).filter(User.id == user.id).first()
    assert updated_user.name == "Test User"
    assert updated_user.bio == "This is my bio"
    assert updated_user.email == "updatetest@example.com"

def test_delete_user_cascade(db_session: Session):
    # Create a user with associated documents
    user = User(email="deletetest@example.com", hashed_password="hashed123")
    db_session.add(user)
    db_session.commit()
    
    # Add a document for this user
    doc = Document(
        user_id=user.id,
        filename="test.pdf",
        filepath="/uploads/test.pdf"
    )
    db_session.add(doc)
    db_session.commit()
    
    # Delete the user
    db_session.delete(user)
    db_session.commit()
    
    # Verify user and their documents are deleted
    deleted_user = db_session.query(User).filter(User.id == user.id).first()
    deleted_doc = db_session.query(Document).filter(Document.id == doc.id).first()
    assert deleted_user is None
    assert deleted_doc is None
