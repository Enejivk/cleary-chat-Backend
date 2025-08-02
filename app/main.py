from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine
from app.routes.user import router as user_router
from app.routes.document import router as document_router



app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(document_router, prefix="/chatbots", tags=["chatbots"])

@app.delete("/reset")
def reset_database():
    """
    Reset the database by dropping and recreating all tables.
    Useful for development/testing purposes.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return {"status": "Database reset successfully."}



@app.get("/")
def check_health():
    return {"status": "ok"}

