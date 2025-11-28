"""Model service for CAD code generation using Modal-hosted models (Qwen and LLaVA)."""
import asyncio
import logging
import os
from enum import Enum

from dotenv import load_dotenv

load_dotenv()

from app.services import rag_service

from PIL import Image

logger = logging.getLogger(__name__)


class ModelChoice(Enum):
    LLAVA = "llava"
    QWEN = "qwen"


# ---------------------------------------------------------------------------
# Modal Configuration
# ---------------------------------------------------------------------------

# Qwen Modal configuration
QWEN_INFERENCE_BACKEND = os.getenv("QWEN_INFERENCE_BACKEND", "modal").lower()
_qwen_modal_enabled = QWEN_INFERENCE_BACKEND == "modal"
_qwen_modal_init_error = None

# LLaVA Modal configuration
LLAVA_INFERENCE_BACKEND = os.getenv("LLAVA_INFERENCE_BACKEND", "modal").lower()
_llava_modal_enabled = LLAVA_INFERENCE_BACKEND == "modal"
_llava_modal_init_error = None

# Import Modal clients
if _qwen_modal_enabled:
    try:
        logger.info("Loading Modal client for Qwen inference")
        from app.services.modal_client import run_modal_qwen_inference, ModalConfigError
    except Exception as exc:
        _qwen_modal_init_error = exc
        _qwen_modal_enabled = False
        logger.warning("[Model Service] Qwen Modal client disabled: %s", exc)

if _llava_modal_enabled:
    try:
        logger.info("Loading Modal client for LLaVA inference")
        from app.services.modal_client import run_modal_llava_inference, ModalConfigError
    except Exception as exc:
        _llava_modal_init_error = exc
        _llava_modal_enabled = False
        logger.warning("[Model Service] LLaVA Modal client disabled: %s", exc)


# ---------------------------------------------------------------------------
# Qwen Inference via Modal
# ---------------------------------------------------------------------------

async def _run_qwen_via_modal(prompt: str, image=None) -> str:
    """Run Qwen inference via Modal GPU worker."""
    if not _qwen_modal_enabled:
        raise RuntimeError(
            "Modal backend disabled but Qwen model requested. "
            "Set QWEN_INFERENCE_BACKEND=modal and configure Modal tokens."
        )
    if _qwen_modal_init_error:
        raise RuntimeError(f"Qwen Modal client disabled: {_qwen_modal_init_error}")

    max_tokens = int(os.getenv("QWEN_MODAL_MAX_NEW_TOKENS", "2048") or 2048)
    modal_temperature = float(os.getenv("QWEN_MODAL_TEMPERATURE", "0.0") or 0.0)
    
    try:
        return await run_modal_qwen_inference(
            prompt=prompt,
            image=image,
            max_new_tokens=max_tokens,
            temperature=modal_temperature,
        )
    except Exception as exc:
        raise RuntimeError(f"Qwen Modal inference failed: {exc}") from exc


# ---------------------------------------------------------------------------
# LLaVA Inference via Modal
# ---------------------------------------------------------------------------

