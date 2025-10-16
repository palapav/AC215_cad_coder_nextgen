# cad-coder-nextgen: Fine-tuning and Deploying Large-Scale Vision Language Models for CAD Code Generation 
# Milestone2: AC215 CAD-Coder Project MS2 Documentation

Project Team Members: Yuyan Fan, Jing Xu, Frank Chen, Aditya Palaparthi
Group Name: CAD-Coder

# Project: 
In this project, we aim to design and deploy a scalable AI-chatbot system that enables engineers, students, and hobbyists to generate CAD code interactively from text or image inputs. Users will upload images and type in text to a Chat-GPT style interface and the system will automatically generate Cad Query Python Code. Additionally, our system automates code generation directly from natural inputs (text/images), provides open, reproducible research into model scaling, and offers a flexible, cloud-deployed interface for broader accessibility. It will be powered by a RAG model and fine-tuned models, making it scalable and specialized in the domain of CAD parts design. 	
			
# Milestone2:
In this milestone, we have the components for multimodal data management, including integration and preprocessing, as well as a RAG pipeline with data collection, chunking, and vector database integration.

Project Milestone 2 Organization
├── Readme.md
├── data # DO NOT UPLOAD DATA TO GITHUB, only .gitkeep to keep the directory or a really small sample
├── notebooks
│   └── eda.ipynb
├── references
├── reports
│   └── Statement of Work_Sample.pdf
└── src
    ├── datapipeline
    │   ├── Dockerfile
    │   ├── Pipfile
    │   ├── Pipfile.lock
    │   ├── dataloader.py
    │   ├── docker-shell.sh
    │   ├── preprocess_cv.py
    │   └── preprocess_rag.py
    └── models
        ├── Dockerfile
        ├── docker-shell.sh
        ├── infer_model.py
        ├── model_rag.py
        └── train_model.py

# Data: 
We use the GenCAD dataset (163k image-code pairs of CAD models with CadQuery scripts) from MIT’s CAD-Coder project (link: : CADCODER/GenCAD-Code · Datasets at Hugging Face ). This dataset provides the exact multimodal alignment needed for text-to-code and image-to-code generation. Its large scale and diversity enable both rigorous scaling analysis and deployment of models that generalize to real CAD design tasks.

# Structure of the whole pipeline:(screenshot)


# Data Pipeline Containers:
1. One container processes the 163K dataset(1.6G) by resizing and normalizing the images and storing them back to Google Cloud Storage (GCS).
Input: Source and destination GCS locations, resizing and normalizing parameters, and required dependencies (provided via Docker).
Output: Resized images stored in the specified GCS location.
2. Another container prepares data for the RAG model, including tasks such as chunking, embedding, and populating the vector database.

# Virtual Environment Setup
# Overview
Description of the virtual environment and its purpose.
# Deliverables
Screenshot of running instances (cloud or local).

# Data Pipeline Overview
1. src/datapipeline/dataloader.py
2. src/datapipeline/preprocess_cv.py This script handles preprocessing on our 100GB dataset. It reduces the image sizes to 128x128 (a parameter that can be changed later) to enable faster iteration during processing. The preprocessed dataset is now reduced to 10GB and stored on GCS.
3. src/datapipeline/preprocess_rag.py This script prepares the necessary data for setting up our vector database. It performs chunking, embedding, and loads the data into a vector database (ChromaDB).
    Overall Design Architecture: 
4. src/preprocessing/Dockerfile(s) Our Dockerfiles follow standard conventions, with the exception of some specific modifications described in the Dockerfile/described below.
5. src/preprocessing/pyproject.toml Our configuration file used in Python projects to define build system requirements, package metadata, and dependencies
6. src/preprocessing/docker-compose.yml

# Running Dockerfile
Instructions for running the Dockerfile can be added here. To run Dockerfile - Instructions here

Models container
- This container has scripts for model training, rag pipeline and inference
- Instructions for running the model container - Instructions here

Screenshots of the whole preprocessing pipeline:

#Application Mock-up
https://casual-lion-94885387.figma.site/ 
