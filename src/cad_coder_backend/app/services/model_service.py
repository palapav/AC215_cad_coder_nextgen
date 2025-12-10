"""Model service for CAD code generation using Modal or GKE-hosted models (Qwen and LLaVA)."""
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
# Backend Configuration
# ---------------------------------------------------------------------------

# Supported backends: "modal", "gke", "mock"
QWEN_INFERENCE_BACKEND = os.getenv("QWEN_INFERENCE_BACKEND", "modal").lower()
LLAVA_INFERENCE_BACKEND = os.getenv("LLAVA_INFERENCE_BACKEND", "modal").lower()

# Initialize backend clients based on configuration
_qwen_backend_enabled = False
_qwen_backend_init_error = None
_llava_backend_enabled = False
_llava_backend_init_error = None

# ---------------------------------------------------------------------------
# Modal Backend Initialization
# ---------------------------------------------------------------------------

if QWEN_INFERENCE_BACKEND == "modal":
    try:
        logger.info("Loading Modal client for Qwen inference")
        from app.services.modal_client import run_modal_qwen_inference, ModalConfigError
        _qwen_backend_enabled = True
    except Exception as exc:
        _qwen_backend_init_error = exc
        logger.warning("[Model Service] Qwen Modal client disabled: %s", exc)

if LLAVA_INFERENCE_BACKEND == "modal":
    try:
        logger.info("Loading Modal client for LLaVA inference")
        from app.services.modal_client import run_modal_llava_inference, ModalConfigError
        _llava_backend_enabled = True
    except Exception as exc:
        _llava_backend_init_error = exc
        logger.warning("[Model Service] LLaVA Modal client disabled: %s", exc)

# ---------------------------------------------------------------------------
# GKE Backend Initialization
# ---------------------------------------------------------------------------

if QWEN_INFERENCE_BACKEND == "gke":
    try:
        logger.info("Loading GKE client for Qwen inference")
        from app.services.gke_client import run_gke_qwen_inference, GKEClientError
        _qwen_backend_enabled = True
    except Exception as exc:
        _qwen_backend_init_error = exc
        logger.warning("[Model Service] Qwen GKE client disabled: %s", exc)

if LLAVA_INFERENCE_BACKEND == "gke":
    try:
        logger.info("Loading GKE client for LLaVA inference")
        from app.services.gke_client import run_gke_llava_inference, GKEClientError
        _llava_backend_enabled = True
    except Exception as exc:
        _llava_backend_init_error = exc
        logger.warning("[Model Service] LLaVA GKE client disabled: %s", exc)

# ---------------------------------------------------------------------------
# Mock Backend (for testing)
# ---------------------------------------------------------------------------

if QWEN_INFERENCE_BACKEND == "mock":
    _qwen_backend_enabled = True
    logger.info("Using mock backend for Qwen inference")

if LLAVA_INFERENCE_BACKEND == "mock":
    _llava_backend_enabled = True
    logger.info("Using mock backend for LLaVA inference")


# ---------------------------------------------------------------------------
# Service Initialization (for backward compatibility)
# ---------------------------------------------------------------------------

def _get_qwen_service():
    """Get Qwen service status (for startup pre-initialization)."""
    return {
        "backend": QWEN_INFERENCE_BACKEND,
        "enabled": _qwen_backend_enabled,
        "error": str(_qwen_backend_init_error) if _qwen_backend_init_error else None,
    }


# ---------------------------------------------------------------------------
# Qwen Inference
# ---------------------------------------------------------------------------

async def _run_qwen_inference(prompt: str, image=None) -> str:
    """Run Qwen inference via configured backend."""
    if not _qwen_backend_enabled:
        raise RuntimeError(
            f"Qwen backend ({QWEN_INFERENCE_BACKEND}) is not enabled. "
            "Check configuration and credentials."
        )
    if _qwen_backend_init_error:
        raise RuntimeError(f"Qwen backend initialization failed: {_qwen_backend_init_error}")

    max_tokens = int(os.getenv("QWEN_MODAL_MAX_NEW_TOKENS", "4096") or 4096)
    temperature = float(os.getenv("QWEN_MODAL_TEMPERATURE", "0.0") or 0.0)

    # Route to appropriate backend
    if QWEN_INFERENCE_BACKEND == "modal":
        from app.services.modal_client import run_modal_qwen_inference
        return await run_modal_qwen_inference(
            prompt=prompt,
            image=image,
            max_new_tokens=max_tokens,
            temperature=temperature,
        )
    
    elif QWEN_INFERENCE_BACKEND == "gke":
        from app.services.gke_client import run_gke_qwen_inference
        return await run_gke_qwen_inference(
            prompt=prompt,
            image=image,
            max_new_tokens=max_tokens,
            temperature=temperature,
        )
    
    elif QWEN_INFERENCE_BACKEND == "mock":
        await asyncio.sleep(0.1)  # Simulate latency
        return _qwen_placeholder()
    
    else:
        raise RuntimeError(f"Unknown Qwen backend: {QWEN_INFERENCE_BACKEND}")


