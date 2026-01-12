#!/bin/bash
# Start script for Railway deployment

# Activate virtual environment if it exists (Railway handles this, but just in case)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start the FastAPI application using uvicorn
# Railway provides $PORT environment variable automatically
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
