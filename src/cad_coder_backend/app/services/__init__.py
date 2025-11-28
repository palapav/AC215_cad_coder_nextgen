"""
Service layer initialization for CAD-Coder backend.
Each service handles a specific task:
- model_service:  run LLaVA/Qwen inference
- db_service:     MongoDB operations
- gcs_service:    Google Cloud Storage I/O
- auth_service:   Google token verification
- rag_service:    RAG retrieval logic
- pipeline_service: triggers ingestion/preprocess/RAG containers
- utils:          shared utilities
"""
