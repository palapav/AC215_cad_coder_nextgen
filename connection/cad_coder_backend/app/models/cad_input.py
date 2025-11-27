from pydantic import BaseModel
from typing import Optional
from .model_choice import ModelChoice

class CADInput(BaseModel):
    prompt: str
    image_path: Optional[str] = None
    user_id: Optional[str] = "default"
    model_choice: Optional[ModelChoice] = ModelChoice.llava
    rag_context: Optional[str] = None  #retrieved context for RAG
