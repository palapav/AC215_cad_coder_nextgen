from fastapi import APIRouter, HTTPException
from app.models.cad_input import CADInput
from app.models.cad_output import CADOutput
from app.services.model_service import generate_cad_code
from app.services.db_service import add_record
from app.services.gcs_service import upload_cad_code

router = APIRouter(prefix="", tags=["Generation"])

@router.post("/generate_cad", response_model=CADOutput)
async def generate_cad(input_data: CADInput):
    try:
        print('This is running')
        cad_code = await generate_cad_code(
            prompt=input_data.prompt,
            image=None,
            model_choice=input_data.model_choice.value,
        )

        # Disable GCS upload (important!)
        gcs_uri = None

        input_type = "image" if input_data.image_path else "text"

        add_record(
            user_id=input_data.user_id or "default",
            prompt=input_data.prompt,
            cad_code=cad_code,
            gcs_uri=gcs_uri,
            image_uri=input_data.image_path,
            input_type=input_type)

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
