import asyncio
from enum import Enum

class ModelChoice(Enum):
    LLAVA = "llava"
    QWEN = "qwen"

models = {
    "llava": "path/to/llava",
    "qwen": "path/to/qwen"
}

async def generate_cad_code(prompt: str, image=None, model_choice: str = "llava"):
    """
    Simulated model inference.
    Replace with actual HuggingFace or local model API calls later.
    """
    await asyncio.sleep(1)
    if model_choice not in models:
        model_choice = "llava"

    if model_choice == "llava":
        return f"# LLaVA generated\nimport cadquery as cq\ncq.Workplane('XY').box(1,1,1)  # {prompt}"
    else:
        return f"# Qwen generated\nimport cadquery as cq\ncq.Workplane('XY').sphere(1)  # {prompt}"