async def _run_qwen_inference_stream(prompt: str, image=None):
    """Stream Qwen tokens."""
    if not _qwen_backend_enabled:
        raise RuntimeError(f"Qwen backend ({QWEN_INFERENCE_BACKEND}) is not enabled.")
    if _qwen_backend_init_error:
        raise RuntimeError(f"Qwen backend initialization failed: {_qwen_backend_init_error}")

    max_tokens = int(os.getenv("QWEN_MODAL_MAX_NEW_TOKENS", "4096") or 4096)
    temperature = float(os.getenv("QWEN_MODAL_TEMPERATURE", "0.0") or 0.0)

    if QWEN_INFERENCE_BACKEND == "modal":
        from app.services.modal_client import stream_modal_qwen_inference
        async for chunk in stream_modal_qwen_inference(
            prompt=prompt,
            image=image,
            max_new_tokens=max_tokens,
            temperature=temperature,
        ):
            yield chunk
    elif QWEN_INFERENCE_BACKEND == "gke":
        from app.services.gke_client import stream_gke_qwen_inference
        async for chunk in stream_gke_qwen_inference(
            prompt=prompt,
            image=image,
            max_new_tokens=max_tokens,
            temperature=temperature,
        ):
            yield chunk
    else:
        raise RuntimeError(f"Streaming not supported for backend: {QWEN_INFERENCE_BACKEND}")


# ---------------------------------------------------------------------------
# LLaVA Inference
# ---------------------------------------------------------------------------

async def _run_llava_inference(prompt: str, image=None) -> str:
    """Run LLaVA inference via configured backend."""
    if not _llava_backend_enabled:
        raise RuntimeError(
            f"LLaVA backend ({LLAVA_INFERENCE_BACKEND}) is not enabled. "
            "Check configuration and credentials."
        )
    if _llava_backend_init_error:
        raise RuntimeError(f"LLaVA backend initialization failed: {_llava_backend_init_error}")

    max_tokens = int(os.getenv("LLAVA_MODAL_MAX_NEW_TOKENS", "4096") or 4096)
    temperature = float(os.getenv("LLAVA_MODAL_TEMPERATURE", "0.0") or 0.0)
    top_p = float(os.getenv("LLAVA_MODAL_TOP_P", "1.0") or 1.0)

    # Route to appropriate backend
    if LLAVA_INFERENCE_BACKEND == "modal":
        from app.services.modal_client import run_modal_llava_inference
        return await run_modal_llava_inference(
            prompt=prompt,
            image=image,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
    
    elif LLAVA_INFERENCE_BACKEND == "gke":
        from app.services.gke_client import run_gke_llava_inference
        return await run_gke_llava_inference(
            prompt=prompt,
            image=image,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
    
    elif LLAVA_INFERENCE_BACKEND == "mock":
        await asyncio.sleep(0.1)  # Simulate latency
        return _llava_placeholder()
    
    else:
        raise RuntimeError(f"Unknown LLaVA backend: {LLAVA_INFERENCE_BACKEND}")


async def _run_llava_inference_stream(prompt: str, image=None):
    """Stream LLaVA tokens."""
    if not _llava_backend_enabled:
        raise RuntimeError(f"LLaVA backend ({LLAVA_INFERENCE_BACKEND}) is not enabled.")
    if _llava_backend_init_error:
        raise RuntimeError(f"LLaVA backend initialization failed: {_llava_backend_init_error}")

    max_tokens = int(os.getenv("LLAVA_MODAL_MAX_NEW_TOKENS", "4096") or 4096)
    temperature = float(os.getenv("LLAVA_MODAL_TEMPERATURE", "0.0") or 0.0)
    top_p = float(os.getenv("LLAVA_MODAL_TOP_P", "1.0") or 1.0)

    if LLAVA_INFERENCE_BACKEND == "modal":
        from app.services.modal_client import stream_modal_llava_inference
        async for chunk in stream_modal_llava_inference(
            prompt=prompt,
            image=image,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        ):
            yield chunk
    elif LLAVA_INFERENCE_BACKEND == "gke":
        from app.services.gke_client import stream_gke_llava_inference
        async for chunk in stream_gke_llava_inference(
            prompt=prompt,
            image=image,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        ):
            yield chunk
    else:
        raise RuntimeError(f"Streaming not supported for backend: {LLAVA_INFERENCE_BACKEND}")


# ---------------------------------------------------------------------------
# Placeholder responses (fallback when backend is not available)
# ---------------------------------------------------------------------------

def _llava_placeholder() -> str:
    return "# LLaVA generated\nimport cadquery as cq\ncq.Workplane('XY').box(1,1,1)"


async def generate_cad_code_stream(
    prompt: str,
    image=None,
    model_choice: ModelChoice = ModelChoice.QWEN,
    image_reference: str = None,
):
    """
    Stream CAD code tokens from the selected model.
    
    For Qwen: RAG context is retrieved and prepended to the prompt before inference.
    For LLaVA: No RAG (image-to-code model).
    """
    if model_choice == ModelChoice.QWEN:
        # Retrieve RAG context for Qwen (gracefully handles errors)
        prompt_for_model = prompt
        try:
            rag_payload = rag_service.retrieve_context(
                prompt=prompt,
                image=image,
                image_reference=image_reference,
            )
            rag_context = rag_payload.get("context") or ""
            if rag_context:
                prompt_for_model = (
                    f"{rag_context}\n\n"
                    "Using the above CAD code examples as inspiration, respond to the user's request:\n"
                    f"{prompt}"
                )
                logger.info("[Model Service] RAG context added to Qwen streaming request")
        except Exception as exc:
            logger.warning("[Model Service] RAG retrieval failed (continuing without): %s", exc)
        
        async for chunk in _run_qwen_inference_stream(prompt_for_model, image=image):
            yield chunk
    elif model_choice == ModelChoice.LLAVA:
        async for chunk in _run_llava_inference_stream(prompt, image=image):
            yield chunk
    else:
        raise RuntimeError(f"Streaming not supported for model: {model_choice}")


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
            cad_text = await _run_qwen_inference(prompt=prompt_for_model, image=image)
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
            cad_text = await _run_llava_inference(prompt=prompt, image=actual_image)
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
