from pydantic import BaseModel
from typing import Optional
from .model_choice import ModelChoice

class CADOutput(BaseModel):
    prompt: str
    cad_code: str
    model: Optional[ModelChoice] = None        # record which model generated the code
    gcs_uri: Optional[str] = None
    rag_used: Optional[bool] = False           # indicate if RAG was applied
    rag_context: Optional[str] = None          # optional context returned from RAG
    pipeline_stage: Optional[str] = None       # track which pipeline stage (e.g., 'generate', 'rag', 'preprocess')
