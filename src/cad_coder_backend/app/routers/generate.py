from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.cad_input import CADInput
from app.models.cad_output import CADOutput
from app.services.model_service import generate_cad_code, generate_cad_code_stream, ModelChoice
from app.services.db_service import add_record
from app.services.gcs_service import upload_cad_code

router = APIRouter(prefix="", tags=["Generation"])

@router.post("/generate_cad", response_model=CADOutput)
async def generate_cad(input_data: CADInput):
    try:
        # Debug: Log the raw input to see what we're receiving
        import json
        print(f'[Generate] Raw input_data: {json.dumps(input_data.dict(), indent=2)}')
        print(f'[Generate] Model choice type: {type(input_data.model_choice)}')
        print(f'[Generate] Model choice value: {input_data.model_choice.value if hasattr(input_data.model_choice, "value") else input_data.model_choice}')
        model_choice_value = input_data.model_choice.value if hasattr(input_data.model_choice, "value") else str(input_data.model_choice)
        print(f'[Generate] Processing request with model: {model_choice_value}')
        
        # Handle image path if provided
        image_input = None
        if input_data.image_path:
            # Check if it's a base64 data URL
            if input_data.image_path.startswith("data:image"):
                try:
                    import base64
                    from io import BytesIO
                    from PIL import Image
                    # Extract base64 data from data URL
                    header, encoded = input_data.image_path.split(",", 1)
                    image_data = base64.b64decode(encoded)
                    image_input = Image.open(BytesIO(image_data)).convert("RGB")
                    print(f'[Generate] Loaded image from base64 data URL')
                except Exception as e:
                    print(f'[Generate] Error decoding base64 image: {e}')
                    raise ValueError(f"Invalid base64 image data: {e}")
            else:
                # Try to load from file path
                from pathlib import Path
                image_path = Path(input_data.image_path)
                if image_path.exists():
                    from PIL import Image
                    image_input = Image.open(image_path).convert("RGB")
                    print(f'[Generate] Loaded image from: {input_data.image_path}')
                else:
                    print(f'[Generate] Warning: Image path does not exist: {input_data.image_path}')
        
        # Validate and set default prompt if empty
        prompt = input_data.prompt.strip() if input_data.prompt else ""
        if not prompt:
            if image_input:
                prompt = "Generate the CADQuery code needed to create the CAD for the provided image."
                print(f'[Generate] Empty prompt provided with image, using default CAD generation prompt')
            else:
                prompt = "Generate CAD code for a simple geometric shape."
                print(f'[Generate] Empty prompt provided, using default prompt')
        
        print(f'[Generate] Calling generate_cad_code with prompt: {prompt[:50]}...')
        model_response = await generate_cad_code(
            prompt=prompt,
            image=image_input,
            model_choice=model_choice_value,
            image_reference=input_data.image_path,
        )
        cad_code = model_response.get("cad_code")
        
        # Validate that we got CAD code
        if not cad_code or not cad_code.strip():
            raise ValueError("Generated CAD code is empty or None")

        print(f'[Generate] Generated CAD code length: {len(cad_code)} characters')

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
            rag_used=model_response.get("rag_used", False),
            rag_context=model_response.get("rag_context"),
            pipeline_stage="generate",
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f'[Generate] Error: {str(e)}')
        print(f'[Generate] Traceback:\n{error_trace}')
        raise HTTPException(status_code=500, detail=f"CAD generation failed: {str(e)}")


@router.post("/generate_cad_stream")
async def generate_cad_stream(input_data: CADInput):
    """
    Stream tokens back to the client while generating CAD code.
    """
    try:
        import json
        import base64
        from io import BytesIO
        from pathlib import Path
        from PIL import Image
        model_choice_value = input_data.model_choice.value if hasattr(input_data.model_choice, "value") else str(input_data.model_choice)
        try:
            model_choice_enum = ModelChoice(model_choice_value)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid model choice: {model_choice_value}")

        image_input = None
        if input_data.image_path:
            if input_data.image_path.startswith("data:image"):
                header, encoded = input_data.image_path.split(",", 1)
                image_data = base64.b64decode(encoded)
                image_input = Image.open(BytesIO(image_data)).convert("RGB")
            else:
                image_path = Path(input_data.image_path)
                if image_path.exists():
                    image_input = Image.open(image_path).convert("RGB")

        prompt = input_data.prompt.strip() if input_data.prompt else ""
        if not prompt:
            prompt = "Generate the CADQuery code needed to create the CAD for the provided image." if image_input else "Generate CAD code for a simple geometric shape."

        async def token_generator():
            buffer = []
            async for chunk in generate_cad_code_stream(
                prompt=prompt,
                image=image_input,
                model_choice=model_choice_enum,
            ):
                buffer.append(chunk)
                yield chunk
            cad_code = "".join(buffer)
            add_record(
                user_id=input_data.user_id or "default",
                prompt=input_data.prompt,
                cad_code=cad_code,
                gcs_uri=None,
                image_uri=input_data.image_path,
                input_type="image" if input_data.image_path else "text")

        return StreamingResponse(token_generator(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming generation failed: {str(e)}")
