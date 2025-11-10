from google.cloud import storage
import os, tempfile

BUCKET_NAME = os.getenv("GCS_BUCKET", "cad-coder-bucket")

def upload_cad_code(prompt: str, cad_code: str):
    """
    Uploads the generated CAD code to Google Cloud Storage
    and returns the gs:// URI.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    filename = f"generated/{prompt.replace(' ', '_')}.py"
    blob = bucket.blob(filename)

    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(cad_code)
        temp_path = f.name

    blob.upload_from_filename(temp_path)
    os.remove(temp_path)
    return f"gs://{BUCKET_NAME}/{filename}"
