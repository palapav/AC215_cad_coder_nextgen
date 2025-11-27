import asyncio
import subprocess
import os
import json
from pathlib import Path
from app.services.utils import detect_project_root

# Try to load environment variables if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, use os.getenv directly
    pass

def get_model_inference_path(use_docker: bool | None = None):
    """
    Get the path to model_inference directory.
    Checks environment variable first, then tries relative paths.
    """
    env_path = os.getenv("MODEL_INFERENCE_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    if use_docker is None:
        use_docker = Path("/workspace/model_inference").exists()

    candidates = []

    workspace_path = Path("/workspace/model_inference")
    if use_docker and workspace_path.exists():
        candidates.append(workspace_path)

    try:
        project_root = detect_project_root(marker="model_inference")
    except FileNotFoundError:
        project_root = detect_project_root()
    candidates.append(project_root / "model_inference")

    app_path = Path("/app/model_inference")
    candidates.append(app_path)

    for candidate in candidates:
        if candidate and candidate.exists():
            scripts_path = candidate / "scripts" / "v1_5" / "eval" / "test_gencadcode.sh"
            if scripts_path.exists():
                return str(candidate)
    
    checked_paths = [env_path] + [str(c) for c in candidates]
    existing_paths = [p for p in checked_paths if p and os.path.exists(p)]
    
    raise FileNotFoundError(
        f"Could not find model_inference directory with scripts. "
        f"Checked paths: {checked_paths}. "
        f"Existing directories (but missing scripts): {existing_paths}. "
        f"Please ensure model_inference is mounted at /workspace/model_inference or set MODEL_INFERENCE_PATH environment variable."
    )

async def generate_cad_code(prompt: str, uid: str, image=None, model_choice: str = "llava"):
    """
    Generate CAD code using the model inference pipeline.
    """
    try:
        # Get the model inference path
        model_inf_path = get_model_inference_path()
        script_path = os.path.join(model_inf_path, "scripts", "v1_5", "eval", "test_gencadcode.sh")
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script not found at: {script_path}")
        print(script_path)
        # Make script executable
        os.chmod(script_path, 0o755)
        
        # Run the inference script
        # Note: This script expects to run from the model_inference directory
        command = ["/bin/bash", script_path, "CADCODER/CAD-Coder", "dataset"]
        
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=model_inf_path,  # Run from model_inference directory
            check=False  # Don't raise on non-zero exit
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Script execution failed: {result.stderr.strip()}")
        
        # Find the output file
        # The script outputs to: ./inference/inference_results/CAD-Coder/dataset/merge.jsonl
        output_file = os.path.join(
            model_inf_path,
            "inference",
            "inference_results",
            "CAD-Coder",
            "dataset",
            "merge.jsonl"
        )
        
        if not os.path.exists(output_file):
            raise FileNotFoundError(f"Output file not found: {output_file}")
        
        # Read and parse the JSONL file
        with open(output_file, 'r') as file:
            for line in file:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    # Check if this record matches our query
                    # For now, return the first valid CAD code we find
                    if 'text' in record:
                        return record['text']
                except json.JSONDecodeError:
                    continue
        
        raise ValueError("No valid CAD code found in output file.")
        
    except Exception as e:
        raise RuntimeError(f"Error generating CAD code: {str(e)}")

# if __name__ == "__main__":
#     import asyncio
#     result = asyncio.run(generate_cad_code("make a cube", model_choice="llava"))
#     print(result)