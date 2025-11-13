import subprocess, logging

def run_stage(stage: str):
    """
    Run one pipeline container (ingestion, preprocess, or rag).
    Must match service name in docker-compose.yml.
    """
    try:
        cmd = ["docker", "compose", "run", stage]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logging.info(f"{stage.capitalize()} pipeline completed successfully.")
        return {"stage": stage, "status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running {stage} pipeline: {e.stderr}")
        return {"stage": stage, "status": "error", "error": e.stderr}
