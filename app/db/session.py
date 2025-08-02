from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from app.setting import current_config

# You can load this from a .env file too
DATABASE_URL = current_config.DB_URI

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for injecting DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