async def _run_llava_via_modal(prompt: str, image=None) -> str:
    """Run LLaVA inference via Modal GPU worker."""
    if not _llava_modal_enabled:
        raise RuntimeError(
            "Modal backend disabled but LLaVA model requested. "
            "Set LLAVA_INFERENCE_BACKEND=modal and configure Modal tokens."
        )
    if _llava_modal_init_error:
        raise RuntimeError(f"LLaVA Modal client disabled: {_llava_modal_init_error}")
    
    if image is None:
        raise ValueError("LLaVA CAD-Coder requires an image input for inference.")

    max_tokens = int(os.getenv("LLAVA_MODAL_MAX_NEW_TOKENS", "3450") or 3450)
    modal_temperature = float(os.getenv("LLAVA_MODAL_TEMPERATURE", "0.0") or 0.0)
    top_p = float(os.getenv("LLAVA_MODAL_TOP_P", "1.0") or 1.0)
    
    try:
        return await run_modal_llava_inference(
            prompt=prompt,
            image=image,
            max_new_tokens=max_tokens,
            temperature=modal_temperature,
            top_p=top_p,
        )
    except Exception as exc:
        raise RuntimeError(f"LLaVA Modal inference failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Placeholder responses (fallback when Modal is not available)
# ---------------------------------------------------------------------------

def _llava_placeholder() -> str:
    return "# LLaVA generated\nimport cadquery as cq\ncq.Workplane('XY').box(1,1,1)"


def _qwen_placeholder() -> str:
    return "# Qwen generated\nimport cadquery as cq\ncq.Workplane('XY').sphere(1)"


# ---------------------------------------------------------------------------
# Main CAD Code Generation Entrypoint
# ---------------------------------------------------------------------------

async def generate_cad_code(
    prompt: str,
    image=None,
    model_choice: str | ModelChoice = "llava",
    uid: str | None = None,
    image_reference: str | None = None,
):
    """
    Main entrypoint for CAD code generation used by the FastAPI router.
    
    Args:
        prompt: User prompt describing the CAD model to generate.
        image: Optional image input (PIL Image, path, or base64 data URL).
        model_choice: Model to use ('llava' or 'qwen').
        uid: Optional user ID for tracking.
        image_reference: Optional image reference path for RAG.
    
    Returns:
        Dictionary containing:
            - cad_code: Generated CAD code
            - rag_used: Whether RAG context was used
            - rag_context: The RAG context if used
            - rag_results: Raw RAG results if used
    """
    await asyncio.sleep(0)  # Yield to event loop

    # Normalize model choice
    if isinstance(model_choice, ModelChoice):
        model_choice_value = model_choice.value
    else:
        model_choice_value = str(model_choice).lower()
    
    if model_choice_value not in (ModelChoice.LLAVA.value, ModelChoice.QWEN.value):
        model_choice_value = ModelChoice.LLAVA.value

    # ---------------------------------------------------------------------------
    # Qwen Inference Path (with RAG)
    # ---------------------------------------------------------------------------
    if model_choice_value == ModelChoice.QWEN.value:
        # Retrieve RAG context
        rag_payload = {"context": "", "results": [], "used": False}
        try:
            rag_payload = rag_service.retrieve_context(
                prompt=prompt,
                image=image,
                image_reference=image_reference,
            )
        except Exception as exc:
            logger.warning("[Model Service] RAG retrieval failed: %s", exc)

        rag_context = rag_payload.get("context") or ""
        prompt_for_model = prompt
        
        if rag_context:
            prompt_for_model = (
                f"{rag_context}\n\n"
                "Using the above CAD code examples as inspiration, respond to the user's request:\n"
                f"{prompt}"
            )

        try:
            cad_text = await _run_qwen_via_modal(prompt=prompt_for_model, image=image)
        except RuntimeError as exc:
            # RuntimeError indicates backend misconfiguration - propagate it
            logger.error("[Model Service] Qwen inference failed: %s", exc)
            raise
        except Exception as exc:
            # Other exceptions (network, etc.) - return placeholder
            logger.error("[Model Service] Qwen inference failed: %s", exc)
            cad_text = _qwen_placeholder()

        return {
            "cad_code": cad_text,
            "rag_used": rag_payload.get("used", False),
            "rag_context": rag_context or None,
            "rag_results": rag_payload.get("results", []),
        }

    # ---------------------------------------------------------------------------
    # LLaVA Inference Path (no RAG, image optional – falls back to Qwen)
    # ---------------------------------------------------------------------------
    if model_choice_value == ModelChoice.LLAVA.value:
        # Use image_reference if provided (e.g., stored path), otherwise raw image.
        actual_image = image if image is not None else image_reference

        if actual_image is None:
            logger.info(
                "[Model Service] No image supplied for LLaVA request; "
                "using a blank placeholder image to keep inference on LLaVA."
            )
            actual_image = Image.new("RGB", (336, 336), color=(0, 0, 0))

        try:
            cad_text = await _run_llava_via_modal(prompt=prompt, image=actual_image)
        except RuntimeError as exc:
            # RuntimeError indicates backend misconfiguration - propagate it
            logger.error("[Model Service] LLaVA inference failed: %s", exc)
            raise
        except Exception as exc:
            # Other exceptions (network, etc.) - return placeholder
            logger.error("[Model Service] LLaVA inference failed: %s", exc)
            cad_text = _llava_placeholder()

        return {
            "cad_code": cad_text,
            "rag_used": False,
            "rag_context": None,
            "rag_results": [],
        }

    # Fallback (should not reach here)
    return {
        "cad_code": _llava_placeholder(),
        "rag_used": False,
        "rag_context": None,
        "rag_results": [],
    }


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(generate_cad_code("make a cube", model_choice="llava"))
    print(result["cad_code"])
