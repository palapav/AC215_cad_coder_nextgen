from fastapi import FastAPI
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

# ---------- CORS (for React frontend) ----------
origins = [
    os.getenv("FRONTEND_ORIGIN", "http://localhost:3000"),
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Include Routers ----------
app.include_router(generate.router)
app.include_router(history.router)
app.include_router(health.router)
#app.include_router(auth.router) # skip auth for now
app.include_router(pipeline.router)

# ---------- Root Endpoint ----------
@app.get("/")
async def root():
    return {"message": "CAD-Coder Backend is running successfully."}
