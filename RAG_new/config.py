import os
from dotenv import load_dotenv

# Configuration constants
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
INDEX_NAME = "cadcoder-mm-index"
ENDPOINT_NAME = "cadcoder-mm-endpoint"
DEPLOYED_INDEX_ID = "cadcoder_mm_deployed"

def load_config():
    """Load environment variables and configuration."""
    load_dotenv()
    
    project_id = os.getenv("PROJECT_ID")
    gcs_data_uri = os.getenv("GCS_DATA_URI")
    location = os.getenv("LOCATION", "us-central1")
    
    if not project_id or not gcs_data_uri:
        raise ValueError("Missing PROJECT_ID or GCS_DATA_URI in .env")
    
    return {
        "project_id": project_id,
        "gcs_uri": gcs_data_uri,
        "location": location
    }