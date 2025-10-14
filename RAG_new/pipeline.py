
import logging
from vertexai import init as vertex_init
from google.cloud import aiplatform

from config import load_config, DEPLOYED_INDEX_ID
from storage_utils import list_gcs_files
from embedding_generator import EmbeddingGenerator
from vector_search import VectorSearchManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def initialize_vertex_ai(config: dict):
    """Initialize Vertex AI SDKs."""
    aiplatform.init(project=config["project_id"], location=config["location"])
    vertex_init(project=config["project_id"], location=config["location"])
    logging.info(f"Vertex AI initialized for project: {config['project_id']}, location: {config['location']}")

def main():
    logging.info("======== Starting Vertex AI Multi-Modal RAG Pipeline ========")
    
    try:
        config = load_config()
        initialize_vertex_ai(config)
        
        files = list_gcs_files(config["gcs_uri"])
        if not files:
            raise RuntimeError(f"No files found in GCS bucket: {config['gcs_uri']}")
        
        embedding_generator = EmbeddingGenerator()
        datapoints = embedding_generator.generate_embeddings(files)
        
        if not datapoints:
            raise RuntimeError("No embeddings were generated. Check file content and types.")
        
        # CORRECTED: Use 'feature_vector' to get dimensions
        dimensions = len(datapoints[0]["feature_vector"])
        
        vector_search = VectorSearchManager(config["project_id"], config["location"])
        vector_search.setup_infrastructure(dimensions)
        
        vector_search.upsert_datapoints(datapoints)
        
        logging.info("\n======== ✅ Pipeline Finished Successfully ✅ ========")
        logging.info(f"- Index:        {vector_search.index.resource_name}")
        logging.info(f"- Endpoint:     {vector_search.endpoint.resource_name}")
        logging.info(f"- Total Vectors Upserted: {len(datapoints)}")
        
    except Exception as e:
        logging.error(f"❌ Pipeline failed with critical error: {e}", exc_info=True)
        # Re-raise to ensure the script exits with a non-zero status code
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