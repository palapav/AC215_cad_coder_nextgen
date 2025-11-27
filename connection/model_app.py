import modal
import subprocess
import time

# 1. Define the main App
app = modal.App("cad-coder-unified")

# 2. Define your Images GLOBALLY (outside the functions)
# This tells Modal how to build the environment before running the code.
# Note: Images are built lazily when first used, but defining them here
# allows Modal to cache and optimize builds.

# Frontend image - use the Dockerfile (nginx-based)
# Note: We'll comment out the frontend function for now since Modal requires Python
# For static sites, consider using Modal's static file serving or a separate deployment
frontend_image = (
    modal.Image.from_dockerfile(
        "./ui/Dockerfile",
        context_dir="./ui",
        force_build=False,
    )
)

# Backend image - Python with ML dependencies
backend_image = (
    modal.Image.from_dockerfile(
        "./cad_coder_backend/Dockerfile",
        context_dir="./cad_coder_backend",
        force_build=False,  # Use cache when possible
    )
    .add_local_dir("./cad_coder_backend", remote_path="/root/backend")
    .add_local_dir("./datapipeline", remote_path="/workspace/datapipeline")
)

# Preprocessing image - lightweight data processing
preprocessing_image = (
    modal.Image.from_dockerfile(
        "./datapipeline/data_preprocessing/Dockerfile",
        context_dir="./datapipeline/data_preprocessing",
        force_build=False,  # Use cache when possible
    )
    .add_local_dir("./datapipeline", remote_path="/root/datapipeline")
)

# Inference image - optimized to avoid conda and heavy train dependencies
inference_image = (
    modal.Image.from_dockerfile(
        "./model_inference/Dockerfile",
        context_dir="./model_inference",
        force_build=False,  # Use cache when possible
    )
    .add_local_dir("./model_inference", remote_path="/root/inference")
)

# 3. Define the Functions
# We use the images defined above. We also MOUNT the local folders
# so the code inside the container can see your files.

# Frontend function commented out - Modal requires Python in images
# For now, deploy the frontend separately or use a different approach
# @app.function(image=frontend_image)
# @modal.web_server(port=80)
# def frontend():
#     pass

@app.function(image=backend_image)
@modal.web_server(port=8000, startup_timeout=60) # Standard API port
def backend():
    """Start the FastAPI backend server."""
    import os
    import sys
    
    # Change to the app directory (Dockerfile sets WORKDIR to /app)
    os.chdir('/app')
    
    # Start uvicorn directly (Modal will keep container alive)
    # Use exec to replace the process so Modal can track it
    os.execvp("uvicorn", [
        "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000"
    ])

@app.function(image=preprocessing_image)
def preprocessing():
    print("Starting preprocessing...")
    # Add your logic here or run a script
    # subprocess.run("python /root/datapipeline/process.py", shell=True)

@app.function(
    image=inference_image,
    gpu="H100", # Requesting H100 GPU
)
def inference():
    print("Starting inference on H100...")
    # Add your logic here
    # subprocess.run("python /root/inference/predict.py", shell=True)

# 4. Local Entrypoint
if __name__ == "__main__":
    # This allows you to run "python model_app.py" to deploy everything
    print("To run this locally for dev, use: modal serve model_app.py")
    print("To deploy to the cloud, use: modal deploy model_app.py")