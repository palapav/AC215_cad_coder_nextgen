import asyncio
from enum import Enum
import subprocess
class ModelChoice(Enum):
    LLAVA = "llava"
    QWEN = "qwen"

models = {
    "llava": "/home/chensiyuan06/CAD-Coder/src2/connection/model_inference",
    "qwen": "path/to/qwen"
}

async def generate_cad_code(prompt: str, uid:str, image=None, model_choice: str = "llava"):
    """
    Simulated model inference.
    Replace with actual HuggingFace or local model API calls later.
    """
    await asyncio.sleep(1)
    if model_choice not in models:
        model_choice = "llava"
    print('done')
    script_path = f"{models[model_choice]}/scripts/v1_5/eval/test_gencadcode.sh"
    command = [script_path, "CADCODER/CAD-Coder", "dataset"]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check = True)
    print('done')
    if result.returncode != 0:
        raise RuntimeError(f"Error: {result.stderr.strip()}")
    with open(file_path, 'r') as file:
        for line in file:
                # Each line in a JSONL file is a separate JSON object
            record = json.loads(line)
            if 'text' in record and record['question_id'] == uid:
                return record['text']  # Return the first encountered 'text' value
            else:
                raise ValueError("No 'text' key found in the JSONL file.")

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(generate_cad_code("make a cube", model_choice="llava"))
    print(result)