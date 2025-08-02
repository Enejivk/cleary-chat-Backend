import os
from dotenv import load_dotenv

load_dotenv()
ENV = os.getenv("ENV", "development")

class Config:
    DEBUG = False
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "my-bucket")
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    REFRESH_TOKEN_EXPIRE_MINUTES = int(eval(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "60*24*7")))
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_URL = os.getenv("QDRANT_URL")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "user_documents")
    OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL")

class DevelopmentConfig(Config):
    DEBUG = True
    DB_URI = os.getenv("SQLITE_DB_URI")
    
class ProductionConfig(Config):
    DB_URI = os.getenv("POSTGRES_DB_URI")

if ENV == "production":
    current_config = ProductionConfig()
else:
    current_config = DevelopmentConfig()
