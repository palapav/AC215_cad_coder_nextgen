import os, logging
from dotenv import load_dotenv

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

def ensure_env_vars(*vars):
    missing = [v for v in vars if not os.getenv(v)]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

def init_environment():
    try:
        load_dotenv()
    except PermissionError:
        pass
    setup_logging()
