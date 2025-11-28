from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.services.pipeline_service import run_stage

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

@router.post("/{stage}")
async def trigger_pipeline(stage: str, background_tasks: BackgroundTasks):
    """
    Trigger a specific pipeline stage (ingestion, preprocess, rag)
    inside its containerized environment.
    
    Example:
      POST /pipeline/ingestion
      POST /pipeline/preprocess
      POST /pipeline/rag
    """
    valid_stages = ["ingestion", "preprocess", "rag"]

    if stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    background_tasks.add_task(run_stage, stage)
    return {"message": f"Pipeline stage '{stage}' started in background."}
