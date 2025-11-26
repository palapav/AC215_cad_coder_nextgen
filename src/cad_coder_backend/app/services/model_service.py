import asyncio
import os
import json
import subprocess
from enum import Enum
from pathlib import Path
import sys
from dotenv import load_dotenv; load_dotenv()


class ModelChoice(Enum):
    LLAVA = "llava"
    QWEN = "qwen"


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_INFERENCE_DIR = PROJECT_ROOT / "src" / "model_inference"
LLAVA_DIR = MODEL_INFERENCE_DIR
QWEN_DIR = MODEL_INFERENCE_DIR / "qwen"

QWEN_INFERENCE_BACKEND = os.getenv("QWEN_INFERENCE_BACKEND", "modal").lower()
_modal_enabled = QWEN_INFERENCE_BACKEND == "modal"
_modal_init_error = None

if _modal_enabled:
    try:
        print("Loading modal client")
        from app.services.modal_client import run_modal_qwen_inference, ModalConfigError
    except Exception as exc:  # pragma: no cover - network errors bubble up
        _modal_init_error = exc
        _modal_enabled = False
        print(f"[Model Service] ⚠️ Modal client disabled: {exc}")
else:
    # Ensure local Qwen code is importable when Modal is disabled
    if QWEN_DIR.exists() and str(QWEN_DIR) not in sys.path:
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
        return await _run_qwen_via_modal(prompt=prompt, image=image)

    # LLaVA path (legacy baseline)
    llava_result = _try_run_llava_script(uid)
    if llava_result:
        return llava_result
    return _llava_placeholder()


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(generate_cad_code("make a cube", model_choice="llava"))
    print(result)