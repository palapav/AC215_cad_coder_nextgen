from fastapi import APIRouter, Query, Body
from app.services.db_service import get_history
from app.services.rag_service import retrieve_similar_context

router = APIRouter(prefix="/history", tags=["History"])

@router.get("/")
async def get_history_records(limit: int = Query(10, ge=1, le=100)):
    """
    Returns the latest generation history.
    """
    records = get_history(limit=limit)
    return {"count": len(records), "records": records}

@router.post("/context")
async def get_rag_context(data: dict = Body(...)):
    """
    Retrieves similar prompts or context from RAG store for a given user prompt.
    """
    prompt = data.get("prompt", "")
    if not prompt:
        return {"context": [], "message": "Empty prompt received."}

    context = retrieve_similar_context(prompt)
    return {"prompt": prompt, "context": context}
