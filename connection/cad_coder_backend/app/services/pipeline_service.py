import subprocess
import logging
import os
from pathlib import Path
from app.services.utils import detect_project_root

PROJECT_ROOT = detect_project_root()
BACKEND_ROOT = PROJECT_ROOT / "cad_coder_backend"
DATAPIPELINE_DIR = PROJECT_ROOT / "datapipeline" / "data_preprocessing"
PREPROCESS_SCRIPT = DATAPIPELINE_DIR / "preprocess_cv.py"
LOCAL_DATA_DIR = PROJECT_ROOT / "data"


async def run_stage(stage: str, data: str, input_dir: str, output_dir: str, user_id: str, prompt: str, use_docker: bool = False):
    """
    Run one pipeline container (ingestion, preprocess, or rag).
    Must match service name in docker-compose.yml.
    """
    try:
        # For preprocess stage, we need to pass arguments to the Python script
        if stage == "preprocess":
            if not PREPROCESS_SCRIPT.exists():
                raise FileNotFoundError(
                    f"Preprocess script not found at {PREPROCESS_SCRIPT}. Check project mounts."
                )

            # The output_dir should be /app/data inside the container (mapped to ../data)
            container_output_dir = "/app/data"
            # Convert host path to container path if needed
            # If it's an absolute path outside /app/data, try to map it to /workspace
            container_image_path = data
            if os.path.isabs(data) and not data.startswith("/app") and not data.startswith("/workspace"):
                container_image_path = data
            
            # Build the command for local execution or Docker
            if use_docker:
                cmd = [
                    "docker", "compose", 
                    "-f", "docker-compose.yml",
                    "run", "--rm",
                    stage,
                    "python", "preprocess_cv.py",
                    "--input_dir", container_image_path,
                    "--output_dir", container_output_dir,
                    "--uid", str(user_id),
                    "--prompt", prompt
                ]
            else:
                # Local execution
                cmd = [
                    "python", str(PREPROCESS_SCRIPT),
                    "--input_dir", container_image_path,
                    "--output_dir", str(LOCAL_DATA_DIR),
                    "--uid", str(user_id),
                    "--prompt", prompt
                ]
        else:
            # For other stages, use the original format with local execution option
            if use_docker:
                cmd = ["docker", "compose", "-f", "docker-compose.yml", "run", "--rm", stage, data]
            else:
                # Local execution: you need to implement how to run this stage locally
                cmd = [stage, data]  # This assumes the stage can be directly executed locally
        
        logging.info(f"Running command: {' '.join(cmd)}")
        cwd = BACKEND_ROOT if BACKEND_ROOT.exists() else Path(__file__).resolve().parents[2]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=str(cwd)
        )
        logging.info(f"{stage.capitalize()} pipeline completed successfully.")
        logging.info(f"Output: {result.stdout}")
        if result.stderr:
            logging.warning(f"Stderr: {result.stderr}")
        return {"stage": stage, "status": "success", "output": result.stdout}
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running {stage} pipeline: {e.stderr}")
        logging.error(f"Command output: {e.stdout}")
        return {"stage": stage, "status": "error", "error": e.stderr, "output": e.stdout}
