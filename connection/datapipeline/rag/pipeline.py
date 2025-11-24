#!/usr/bin/env python
"""
pipeline.py
-----------
RAG pipeline that reads preprocessed data and creates vector embeddings.

Reads from: gs://{bucket}/processed_data/{split}/
"""

import os
import logging
import argparse
from vertexai import init as vertex_init
from google.cloud import aiplatform

from config import DEPLOYED_INDEX_ID
from storage_utils import list_gcs_files
from embedding_generator import EmbeddingGenerator
from vector_search import VectorSearchManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def initialize_vertex_ai(project_id: str, location: str):
    """Initialize Vertex AI SDKs."""
    aiplatform.init(project=project_id, location=location)
    vertex_init(project=project_id, location=location)
    logging.info(f"Vertex AI initialized for project: {project_id}, location: {location}")

def main():
    parser = argparse.ArgumentParser(description="RAG Pipeline for CAD-Coder")
    parser.add_argument("--bucket", type=str, default=os.getenv("GCS_BUCKET", "cad-coder-nextgen-data"))
    parser.add_argument("--split", type=str, default=os.getenv("PIPELINE_SPLIT", "test"))
    parser.add_argument("--project_id", type=str, default=os.getenv("PROJECT_ID", "cad-coder-nextgen"))
    parser.add_argument("--location", type=str, default=os.getenv("LOCATION", "us-central1"))
    args = parser.parse_args()
    
    # Construct GCS URI from preprocessed data
    gcs_uri = f"gs://{args.bucket}/processed_data/{args.split}"
    
    logging.info("=" * 60)
    logging.info("🧠 CAD-CODER RAG PIPELINE")
    logging.info("=" * 60)
    logging.info(f"📥 Reading preprocessed data from: {gcs_uri}")
    logging.info(f"📊 Split: {args.split}")
    
    try:
        initialize_vertex_ai(args.project_id, args.location)
        
        files = list_gcs_files(gcs_uri)
        if not files:
            raise RuntimeError(f"No files found in {gcs_uri}")
        
        logging.info(f"📋 Found {len(files)} files to process")
        
        embedding_generator = EmbeddingGenerator()
        datapoints = embedding_generator.generate_embeddings(files)
        
        if not datapoints:
            raise RuntimeError("No embeddings were generated. Check file content and types.")
        
        # Get dimensions from first datapoint
        dimensions = len(datapoints[0]["feature_vector"])
        logging.info(f"📐 Vector dimensions: {dimensions}")
        
        vector_search = VectorSearchManager(args.project_id, args.location)
        vector_search.setup_infrastructure(dimensions)
        
        vector_search.upsert_datapoints(datapoints)
        
        logging.info("\n" + "=" * 60)
        logging.info("✅ RAG PIPELINE COMPLETE")
        logging.info("=" * 60)
        logging.info(f"📊 Split processed: {args.split}")
        logging.info(f"📦 Source: {gcs_uri}")
        logging.info(f"🔢 Total vectors upserted: {len(datapoints)}")
        logging.info(f"📍 Index: {vector_search.index.resource_name}")
        logging.info(f"🔗 Endpoint: {vector_search.endpoint.resource_name}")
        
    except Exception as e:
        logging.error(f"❌ RAG pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

# import logging
# from vertexai import init as vertex_init
# from google.cloud import aiplatform

# from config import load_config, INDEX_NAME, ENDPOINT_NAME, DEPLOYED_INDEX_ID
# from storage_utils import list_gcs_files
# from embedding_generator import EmbeddingGenerator
# from vector_search import VectorSearchManager

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s"
# )

# def initialize_vertex_ai(config: dict):
#     """Initialize Vertex AI SDKs."""
#     aiplatform.init(project=config["project_id"], location=config["location"])
#     vertex_init(project=config["project_id"], location=config["location"])
#     logging.info(f"Vertex AI initialized for project: {config['project_id']}, location: {config['location']}")


# def main():
#     logging.info("======== Starting Vertex AI Multi-Modal RAG Pipeline ========")
    
#     try:
#         # Load configuration
#         config = load_config()
        
#         # Initialize Vertex AI
#         initialize_vertex_ai(config)
        
#         # List files from GCS
#         files = list_gcs_files(config["gcs_uri"])
#         if not files:
#             raise RuntimeError("No files found in GCS_DATA_URI")
        
#         # Generate embeddings
#         embedding_generator = EmbeddingGenerator()
#         datapoints = embedding_generator.generate_embeddings(files)
        
#         if not datapoints:
#             raise RuntimeError("No embeddings generated. Check file types and content.")
        
#         # --- THIS IS THE FIX ---
#         # Get vector dimensions from the first datapoint using the correct key
#         dimensions = len(datapoints[0]["feature_vector"]) 
        
#         # Setup vector search
#         vector_search = VectorSearchManager(config["project_id"], config["location"])
#         vector_search.setup_infrastructure(dimensions)
        
#         # Upsert datapoints
#         vector_search.upsert_datapoints(datapoints)
        
#         # Log success
#         logging.info("\n======== ✅ Pipeline Finished Successfully ✅ ========")
#         logging.info(f"- Index:        {vector_search.index.resource_name}")
#         logging.info(f"- Endpoint:     {vector_search.endpoint.resource_name}")
#         logging.info(f"- Deployed ID:  {DEPLOYED_INDEX_ID}")
#         logging.info(f"- Total Vectors: {len(datapoints)}")
        
#     except Exception as e:
#         logging.error(f"❌ Pipeline failed with critical error: {e}")
#         # Re-raise the exception to get a full traceback
#         raise

# if __name__ == "__main__":
#     main()

# # def main():
# #     logging.info("======== Starting Vertex AI Multi-Modal RAG Pipeline ========")
    
# #     try:
# #         # Load configuration
# #         config = load_config()
        
# #         # Initialize Vertex AI
# #         initialize_vertex_ai(config)
        
# #         # List files from GCS
# #         files = list_gcs_files(config["gcs_uri"])
# #         if not files:
# #             raise RuntimeError("No files found in GCS_DATA_URI")
        
# #         # Generate embeddings
# #         embedding_generator = EmbeddingGenerator()
# #         datapoints = embedding_generator.generate_embeddings(files)
        
# #         if not datapoints:
# #             raise RuntimeError("No embeddings generated. Check file types and content.")
        
# #         # Setup vector search
# #         dimensions = len(datapoints[0]["vector"])
# #         vector_search = VectorSearchManager(config["project_id"], config["location"])
# #         vector_search.setup_infrastructure(dimensions)
        
# #         # Upsert datapoints
# #         vector_search.upsert_datapoints(datapoints)
        
# #         # Log success
# #         logging.info("\n======== Pipeline Finished Successfully ========")
# #         logging.info(f"- Index:        {vector_search.index.resource_name}")
# #         logging.info(f"- Endpoint:     {vector_search.endpoint.resource_name}")
# #         logging.info(f"- Deployed ID:  {DEPLOYED_INDEX_ID}")
# #         logging.info(f"- Total Vectors: {len(datapoints)}")
        
# #         # Final statistics
# #         image_count = len([dp for dp in datapoints if dp.get("metadata", {}).get("type") == "image"])
# #         code_count = len([dp for dp in datapoints if dp.get("metadata", {}).get("type") == "code"])
# #         paired_images_count = len([dp for dp in datapoints if dp.get("metadata", {}).get("type") == "image" and dp.get("metadata", {}).get("paired_item")])
        
# #         logging.info(f"- Images: {image_count}, Code chunks: {code_count}, Paired images: {paired_images_count}")
        
# #     except Exception as e:
# #         logging.error(f"❌ Pipeline failed with critical error: {e}")
# #         raise

# # if __name__ == "__main__":
# #     main()