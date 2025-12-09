#!/usr/bin/env python3
"""
Qwen Inference Server for GKE Deployment

This module provides a FastAPI-based inference server for the fine-tuned
Qwen3-VL model, designed to run on GKE with GPU support and auto-scaling.

Features:
- Health and readiness endpoints for Kubernetes probes
- Batched inference support
- Request queuing and timeout handling
- Prometheus metrics for monitoring
- Graceful shutdown handling
"""

import asyncio
import base64
import io
import logging
import os
import signal
import sys
import time
from contextlib import asynccontextmanager
from typing import Optional

import torch
import uvicorn
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

BASE_MODEL = os.getenv("QWEN_BASE_MODEL", "Qwen/Qwen3-VL-2B-Instruct")
CHECKPOINT_PATH = os.getenv("CHECKPOINT_PATH", "/models/qwen/final_model.pt")
MAX_NEW_TOKENS = int(os.getenv("QWEN_MODAL_MAX_NEW_TOKENS", "4096"))
DEFAULT_TEMPERATURE = float(os.getenv("QWEN_MODAL_TEMPERATURE", "0.0"))
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "4"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "300"))
PORT = int(os.getenv("PORT", "8080"))

# =============================================================================
# Prometheus Metrics
# =============================================================================

REQUEST_COUNT = Counter(
    "qwen_inference_requests_total",
    "Total number of inference requests",
    ["status"]
)
REQUEST_LATENCY = Histogram(
    "qwen_inference_latency_seconds",
    "Inference request latency in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)
MODEL_LOADED = Gauge(
    "qwen_model_loaded",
    "Whether the model is loaded and ready"
)
GPU_MEMORY_USED = Gauge(
    "qwen_gpu_memory_used_bytes",
    "GPU memory used in bytes"
)
QUEUE_SIZE = Gauge(
    "qwen_inference_queue_size",
    "Number of requests in queue"
)

# =============================================================================
# Global State
# =============================================================================

model_state = {
    "model": None,
    "processor": None,
    "ready": False,
    "loading": False,
    "error": None,
}

# Inference queue
inference_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
shutdown_event = asyncio.Event()

# =============================================================================
# Pydantic Models
# =============================================================================

class InferenceRequest(BaseModel):
    """Request model for inference endpoint."""
    prompt: str = Field(..., description="Text prompt for CAD code generation")
    image_bytes: Optional[str] = Field(None, description="Base64-encoded image bytes")
    image_format: Optional[str] = Field(None, description="Image format (PNG, JPEG, etc.)")
    max_new_tokens: int = Field(default=MAX_NEW_TOKENS, ge=1, le=8192)
    temperature: float = Field(default=DEFAULT_TEMPERATURE, ge=0.0, le=2.0)


class InferenceResponse(BaseModel):
    """Response model for inference endpoint."""
    generated_text: str
    tokens_generated: int
    inference_time_ms: float


class HealthResponse(BaseModel):
    """Response model for health endpoint."""
    status: str
    model_loaded: bool
    gpu_available: bool
    gpu_memory_used_mb: Optional[float] = None


# =============================================================================
# Model Loading
# =============================================================================

def load_model():
    """Load the Qwen model and processor."""
    global model_state
    
    if model_state["loading"]:
        return
    
    model_state["loading"] = True
    model_state["error"] = None
    
    try:
        logger.info(f"Loading Qwen model from {BASE_MODEL}")
        logger.info(f"Checkpoint path: {CHECKPOINT_PATH}")
        
        # Import inference service functions
        from inference_service import initialize_model
        
        model, processor = initialize_model(
            checkpoint_path=CHECKPOINT_PATH if os.path.exists(CHECKPOINT_PATH) else None,
            base_model=BASE_MODEL,
        )
        
        model_state["model"] = model
        model_state["processor"] = processor
        model_state["ready"] = True
        MODEL_LOADED.set(1)
        
        logger.info("✓ Model loaded successfully")
        
        # Update GPU memory metric
        if torch.cuda.is_available():
            memory_used = torch.cuda.memory_allocated() / 1024**2
            GPU_MEMORY_USED.set(memory_used * 1024**2)
            logger.info(f"GPU memory used: {memory_used:.2f} MB")
            
    except Exception as e:
        model_state["error"] = str(e)
        model_state["ready"] = False
        MODEL_LOADED.set(0)
        logger.error(f"Failed to load model: {e}")
        raise
    finally:
        model_state["loading"] = False


# =============================================================================
# Inference
# =============================================================================

async def run_inference(request: InferenceRequest) -> InferenceResponse:
    """Run inference on a single request."""
    if not model_state["ready"]:
        raise HTTPException(status_code=503, detail="Model not ready")
    
    start_time = time.time()
    
    try:
from inference_service import generate_cad_code, generate_cad_code_stream
        
        # Decode image if provided
        pil_image = None
        if request.image_bytes:
            try:
                image_data = base64.b64decode(request.image_bytes)
                pil_image = Image.open(io.BytesIO(image_data)).convert("RGB")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid image data: {e}")
        
        # Run inference in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        generated_text = await loop.run_in_executor(
            None,
            lambda: generate_cad_code(
                prompt=request.prompt,
                image=pil_image,
                max_new_tokens=request.max_new_tokens,
                temperature=request.temperature,
            )
        )
        
        inference_time_ms = (time.time() - start_time) * 1000
        REQUEST_LATENCY.observe(inference_time_ms / 1000)
        REQUEST_COUNT.labels(status="success").inc()
        
        return InferenceResponse(
            generated_text=generated_text,
            tokens_generated=len(generated_text.split()),  # Approximate
            inference_time_ms=inference_time_ms,
        )
        
    except HTTPException:
        REQUEST_COUNT.labels(status="error").inc()
        raise
    except Exception as e:
        REQUEST_COUNT.labels(status="error").inc()
        logger.error(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# FastAPI Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Qwen inference server...")
    
    # Load model in background
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, load_model)
    
    # Setup signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda s, f: shutdown_event.set())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Qwen inference server...")
    shutdown_event.set()


