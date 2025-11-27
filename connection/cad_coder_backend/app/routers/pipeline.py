from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.services.pipeline_service import run_stage
from pydantic import BaseModel
import os

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

class PipelineInput(BaseModel):
    data: str
    input_dir: str
    user_id: str  # Adding user_id to the model
    prompt: str   # Adding prompt to the model

@router.post("/{stage}")
async def trigger_pipeline(stage: str, pipeline_input: PipelineInput, use_docker: bool = False):
    """
    Trigger a specific pipeline stage (ingestion, preprocess, rag)
    inside its containerized environment.
    
    Example:
      POST /pipeline/ingestion
      POST /pipeline/preprocess
      POST /pipeline/rag
    """
    valid_stages = ['preprocess'] #["ingestion", "preprocess", "rag"]
    if stage in valid_stages:
        # Perform the intended preprocessing operation
        # Return a success result or an appropriate error
    # Output directory inside the container (mapped to ../data from cad_coder_backend)
        if use_docker:
            output_dir = '/app/data'
        else: output_dir = '../data'
        if stage not in valid_stages: 
            raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    # Use data field as the image file path, input_dir as the directory containing it
    # If input_dir is not provided or is the same as data, derive it from data
        image_path = pipeline_input.data
        input_directory = pipeline_input.input_dir if pipeline_input.input_dir else os.path.dirname(image_path) or "."

        # background_tasks.add_task(run_stage, stage,  image_path,  # Pass the image file path as data
        # input_directory,  # Pass the input directory
        # output_dir, 
        # pipeline_input.user_id,  # Pass user_id to the function
        # pipeline_input.prompt     # Pass prompt to the function
        # )
        await run_stage(stage, image_path, input_directory, output_dir, pipeline_input.user_id, pipeline_input.prompt)
    print('result is successful')
    return {"status": "success"}
