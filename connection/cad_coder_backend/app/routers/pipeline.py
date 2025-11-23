from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.services.pipeline_service import run_stage
from pydantic import BaseModel

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

class PipelineInput(BaseModel):
    data: str
    input_dir: str
    user_id: str  # Adding user_id to the model
    prompt: str   # Adding prompt to the model

@router.post("/{stage}")
async def trigger_pipeline(stage: str, pipeline_input: PipelineInput, background_tasks: BackgroundTasks):
    """
    Trigger a specific pipeline stage (ingestion, preprocess, rag)
    inside its containerized environment.
    
    Example:
      POST /pipeline/ingestion
      POST /pipeline/preprocess
      POST /pipeline/rag
    """
    valid_stages = ['preprocess'] #["ingestion", "preprocess", "rag"]
    output_dir = '/Users/chensiyuan15/documents/src/data'
    if stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    background_tasks.add_task(
        run_stage, 
        stage, 
        pipeline_input.data, 
        pipeline_input.input_dir, 
        output_dir, 
        pipeline_input.user_id,  # Pass user_id to the function
        pipeline_input.prompt     # Pass prompt to the function
    )
    return {"message": f"Pipeline stage '{stage}' started in background."}
