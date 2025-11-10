from fastapi import APIRouter, UploadFile, Form
from services.model_service import generate_cad_code
from services.db_service import add_record
from services.gcs_service import upload_cad_code

router = APIRouter(prefix="", tags=["Generation"])

@router.post("/generate_cad")
async def generate_cad(
    prompt: str = Form(...),
    image: UploadFile = None,
    user_id: str = "default"
):
    """
    Endpoint to generate CAD code from text/image prompt.
    """
    cad_code = await generate_cad_code(prompt, image)
    gcs_uri = upload_cad_code(prompt, cad_code)
    add_record(user_id, prompt, cad_code, gcs_uri)

    return {
        "prompt": prompt,
        "cad_code": cad_code,
        "gcs_uri": gcs_uri
    }
