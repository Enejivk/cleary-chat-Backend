# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from app.models.models import Document
# from app.db.session import get_db
# from app.utils.auth import get_current_user
# from typing import Annotated

# import tempfile, requests, os
# from langchain_community.document_loaders import PyPDFLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.embeddings import OpenAIEmbeddings
# from langchain_community.vectorstores import Qdrant
# from qdrant_client import QdrantClient
# from dotenv import load_dotenv
# from app.setting import current_config


# load_dotenv()

# QDRANT_API_KEY = current_config.QDRANT_API_KEY
# QDRANT_URL = current_config.QDRANT_URL
# OPENAI_API_KEY = current_config.OPENAI_API_KEY
# COLLECTION_NAME = current_config.COLLECTION_NAME

# qdrant_client = QdrantClient(
#     url=QDRANT_URL,
#     api_key=QDRANT_API_KEY,
# )

# router = APIRouter()

# @router.post("/train")
# def train_user_vector_store(
#     user_id: Annotated[str, Depends(get_current_user)], 
#     db: Session = Depends(get_db)
#     ):
#     documents = db.query(Document).filter(Document.user_id == user_id).all()
#     if not documents:
#         raise HTTPException(status_code=404, detail="No documents found for this user.")
#     pdf_urls = [doc.filepath for doc in documents]

#     all_chunks = []
#     for url in pdf_urls:
#         try:
#             response = requests.get(url)
#             response.raise_for_status()

#             with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
#                 tmp.write(response.content)
#                 tmp_path = tmp.name

#             loader = PyPDFLoader(tmp_path)
#             docs = loader.load()

#             splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
#             chunks = splitter.split_documents(docs)

#             for chunk in chunks:
#                 chunk.metadata["user_id"] = user_id

#             all_chunks.extend(chunks)

#         finally:
#             if os.path.exists(tmp_path):
#                 os.remove(tmp_path)

#     embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

#     Qdrant.from_documents(
#         documents=all_chunks,
#         embedding=embeddings,
#         location=QDRANT_URL,
#         api_key=QDRANT_API_KEY,
#         collection_name=COLLECTION_NAME
#     )

#     return {"message": f"✅ Indexed {len(all_chunks)} chunks for user {user_id}."}
