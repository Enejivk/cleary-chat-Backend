from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, Form
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Document, ChatBot, ChatMessage
from app.utils import precess_pdf, save_pdf, get_current_user
from typing import Annotated
from pydantic import BaseModel
import uuid
import json

router = APIRouter()

# --- Utility Function ---

def handle_pdf_upload(files, user_id, db, background_tasks) -> list:
    """
    Handles PDF validation, storage, DB persistence, and async processing.

    Returns:
        List of dicts containing metadata about uploaded files.
    """
    results = []
    for file in files:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF. Only PDF files are allowed.")
        
        # Store PDF to cloud/local storage
        file_url = save_pdf.concurrent_upload(file.file, file.filename, file.content_type, user_id)
        file_type_simple = file.content_type.split("/")[-1] if "/" in file.content_type else file.content_type

        # Persist document metadata
        doc = Document(
            id=str(uuid.uuid4()),
            user_id=user_id,
            filename=file.filename,
            filepath=file_url,
            file_type=file_type_simple,
        )
        
        # Schedule background task for further processing (e.g., embedding)
        background_tasks.add_task(
            precess_pdf.process_pdf,
            user_id=user_id,
            file_name=file.filename,
            file_id=doc.id,
        )
        
        db.add(doc)
        # Extract only the subtype from the content type (e.g., "pdf" from "application/pdf")
        
        results.append({
            "document_id": doc.id,
            "file_url": file_url,
            "filename": file.filename,
            "type": file_type_simple,
        })

    db.commit()
    return results

def save_chat_message(user_id: str, chatbot_id: str, content: str, sender: str, db: Session):
    """
    Saves a chat message to the database.
    """
    
    message = ChatMessage(
        id=str(uuid.uuid4()),
        user_id=user_id,
        chatbot_id=chatbot_id,
        text=content,
        sender=sender
    )
    
    db.add(message)
    db.commit()
# --- Endpoints ---


