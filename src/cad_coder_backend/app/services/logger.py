'''
OPTIONAL
You should include logger.py if you want:
1. Unified logging between your FastAPI backend and the external pipeline (so both write into one file such as PIPELINE_RUN.log).
2. Structured log formatting for CI/CD monitoring, or if you later use a tool like GCP Cloud Logging or ELK.
'''
import logging
import os

LOG_PATH = os.getenv("LOG_PATH", "PIPELINE_RUN.log")

def get_logger(name: str = "cad_coder"):
    """
    Returns a configured logger that writes both to console and to PIPELINE_RUN.log
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        # Console
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        # File
        fh = logging.FileHandler(LOG_PATH)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger

'''
Then in any service:

from app.services.logger import get_logger
logger = get_logger(__name__)
logger.info("Pipeline started")
logger.error("Pipeline failed")
'''