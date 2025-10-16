import os
import tempfile
import logging
from typing import List, Tuple
from google.cloud import storage
from vertexai.preview.vision_models import Image

def _split_gs_uri(gs_uri: str) -> Tuple[str, str]:
    """Split GCS URI into bucket and prefix."""
    assert gs_uri.startswith("gs://")
    path = gs_uri[len("gs://"):]
    bucket = path.split("/")[0]
    prefix = path[len(bucket) + 1:] if len(path) > len(bucket) else ""
    return bucket, prefix

def list_gcs_files(gs_uri: str) -> List[str]:
    """List all supported files in GCS."""
    client = storage.Client()
    bucket_name, prefix = _split_gs_uri(gs_uri)
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    
    supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.jsonl', '.txt')
    files = [
        f"gs://{bucket_name}/{b.name}" for b in blobs 
        if not b.name.endswith("/") and b.name.lower().endswith(supported_extensions)
    ]
    logging.info(f"Found {len(files)} supported files in {gs_uri}")
    return files

def read_gcs_text(gs_uri: str) -> str:
    """Read text content from GCS."""
    client = storage.Client()
    bucket_name, prefix = _split_gs_uri(gs_uri)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(prefix)
    return blob.download_as_text()

def load_image_from_gcs(gcs_uri: str) -> Image:
    """Load image from GCS for Vertex AI."""
    try:
        return Image.load_from_file(gcs_uri)
    except Exception as e:
        logging.warning(f"Direct loading failed, trying download method: {e}")
        client = storage.Client()
        bucket_name = gcs_uri.replace("gs://", "").split("/")[0]
        blob_name = "/".join(gcs_uri.replace("gs://", "").split("/")[1:])
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        extension = os.path.splitext(blob_name)[1].lower() or '.png'
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            blob.download_to_filename(temp_file.name)
            image = Image.load_from_file(temp_file.name)
            os.unlink(temp_file.name)
            return image

def extract_image_filename(image_path: str) -> str:
    """Extract filename from image path."""
    return os.path.basename(image_path)

def find_matching_image_uri(image_files: List[str], target_filename: str) -> str:
    """Find matching image URI by filename."""
    for image_uri in image_files:
        if image_uri.endswith(target_filename):
            return image_uri
    return None