from google.cloud import storage
import os, tempfile

BUCKET_NAME = os.getenv("GCS_BUCKET", "cad-coder-bucket")

def upload_cad_code(prompt: str, cad_code: str):
    """
    Uploads the generated CAD code to Google Cloud Storage
    and returns the gs:// URI. 
    If no valid credentials are found, skips upload and returns a local placeholder.
    """
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not credentials_path or not os.path.exists(credentials_path):
        print("⚠️  No valid GCS credentials found. Skipping upload (local mode).")
        return f"local://{prompt.replace(' ', '_')}.py"

    try:
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

    except Exception as e:
        print(f"⚠️  GCS upload failed: {e}. Returning local path instead.")
        return f"local://{prompt.replace(' ', '_')}.py"

if __name__ == "__main__":
    uri = upload_cad_code("cube_test", "import cadquery as cq\nprint('Cube')")
    print(uri)