@router.post("/upload")
async def upload_pdf(
    user_id: Annotated[str, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """
    Endpoint to upload one or multiple PDF documents for processing.
    """
    results = handle_pdf_upload(files, user_id, db, background_tasks)
    return {
        "files": results,
        "message": "Upload successful",
        "count": len(results)
    }

@router.get("/documents")
async def get_documents(
    user_id: Annotated[str, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Retrieves all documents uploaded by the current user.
    """
    documents = db.query(Document).filter(Document.user_id == user_id).all()
    return [{"id": doc.id, "filename": doc.filename, "filepath": doc.filepath} for doc in documents]


class ChatWithDocument(BaseModel):
    query: str
    document_id: list[str]
    messageHistory: list[dict] = []
    chatbot_id: str

@router.post("/chat")
async def chat_with_document(
    background_tasks: BackgroundTasks,
    user_id: Annotated[str, Depends(get_current_user)],
    chat_data: ChatWithDocument,
    db: Session = Depends(get_db),  # <-- add db here
):
    """
    Query a document collection and get AI-generated response based on user input.
    """
    
    background_tasks.add_task(
        save_chat_message,
        user_id=user_id,
        chatbot_id=chat_data.chatbot_id,
        content=chat_data.query,
        sender="user",
        db=db
    )
    
    context = precess_pdf.query_collection(
        query=chat_data.query,
        filter={
            "$and": [
                {"user_id": {"$eq": str(user_id)}},
                {"id": {"$in": chat_data.document_id}}
            ]
        }
    )
    
    response = precess_pdf.get_ai_response(
        query=chat_data.query,
        context=context,
        message_history=chat_data.messageHistory
    )
    
    background_tasks.add_task(
        save_chat_message,
        user_id=user_id,
        chatbot_id=chat_data.chatbot_id,
        content=response,
        sender="bot",
        db=db  
    )
    return response


@router.get("/list_collections")
def list_collections():
    """
    Returns a list of all ChromaDB collection names.
    Useful for populating dropdowns on the frontend.
    """
    collections = precess_pdf.list_collections()
    return [collection.name for collection in collections]


@router.post("/create_chatbot")
async def create_chatbot(
    user_id: Annotated[str, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    systemPrompt: str = Form(...),
    welcomeMessage: str = Form(...),
    theme: str = Form(...),
    primaryColor: str = Form(...),
    selectedDocuments: list[str] = Form([]),
    newDocument: list[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    Creates a new chatbot configuration with optional document uploads and links.
    """
    # Upload new documents if present
    uploaded_files = []
    if newDocument:
        uploaded_files = handle_pdf_upload(newDocument, user_id, db, background_tasks)
    
    # Combine existing and newly uploaded document IDs
    combined_doc_ids = [doc["document_id"] for doc in uploaded_files] + selectedDocuments

    # Fetch Document instances from the database
    documents = db.query(Document).filter(Document.id.in_(combined_doc_ids)).all() if combined_doc_ids else []

    # Persist chatbot configuration
    chatbot = ChatBot(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=name,
        system_prompt=systemPrompt,
        welcome_message=welcomeMessage,
        theme=theme,
        primary_color=primaryColor,
        documents=documents,
    )

    db.add(chatbot)
    db.commit()
    db.refresh(chatbot)

    return {
            "id": chatbot.id,
            "name": chatbot.name,
            "systemPrompt": chatbot.system_prompt,
            "welcomeMessage": chatbot.welcome_message,
            "theme": chatbot.theme,
            "primaryColor": chatbot.primary_color,
            "documentIds": [doc.id for doc in chatbot.documents],
            "message": "Chatbot updated successfully",
            
            "createdAt": chatbot.created_at.isoformat(),
            "lasttrained": chatbot.last_trained.isoformat() if chatbot.last_trained else None,
            "updatedAt": chatbot.updated_at.isoformat(),
    }
    
    
@router.get("/get_chatbots")
async def get_chatbots(
    user_id: Annotated[str, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Retrieve all chatbot configurations belonging to the current user.
    """
    chatbots = db.query(ChatBot).filter(ChatBot.user_id == user_id).all()
    
    return [
        {
            "id": chatbot.id,
            "name": chatbot.name,
            "systemPrompt": chatbot.system_prompt,
            "welcomeMessage": chatbot.welcome_message,
            "theme": chatbot.theme,
            "primaryColor": chatbot.primary_color,
            "documentIds": [doc.id for doc in chatbot.documents],
            "message": "Chatbot updated successfully",
            "createdAt": chatbot.created_at.isoformat(),
            "lasttrained": chatbot.last_trained.isoformat() if chatbot.last_trained else None,
            "updatedAt": chatbot.updated_at.isoformat(),
        }
        for chatbot in chatbots
    ]


@router.post("/chatbot/{chatbot_id}/add_documents")
async def add_documents_to_chatbot(
    chatbot_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
    new_documents: list[UploadFile] = File(None),
    existing_document_ids: list[str] = Form([]),
    db: Session = Depends(get_db),
):
    """
    Add new or existing documents to a chatbot.
    """
    # Fetch the chatbot and verify ownership
    chatbot = db.query(ChatBot).filter(ChatBot.id == chatbot_id, ChatBot.user_id == user_id).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found or access denied.")

    # Upload new documents if provided
    uploaded_files = []
    if new_documents:
        uploaded_files = handle_pdf_upload(new_documents, user_id, db, background_tasks)

    # Combine document IDs
    combined_doc_ids = [doc["document_id"] for doc in uploaded_files] + existing_document_ids

    # Fetch Document instances
    documents = db.query(Document).filter(Document.id.in_(combined_doc_ids)).all() if combined_doc_ids else []

    # Add documents to chatbot (avoid duplicates)
    for doc in documents:
        if doc not in chatbot.documents:
            chatbot.documents.append(doc)

    db.commit()
    db.refresh(chatbot)

    return {
        "id": chatbot.id,
        "document_ids": [doc.id for doc in chatbot.documents],
        "message": "Documents added successfully"
    }

@router.put("/chatbot/{chatbot_id}/update")
async def update_chatbot(
    chatbot_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    name: str = Form(None),
    systemPrompt: str = Form(None),
    welcomeMessage: str = Form(None),
    theme: str = Form(None),
    primaryColor: str = Form(None),
    selectedDocuments: list[str] = Form([]),
    db: Session = Depends(get_db),
):
    """
    Update chatbot configuration fields and associated documents.
    """
    chatbot = db.query(ChatBot).filter(ChatBot.id == chatbot_id, ChatBot.user_id == user_id).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found or access denied.")

    if name is not None:
        chatbot.name = name
    if systemPrompt is not None:
        chatbot.system_prompt = systemPrompt
    if welcomeMessage is not None:
        chatbot.welcome_message = welcomeMessage
    if theme is not None:
        chatbot.theme = theme
    if primaryColor is not None:
        chatbot.primary_color = primaryColor

    # Update associated documents if provided
    if selectedDocuments is not None:
        documents = db.query(Document).filter(Document.id.in_(selectedDocuments)).all()
        chatbot.documents = documents

    db.commit()
    db.refresh(chatbot)

    return {
        "id": chatbot.id,
        "name": chatbot.name,
        "systemPrompt": chatbot.system_prompt,
        "welcomeMessage": chatbot.welcome_message,
        "theme": chatbot.theme,
        "primaryColor": chatbot.primary_color,
        "documentIds": [doc.id for doc in chatbot.documents],
        "message": "Chatbot updated successfully",
        
        "createdAt": chatbot.created_at.isoformat(),
        "lasttrained": chatbot.last_trained.isoformat() if chatbot.last_trained else None,
        "updatedAt": chatbot.updated_at.isoformat(),
    }


@router.get("/get_all_documents")
async def all_user_documents(
    user_id: Annotated[str, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Retrieve all documents belonging to the current user.
    """
    documents = db.query(Document).filter(Document.user_id == user_id).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "filepath": doc.filepath,
            "Type": doc.file_type,
            "createdAt": doc.created_at.isoformat() if hasattr(doc, "created_at") and doc.created_at else None,
        }
        for doc in documents
    ]

@router.get("/get_all_messages")
async def get_all_messages(
    user_id: Annotated[str, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Retrieve all messages belonging to the current user.
    """
    messages = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).all()
    return [
        {
            "id": message.id,
            "chatbot_id": message.chatbot_id,
            "content": message.text,
            "createdAt": message.created_at.isoformat() if hasattr(message, "created_at") and message.created_at else None,
        }
        for message in messages
    ]
    
@router.get("/chatbot/{chatbot_id}/messages")
async def get_messages_by_chatbot(
    chatbot_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Retrieve all messages for a specific chatbot belonging to the current user.
    """
    messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == user_id,
        ChatMessage.chatbot_id == chatbot_id
    ).all()
    return [
        {
            "id": message.id,
            "sender": message.sender, 
            "content": message.text,
            "timestamp": message.created_at.isoformat() if hasattr(message, "created_at") and message.created_at else None,
        }
        for message in messages
    ]

@router.delete("/chatbot/{chatbot_id}/clear_user_chat")
async def clear_user_chat_for_chatbot(
    chatbot_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Delete all chat messages for a specific chatbot belonging to the current user.
    """
    messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == user_id,
        ChatMessage.chatbot_id == chatbot_id
    ).all()
    for message in messages:
        db.delete(message)
    db.commit()
    return {"message": "All chat messages for this chatbot have been deleted."}