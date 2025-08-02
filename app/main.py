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
    Reset the database by dropping all tables except the users table,
    then recreating the dropped tables.
    """
    # Get all table names except 'users'
    tables_to_drop = [table.name for table in Base.metadata.sorted_tables if table.name != "users"]
    # Drop all tables except 'users'
    if tables_to_drop:
        Base.metadata.drop_all(bind=engine, tables=[table for table in Base.metadata.sorted_tables if table.name in tables_to_drop])
    # Recreate the dropped tables
    if tables_to_drop:
        Base.metadata.create_all(bind=engine, tables=[table for table in Base.metadata.sorted_tables if table.name in tables_to_drop])
    return {"status": "Database reset successfully (except users table)."}



@app.get("/")
def check_health():
    return {"status": "ok"}

