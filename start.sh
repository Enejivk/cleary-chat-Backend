
#!/bin/bash

source .venv/bin/activate
# Start FastAPI app with Uvicorn, log output, and run in background
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4