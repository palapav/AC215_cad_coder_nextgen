"""
Router module: defines all API routes for the CAD-Coder backend.
Includes endpoints for:
- /generate_cad : model inference
- /history      : data retrieval
- /health       : system status
"""
from fastapi import APIRouter

# Optional central router aggregation (if you prefer single include)
router = APIRouter()

from . import generate, history, health  # noqa: F401
