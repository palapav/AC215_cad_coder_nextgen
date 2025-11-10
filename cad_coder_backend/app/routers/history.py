from fastapi import APIRouter, Query
from services.db_service import get_history

router = APIRouter(prefix="/history", tags=["History"])

@router.get("/")
async def get_history_records(limit: int = Query(10, ge=1, le=100)):
    """
    Retrieve previous generation history (latest first).
    """
    records = get_history(limit=limit)
    return {"count": len(records), "records": records}
