from pydantic import BaseModel, validator
from typing import Optional, Union
from .model_choice import ModelChoice

class CADInput(BaseModel):
    prompt: str
    image_path: Optional[str] = None
    user_id: Optional[str] = "default"
    model_choice: Optional[Union[ModelChoice, str]] = ModelChoice.llava
    rag_context: Optional[str] = None  #retrieved context for RAG
    
    @validator('model_choice', pre=True)
    def validate_model_choice(cls, v):
        """Convert string to ModelChoice enum if needed"""
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower == "qwen":
                return ModelChoice.qwen
            elif v_lower == "llava":
                return ModelChoice.llava
            else:
                # Try to match by enum value
                try:
                    return ModelChoice(v_lower)
                except ValueError:
                    print(f"[CADInput] Warning: Invalid model_choice '{v}', defaulting to llava")
                    return ModelChoice.llava
        elif isinstance(v, ModelChoice):
            return v
        else:
            print(f"[CADInput] Warning: Unexpected model_choice type '{type(v)}', defaulting to llava")
            return ModelChoice.llava
