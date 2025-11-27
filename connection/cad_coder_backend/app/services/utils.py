import os
import logging
from pathlib import Path
from functools import lru_cache
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
    load_dotenv()
    setup_logging()


@lru_cache(maxsize=1)
def detect_project_root(marker: str = "datapipeline") -> Path:
    """
    Locate the monorepo root regardless of whether we are running on host or inside Docker.
    Falls back to /workspace (docker-compose mount) if walking parents fails.
    Also handles Modal deployment where datapipeline is mounted at /workspace/datapipeline.
    """
    current_dir = Path(__file__).resolve().parent
    
    # First, try walking up from current directory
    for parent in [current_dir] + list(current_dir.parents):
        if (parent / marker).exists():
            return parent

    # Check /workspace (docker-compose mount or Modal mount)
    workspace_root = Path("/workspace")
    if workspace_root.exists():
        # Check if marker exists directly in workspace
        if (workspace_root / marker).exists():
            return workspace_root
        # Check if we're in Modal and datapipeline is at /workspace/datapipeline
        if (workspace_root / "datapipeline").exists():
            return workspace_root

    # For Modal: check if we're in /app and datapipeline might be at /workspace
    app_dir = Path("/app")
    if app_dir.exists():
        workspace_check = Path("/workspace") / marker
        if workspace_check.exists():
            return Path("/workspace")

    # Last resort: if we can't find it, return /app as project root (Modal case)
    # This allows the app to start even if datapipeline isn't available
    if app_dir.exists():
        logging.warning(
            f"Could not find '{marker}' directory. Using /app as project root. "
            "Some pipeline features may not work."
        )
        return app_dir

    raise FileNotFoundError(
        f"Unable to determine project root. Looking for '{marker}' starting from {current_dir}"
    )