app = FastAPI(
    title="Qwen CAD-Coder Inference Service",
    description="GPU-accelerated CAD code generation using fine-tuned Qwen3-VL",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Kubernetes liveness probe."""
    gpu_available = torch.cuda.is_available()
    gpu_memory_mb = None
    
    if gpu_available:
        gpu_memory_mb = torch.cuda.memory_allocated() / 1024**2
    
    return HealthResponse(
        status="healthy" if not model_state["error"] else "unhealthy",
        model_loaded=model_state["ready"],
        gpu_available=gpu_available,
        gpu_memory_used_mb=gpu_memory_mb,
    )


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes readiness probe."""
    if not model_state["ready"]:
        if model_state["loading"]:
            raise HTTPException(status_code=503, detail="Model is loading")
        elif model_state["error"]:
            raise HTTPException(status_code=503, detail=f"Model load error: {model_state['error']}")
        else:
            raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {"status": "ready"}


@app.post("/infer", response_model=InferenceResponse)
async def infer(request: InferenceRequest):
    """Run CAD code generation inference."""
    return await run_inference(request)


@app.post("/v1/generate", response_model=InferenceResponse)
async def generate(request: InferenceRequest):
    """Alternative endpoint for compatibility."""
    return await run_inference(request)


@app.post("/stream")
async def stream(request: InferenceRequest):
    """Stream CAD code tokens as they are generated."""
    if not model_state["ready"]:
        raise HTTPException(status_code=503, detail="Model not ready")

    try:
        # Decode image if provided
        pil_image = None
        if request.image_bytes:
            image_data = base64.b64decode(request.image_bytes)
            pil_image = Image.open(io.BytesIO(image_data)).convert("RGB")

        def token_generator():
            for chunk in generate_cad_code_stream(
                prompt=request.prompt,
                image=pil_image,
                max_new_tokens=request.max_new_tokens,
                temperature=request.temperature,
            ):
                yield chunk

        return StreamingResponse(token_generator(), media_type="text/plain")
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    # Update queue size metric
    QUEUE_SIZE.set(inference_queue.qsize())
    
    # Update GPU memory metric
    if torch.cuda.is_available():
        GPU_MEMORY_USED.set(torch.cuda.memory_allocated())
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Qwen CAD-Coder Inference",
        "model": BASE_MODEL,
        "status": "ready" if model_state["ready"] else "loading",
    }


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "gke_server:app",
        host="0.0.0.0",
        port=PORT,
        workers=1,  # Single worker for GPU model
        log_level="info",
    )
