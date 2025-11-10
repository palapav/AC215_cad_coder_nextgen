import os

def ensure_env_vars(*vars):
    """Check that all environment variables are set."""
    missing = [v for v in vars if not os.getenv(v)]
    if missing:
        raise EnvironmentError(f"Missing env vars: {', '.join(missing)}")
