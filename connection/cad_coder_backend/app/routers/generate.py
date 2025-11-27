from fastapi import APIRouter, HTTPException
from app.models.cad_input import CADInput
from app.models.cad_output import CADOutput
from app.services.model_service import generate_cad_code
from app.services.db_service import add_record
# from app.services.gcs_service import upload_cad_code

router = APIRouter(prefix="", tags=["Generation"])
preprocessed_storage = {}

async def fetch_preprocessed_data(user_id: str, prompt: str, fallback_image_path: str | None = None):
    key = f"{user_id}:{prompt}"
    if key in preprocessed_storage:
        return preprocessed_storage[key]
    
    if fallback_image_path:
        return {
            "image_path": fallback_image_path,
            "dataset_path": None,
            "raw_upload_path": None,
        }
    
    raise HTTPException(status_code=404, detail="Preprocessed data not found.")

    # Example: You may want to query your database for the data.
    # Here you should implement the actual logic to fetch based on user_id and prompt.
    # For instance:
    # record = await your_database.query(user_id=user_id, prompt=prompt)
    # return {
    #     "image_path": record.image_path,
    #     "rag_context": record.rag_context
    # }

@router.post("/generate_cad", response_model=CADOutput)
async def generate_cad(input_data: CADInput):
    try:
        print('Request received for CAD generation.')
        preprocessed_data = await fetch_preprocessed_data(
            user_id=input_data.user_id,
            prompt=input_data.prompt,
            fallback_image_path=input_data.image_path
        )
        cad_code = await generate_cad_code(
            prompt=input_data.prompt,
            uid = input_data.user_id,
            image=preprocessed_data["image_path"],
            model_choice=input_data.model_choice.value,
        )

        # Disable GCS upload (important!)
        gcs_uri = None

        input_type = "image" if input_data.image_path else "text"

        add_record(
            user_id=input_data.user_id or "default",
            prompt=input_data.prompt,
            cad_code=cad_code,
            # gcs_uri=gcs_uri,
            image_uri=input_data.image_path,
            input_type=input_type)
        print('done')
        return CADOutput(
            prompt=input_data.prompt,
            cad_code=cad_code,
            model=input_data.model_choice,
            #gcs_uri=gcs_uri,
            #rag_used=bool(input_data.rag_context),
            pipeline_stage="generate",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
