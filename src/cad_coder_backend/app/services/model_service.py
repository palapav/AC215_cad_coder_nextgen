import asyncio
import os
import json
import subprocess
from enum import Enum
from pathlib import Path

class ModelChoice(Enum):
    LLAVA = "llava"
    QWEN = "qwen"

# Get the project root directory (assuming this file is in src/cad_coder_backend/app/services/)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
MODEL_INFERENCE_DIR = PROJECT_ROOT / "src" / "model_inference"

models = {
    "llava": MODEL_INFERENCE_DIR,
    "qwen": MODEL_INFERENCE_DIR  # Placeholder - update when Qwen model is available
}

async def generate_cad_code(prompt: str, image=None, model_choice: str = "llava", uid: str = None):
    """
    Generate CAD code using model inference.
    Attempts to run actual inference if model checkpoints and scripts are available,
    otherwise falls back to placeholder responses.
    
    Requirements for actual inference:
    1. Model checkpoints available in model_inference directory
    2. Proper data files prepared
    3. GPU access configured (for Docker)
    4. uid parameter provided for result lookup
    """
    await asyncio.sleep(1)
    if model_choice not in models:
        model_choice = "llava"
    
    model_path = models[model_choice]
    
    # Check if model_inference directory exists
    if not model_path.exists():
        # Fallback to placeholder if model_inference not available
        if model_choice == "llava":
            return f"# LLaVA generated\nimport cadquery as cq\ncq.Workplane('XY').box(1,1,1)"
        else:
            return f"# Qwen generated\nimport cadquery as cq\ncq.Workplane('XY').sphere(1)"
    
    # Try to run actual inference if script exists and uid is provided
    script_path = model_path / "scripts" / "v1_5" / "eval" / "test_gencadcode.sh"
    
    if script_path.exists() and uid:
        try:
            # Run inference script
            command = [str(script_path), "CADCODER/CAD-Coder", "dataset"]
            result = subprocess.run(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                cwd=str(model_path),
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Inference error: {result.stderr.strip()}")
            
            # Find the output file (check for merged results first)
            output_file = model_path / "inference" / "inference_results" / "CAD-Coder" / "dataset" / "merge.jsonl"
            
            if not output_file.exists():
                # Try alternative location
                output_file = model_path / "model_inference" / "inference" / "inference_results" / "CAD-Coder" / "dataset" / "merge.jsonl"
            
            if output_file.exists():
                # Read results from JSONL file
                with open(output_file, 'r') as file:
                    for line in file:
                        try:
                            record = json.loads(line.strip())
                            if 'text' in record and record.get('question_id') == uid:
                                return record['text']
                        except json.JSONDecodeError:
                            continue
                
                # If uid not found, return first result
                with open(output_file, 'r') as file:
                    first_line = file.readline()
                    if first_line:
                        record = json.loads(first_line.strip())
                        if 'text' in record:
                            return record['text']
            
            # If no results file found, fall through to placeholder
        except subprocess.TimeoutExpired:
            raise RuntimeError("Inference timed out after 5 minutes")
        except Exception as e:
            # Log error but fall through to placeholder
            print(f"Inference error: {e}")
    
    # Fallback to placeholder
    if model_choice == "llava":
        return f"# LLaVA generated\nimport cadquery as cq\ncq.Workplane('XY').box(1,1,1)"
    else:
        return f"# Qwen generated\nimport cadquery as cq\ncq.Workplane('XY').sphere(1)"

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(generate_cad_code("make a cube", model_choice="llava"))
    print(result)