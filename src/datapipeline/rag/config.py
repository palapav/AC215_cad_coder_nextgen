import os

# Configuration constants (can be overridden via environment variables)
RETRY_ATTEMPTS = int(os.getenv("RAG_RETRY_ATTEMPTS", "3"))
RETRY_DELAY = int(os.getenv("RAG_RETRY_DELAY", "5"))
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))
INDEX_NAME = os.getenv("RAG_INDEX_NAME", "cadcoder-mm-index")
ENDPOINT_NAME = os.getenv("RAG_ENDPOINT_NAME", "cadcoder-mm-endpoint")
DEPLOYED_INDEX_ID = os.getenv("RAG_DEPLOYED_INDEX_ID", "test_backend_rag_model_inf_1765410974366")