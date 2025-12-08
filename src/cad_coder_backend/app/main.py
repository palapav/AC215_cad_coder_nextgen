from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Import routers
from app.routers import generate, history, health, auth, pipeline
from app.services.utils import setup_logging

# ✅ Load environment variables early
load_dotenv()
setup_logging()

# ---------- FastAPI App ----------
app = FastAPI(
    title="CAD-Coder Backend",
    version="1.2.0",
    description="Backend for CAD-Coder supporting model selection, RAG, and pipeline control.",
)

# ---------- Startup Event: Pre-load Qwen model (optional, lazy loading also works) ----------
@app.on_event("startup")
async def startup_event():
    """Initialize Qwen model on startup (optional - lazy loading also works)"""
    try:
        # Pre-initialize Qwen model for faster first request
        from app.services.model_service import _get_qwen_service
        print("[Startup] Pre-initializing Qwen model...")
        _get_qwen_service()
        print("[Startup] ✓ Qwen model ready")
    except Exception as e:
        print(f"[Startup] ⚠️ Qwen model initialization skipped: {e}")
        print("[Startup] Model will be loaded on first use (lazy loading)")

# ---------- CORS (for React frontend) ----------
# In production, frontend and backend are served from the same origin via ingress
# So we need to allow the production IP as well as localhost for development
origins = [
    os.getenv("FRONTEND_ORIGIN", "http://localhost:3000"),
    "http://127.0.0.1:3000",
    "http://136.110.150.2",  # Production IP
    "*",  # Allow all origins for flexibility (ingress handles routing)
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins since ingress handles same-origin routing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Include Routers with /api prefix ----------
api_router = APIRouter(prefix="/api")
api_router.include_router(generate.router)
api_router.include_router(history.router)
api_router.include_router(health.router)
#api_router.include_router(auth.router) # skip auth for now
api_router.include_router(pipeline.router)

# Add a root /api endpoint
@api_router.get("/")
async def api_root():
    return {
        "message": "CAD-Coder API",
        "version": "1.2.0",
        "endpoints": {
            "health": "/api/health/",
            "generate": "/api/generate_cad",
            "history": "/api/history/",
        }
    }

app.include_router(api_router)

# ---------- Root Endpoint ----------
@app.get("/")
async def root():
    return {"message": "CAD-Coder Backend is running successfully."}
