from pydantic import BaseModel
from typing import Optional

class CADInput(BaseModel):
    prompt: str
    image_path: Optional[str] = None
    user_id: Optional[str] = "default"
