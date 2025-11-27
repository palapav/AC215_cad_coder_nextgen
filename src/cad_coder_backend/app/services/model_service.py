import asyncio
import json
import logging
import os
import subprocess
from enum import Enum
from pathlib import Path
import sys

from dotenv import load_dotenv

load_dotenv()

from app.services import rag_service

logger = logging.getLogger(__name__)


class ModelChoice(Enum):
    LLAVA = "llava"
    QWEN = "qwen"


CURRENT_FILE = Path(__file__).resolve()
APP_DIR = CURRENT_FILE.parents[1]  # /app/app
PROJECT_ROOT = APP_DIR.parent      # /app

def _resolve_model_inference_dir() -> Path:
    candidates = [
        PROJECT_ROOT / "model_inference",
        PROJECT_ROOT / "src" / "model_inference",
        PROJECT_ROOT.parent / "model_inference",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


MODEL_INFERENCE_DIR = _resolve_model_inference_dir()
LLAVA_DIR = MODEL_INFERENCE_DIR
QWEN_DIR = MODEL_INFERENCE_DIR / "qwen"

QWEN_INFERENCE_BACKEND = os.getenv("QWEN_INFERENCE_BACKEND", "modal").lower()
_modal_enabled = QWEN_INFERENCE_BACKEND == "modal"
_modal_init_error = None

if _modal_enabled:
    try:
        logger.info("Loading Modal client for Qwen inference")
        from app.services.modal_client import run_modal_qwen_inference, ModalConfigError
    except Exception as exc:  # pragma: no cover - network errors bubble up
        _modal_init_error = exc
        _modal_enabled = False
        logger.warning("[Model Service] Modal client disabled: %s", exc)
elif QWEN_DIR.exists() and str(QWEN_DIR) not in sys.path:
    sys.path.insert(0, str(QWEN_DIR))


async def _run_qwen_via_modal(prompt: str, image=None) -> str:
    if not _modal_enabled:
        raise RuntimeError(
            "Modal backend disabled but qwen model requested. "
            "Set QWEN_INFERENCE_BACKEND=modal and configure Modal tokens."
        )
    if _modal_init_error:
        raise RuntimeError(f"Modal client disabled: {_modal_init_error}")

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
        raise RuntimeError(f"Modal inference failed: {exc}") from exc


def _llava_placeholder() -> str:
    return "# LLaVA generated\nimport cadquery as cq\ncq.Workplane('XY').box(1,1,1)"


def _qwen_placeholder() -> str:
    return "# Qwen generated\nimport cadquery as cq\ncq.Workplane('XY').sphere(1)"


def _try_run_llava_script(uid: str | None) -> str | None:
    """Attempt to run the legacy LLaVA inference script if present."""
    llava_path = LLAVA_DIR
    if not llava_path.exists():
        return None

    script_path = llava_path / "scripts" / "v1_5" / "eval" / "test_gencadcode.sh"
    if not script_path.exists() or not uid:
        return None

    try:
        command = [str(script_path), "CADCODER/CAD-Coder", "dataset"]
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(llava_path),
            timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Inference error: {result.stderr.strip()}")

        output_file = (
            llava_path
            / "inference"
            / "inference_results"
            / "CAD-Coder"
            / "dataset"
            / "merge.jsonl"
        )
        if not output_file.exists():
            output_file = (
                llava_path
                / "model_inference"
                / "inference"
                / "inference_results"
                / "CAD-Coder"
                / "dataset"
                / "merge.jsonl"
            )
        if not output_file.exists():
            return None

        with open(output_file, "r") as file:
            for line in file:
                try:
                    record = json.loads(line.strip())
                    if "text" in record and record.get("question_id") == uid:
                        return record["text"]
                except json.JSONDecodeError:
                    continue

        with open(output_file, "r") as file:
            first_line = file.readline()
            if first_line:
                record = json.loads(first_line.strip())
                if "text" in record:
                    return record["text"]
    except subprocess.TimeoutExpired:
        raise RuntimeError("LLaVA inference timed out after 5 minutes")
    except Exception as exc:
        print(f"[Model Service] LLaVA script error: {exc}")
    return None


async def generate_cad_code(
    prompt: str,
    image=None,
    model_choice: str | ModelChoice = "llava",
    uid: str | None = None,
    image_reference: str | None = None,
):
    """Main entrypoint used by the FastAPI router."""
    await asyncio.sleep(0)

    if isinstance(model_choice, ModelChoice):
        model_choice_value = model_choice.value
    else:
        model_choice_value = str(model_choice).lower()
    if model_choice_value not in (ModelChoice.LLAVA.value, ModelChoice.QWEN.value):
        model_choice_value = ModelChoice.LLAVA.value

    if model_choice_value == ModelChoice.QWEN.value:
        rag_payload = {"context": "", "results": [], "used": False}
        try:
            rag_payload = rag_service.retrieve_context(
                prompt=prompt,
                image=image,
                image_reference=image_reference,
            )
        except Exception as exc:  # pragma: no cover - guard rail
            logger.warning("[Model Service] RAG retrieval failed: %s", exc)

        rag_context = rag_payload.get("context") or ""
        prompt_for_model = prompt
        if rag_context:
            prompt_for_model = (
                f"{rag_context}\n\n"
                "Using the above CAD code examples as inspiration, respond to the user's request:\n"
                f"{prompt}"
            )

        cad_text = await _run_qwen_via_modal(prompt=prompt_for_model, image=image)
        return {
            "cad_code": cad_text,
            "rag_used": rag_payload.get("used", False),
            "rag_context": rag_context or None,
            "rag_results": rag_payload.get("results", []),
        }

    # LLaVA path (legacy baseline)
    llava_result = _try_run_llava_script(uid)
    if llava_result:
        return {
            "cad_code": llava_result,
            "rag_used": False,
            "rag_context": None,
            "rag_results": [],
        }
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