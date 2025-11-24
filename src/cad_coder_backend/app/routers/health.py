from fastapi import APIRouter
from app.services.db_service import client, db

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/")
async def health_check():
    """Health check endpoint that verifies MongoDB connection."""
    try:
        # Test MongoDB connection
        client.server_info()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "mongodb": db_status
    }
