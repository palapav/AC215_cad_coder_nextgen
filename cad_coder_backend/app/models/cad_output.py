from pydantic import BaseModel
from typing import Optional

class CADOutput(BaseModel):
    prompt: str
    cad_code: str
    gcs_uri: Optional[str] = None
