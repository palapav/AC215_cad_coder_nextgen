# /app/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi import Form
import asyncio
from app.services import model_service
from app.routers import generate
from app.routers.pipeline import PipelineInput, trigger_pipeline
from app.services.utils import detect_project_root

router = APIRouter()

PROJECT_ROOT = detect_project_root()
TEMP_DIR = PROJECT_ROOT / "temp"
DATA_DIR = PROJECT_ROOT / "data"


def _cache_preprocess_artifacts(pipeline_input: PipelineInput):
    """
    Store preprocess outputs in the in-memory cache used by generate.py.
    """
    cache_key = f"{pipeline_input.user_id}:{pipeline_input.prompt}"
    processed_image = (DATA_DIR / f"{pipeline_input.user_id}.png").resolve()
    dataset_path = (DATA_DIR / "dataset.jsonl").resolve()
    artifacts = {
        "image_path": str(processed_image) if processed_image.exists() else str(processed_image),
        "dataset_path": str(dataset_path) if dataset_path.exists() else None,
        "raw_upload_path": pipeline_input.data,
    }
    generate.preprocessed_storage[cache_key] = artifacts
    return artifacts


async def _preprocess(pipeline_input: PipelineInput):
    try:
        print("Received preprocess request with user_id:", pipeline_input.user_id)
        print("Prompt for inference:", pipeline_input.prompt)

        # Preprocess step
        preprocessing_result = None
        if asyncio.iscoroutinefunction(trigger_pipeline):
            preprocessing_result = await trigger_pipeline("preprocess", pipeline_input)
        else:
            preprocessing_result = trigger_pipeline("preprocess", pipeline_input)
        
        if preprocessing_result and preprocessing_result.get("status") == "success":
            artifacts = _cache_preprocess_artifacts(pipeline_input)
            return {
                "status": "success",
                "message": "Preprocessing completed.",
                "artifacts": artifacts,
            }
        
        # Check if preprocessing was successful
        if not preprocessing_result or "error" in preprocessing_result:
            print("Preprocessing failed. Exiting.")
            return {"status": "error", "message": "Preprocessing failed. Please check the logs."}
    except Exception as e:
        print("An error occurred:", str(e))
        return {"status": "error", "message": str(e)}
    
async def _inference(pipeline_input: PipelineInput):
    try:
        print("Received infernce request with user_id:", pipeline_input.user_id)
        print("Prompt for inference:", pipeline_input.prompt)
         
        # Inference step
        print("Started inference with prompt:", pipeline_input.prompt)
        # Assuming output_dir is where your processed files are saved
        input_path = '../../../data'
        print("Input path set to:", input_path)

        inference_result = None
        if asyncio.iscoroutinefunction(model_service.generate_cad_code):
            inference_result = await model_service.generate_cad_code(
                prompt=pipeline_input.prompt,
                uid=pipeline_input.user_id,
                image=None,
                model_choice="llava"
            )
        else:
            inference_result = model_service.generate_cad_code(
                prompt=pipeline_input.prompt,
                uid=pipeline_input.user_id,
                image=None,
                model_choice="llava"
            )
        print("Inference completed successfully.")
        return {"status": "success", "result": inference_result}
    except Exception as e:
        print("An error occurred:", str(e))
        return {"status": "error", "message": str(e)}

@router.post("/upload/")
async def upload_image(file: UploadFile = File(...),  user_id: str = Form(...), prompt: str = Form(...)):
    try:
        # Save uploaded file temporarily
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        file_location = TEMP_DIR / file.filename
        with open(file_location, "wb") as f:
            f.write(await file.read())
        print(f"User ID: {user_id}, Prompt: {prompt}")
        print('done')
        pipeline_input = PipelineInput(
            data=str(file_location),
            input_dir=str(file_location.parent),
            user_id= user_id,
            prompt=prompt
        )
        preprocessing_successful = await _preprocess(pipeline_input)
        print(preprocessing_successful)
        response_payload = {
            "message": "Image uploaded. Preprocessing pipeline triggered.",
            "preprocess": preprocessing_successful,
        }
        # If preprocessing is successful, run inference
        if preprocessing_successful and preprocessing_successful.get("status") == "success":
            print('start_inferencing')
            inference_result = await _inference(pipeline_input)
            response_payload["inference"] = inference_result
        else:
            raise HTTPException(status_code=500, detail=preprocessing_successful.get("message", "Preprocessing failed."))
        return JSONResponse(content=response_payload)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
