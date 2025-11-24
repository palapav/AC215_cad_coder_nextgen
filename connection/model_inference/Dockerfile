# Use an official Python image as a base
FROM python:3.10-slim
# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install conda (Miniconda)
RUN apt-get update && apt-get install -y wget bzip2 && \
    wget "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh" && \
    /bin/bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && \
    rm Miniconda3-latest-Linux-x86_64.sh && \
    /opt/conda/bin/conda clean -afy
ENV PATH /opt/conda/bin:$PATH
# Accept Terms of Service for Anaconda channels
RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

# Suggestion to activate the environment (will not persist)
ENV PATH /opt/conda/envs/llava/bin:$PATH
# Create the llava conda environment and install required packages
RUN conda create -n llava python=3.10 -y

# Activate the environment and install FlashAttention
RUN /bin/bash -c "source activate llava"

# Install required packages
RUN /opt/conda/bin/conda run -n llava pip install --upgrade pip
RUN /opt/conda/bin/conda run -n llava pip install -e .
RUN /opt/conda/bin/conda run -n llava pip install -e ".[train]"
RUN /opt/conda/bin/conda run -n llava pip install datasets
RUN /opt/conda/bin/conda run -n llava pip install peft==0.10.0
RUN pip install torch torchvision torchaudio
RUN /opt/conda/bin/conda run -n llava pip install tensorboard
RUN /opt/conda/bin/conda run -n llava pip install transformers


# Execute your custom script (ensure the script exists in the copied contents)
# Ensure you provide the required arguments correctly
CMD ["conda", "run", "-n", "llava", "/bin/bash", "./scripts/v1_5/eval/test_gencadcode.sh", "CADCODER/CAD-Coder", "cadquery_test_data_subset100", "python", "scripts/generate_model_cad.py", "--dataset_name", "cadquery_test_data_subset100", "--model_tested", "CADCODER/CAD-Coder", "--code_language", "cadquery", "--pc_reps", "3", "--parallel"]