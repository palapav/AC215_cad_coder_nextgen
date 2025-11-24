import asyncio
import os
import json
import subprocess
from enum import Enum
from pathlib import Path
import sys

class ModelChoice(Enum):
    LLAVA = "llava"
    QWEN = "qwen"

# Get the project root directory (assuming this file is in src/cad_coder_backend/app/services/)
# In Docker: /app/app/services/model_service.py -> /app/model_inference/qwen
# In local: src/cad_coder_backend/app/services/model_service.py -> src/model_inference/qwen
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
MODEL_INFERENCE_DIR = PROJECT_ROOT / "src" / "model_inference"
QWEN_DIR = MODEL_INFERENCE_DIR / "qwen"

# Fallback: Check if qwen is mounted directly at /app/model_inference/qwen (Docker)
if not QWEN_DIR.exists():
    docker_qwen_path = Path("/app/model_inference/qwen")
    if docker_qwen_path.exists():
        QWEN_DIR = docker_qwen_path
        print(f"[Model Service] Using Docker-mounted Qwen path: {QWEN_DIR}")

# Add qwen directory to path for imports
if str(QWEN_DIR) not in sys.path:
    sys.path.insert(0, str(QWEN_DIR))

models = {
    "llava": MODEL_INFERENCE_DIR,
    "qwen": QWEN_DIR
}

# Lazy load Qwen service
_qwen_service = None

def _get_qwen_service():
    """Lazy load Qwen inference service"""
    global _qwen_service
    if _qwen_service is None:
        try:
            print(f"[Model Service] QWEN_DIR: {QWEN_DIR}")
            print(f"[Model Service] QWEN_DIR exists: {QWEN_DIR.exists()}")
            
            # Check if Qwen directory exists
            if not QWEN_DIR.exists():
                raise FileNotFoundError(f"Qwen directory not found: {QWEN_DIR}")
            
            # List files in Qwen directory for debugging
            if QWEN_DIR.exists():
                files = list(QWEN_DIR.iterdir())
                print(f"[Model Service] Files in Qwen directory: {[f.name for f in files[:10]]}")
            
            # Try to import the inference service
            try:
                from inference_service import initialize_model, generate_cad_code as qwen_generate
                print(f"[Model Service] Successfully imported inference_service from {QWEN_DIR}")
            except ImportError as e:
                raise ImportError(f"Failed to import Qwen inference service from {QWEN_DIR}: {e}. Make sure inference_service.py exists.")
            
            checkpoint_path = QWEN_DIR / "final_model.pt"
            base_model = "Qwen/Qwen3-VL-2B-Instruct"
            
            print(f"[Model Service] Initializing Qwen model...")
            print(f"[Model Service] Checkpoint path: {checkpoint_path}")
            print(f"[Model Service] Checkpoint exists: {checkpoint_path.exists()}")
            print(f"[Model Service] Base model: {base_model}")
            
            if checkpoint_path.exists():
                print(f"[Model Service] Loading fine-tuned checkpoint from: {checkpoint_path}")
                initialize_model(
                    checkpoint_path=str(checkpoint_path),
                    base_model=base_model
                )
            else:
                print(f"[Model Service] Warning: Checkpoint not found at {checkpoint_path}, using base model only")
                print(f"[Model Service] Looking for checkpoint in: {QWEN_DIR}")
                # Try alternative checkpoint names
                alt_checkpoints = ["checkpoint.pt", "model.pt", "best_model.pt"]
                found_checkpoint = None
                for alt_name in alt_checkpoints:
                    alt_path = QWEN_DIR / alt_name
                    if alt_path.exists():
                        found_checkpoint = alt_path
                        print(f"[Model Service] Found alternative checkpoint: {alt_path}")
                        break
                
                if found_checkpoint:
                    initialize_model(
                        checkpoint_path=str(found_checkpoint),
                        base_model=base_model
                    )
                else:
                    initialize_model(
                        checkpoint_path=None,
                        base_model=base_model
                    )
            
            _qwen_service = qwen_generate
            print("[Model Service] ✓ Qwen service initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize Qwen service: {e}"
            print(f"[Model Service] ⚠️ {error_msg}")
            import traceback
            traceback.print_exc()
            # Store error for debugging but don't set service to None
            # This way we can retry or get better error messages
            raise RuntimeError(error_msg) from e
    return _qwen_service

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
    
    # Try Qwen inference if selected
    if model_choice == "qwen":
        try:
            qwen_service = _get_qwen_service()
            if qwen_service:
                # Handle image input
                image_path = None
                pil_image = None
                
                if image:
                    # If image is a PIL Image, use it directly
                    from PIL import Image
                    if isinstance(image, Image.Image):
                        pil_image = image
                    elif isinstance(image, str):
                        # If it's a path string
                        image_path = image
                    elif isinstance(image, Path):
                        image_path = str(image)
                
                # Run Qwen inference in thread pool to avoid blocking
                import concurrent.futures
                loop = asyncio.get_event_loop()
                
                def run_qwen_inference():
                    """Wrapper function to run Qwen inference synchronously"""
                    return qwen_service(
                        prompt=prompt,
                        image=pil_image,
                        image_path=image_path,
                        max_new_tokens=4096,
                        temperature=1.0  # Match eval_model.py default
                    )
                
                # Run in executor and await the result
                result = await loop.run_in_executor(None, run_qwen_inference)
                
                if result and result.strip():
                    return result.strip()
                else:
                    raise RuntimeError("Qwen inference returned empty result")
        except Exception as e:
            print(f"[Model Service] Qwen inference error: {e}")
            import traceback
            traceback.print_exc()
            # Re-raise the error so frontend gets proper error message
            raise RuntimeError(f"Qwen inference failed: {str(e)}") from e
    
    # Fallback to placeholder
    if model_choice == "llava":
        return f"# LLaVA generated\nimport cadquery as cq\ncq.Workplane('XY').box(1,1,1)"
    else:
        return f"# Qwen generated\nimport cadquery as cq\ncq.Workplane('XY').sphere(1)"

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(generate_cad_code("make a cube", model_choice="llava"))
    print(result)