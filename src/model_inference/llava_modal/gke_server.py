#!/usr/bin/env python3
"""
LLaVA Inference Server for GKE Deployment

This module provides a FastAPI-based inference server for the CAD-Coder
LLaVA model, designed to run on GKE with A100 GPU support.

Features:
- Health and readiness endpoints for Kubernetes probes
- Automatic model download from HuggingFace
- Request timeout handling
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
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from transformers import TextIteratorStreamer
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

HF_MODEL_PATH = os.getenv("LLAVA_HF_MODEL", "CADCODER/CAD-Coder")
CONV_MODE = os.getenv("LLAVA_CONV_MODE", "vicuna_v1")
MAX_NEW_TOKENS = int(os.getenv("LLAVA_MODAL_MAX_NEW_TOKENS", "3450"))
DEFAULT_TEMPERATURE = float(os.getenv("LLAVA_MODAL_TEMPERATURE", "0.0"))
DEFAULT_TOP_P = float(os.getenv("LLAVA_MODAL_TOP_P", "1.0"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "300"))
PORT = int(os.getenv("PORT", "8080"))

# =============================================================================
# Prometheus Metrics
# =============================================================================

REQUEST_COUNT = Counter(
    "llava_inference_requests_total",
    "Total number of inference requests",
    ["status"]
)
REQUEST_LATENCY = Histogram(
    "llava_inference_latency_seconds",
    "Inference request latency in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)
MODEL_LOADED = Gauge(
    "llava_model_loaded",
    "Whether the model is loaded and ready"
)
GPU_MEMORY_USED = Gauge(
    "llava_gpu_memory_used_bytes",
    "GPU memory used in bytes"
)

# =============================================================================
# Global State
# =============================================================================

model_state = {
    "tokenizer": None,
    "model": None,
    "image_processor": None,
    "context_len": None,
    "ready": False,
    "loading": False,
    "error": None,
}

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
    top_p: float = Field(default=DEFAULT_TOP_P, ge=0.0, le=1.0)


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
    """Load the LLaVA model and processor."""
    global model_state
    
    if model_state["loading"]:
        return
    
    model_state["loading"] = True
    model_state["error"] = None
    
    try:
        logger.info(f"Loading LLaVA model from {HF_MODEL_PATH}")
        
        # Ensure cache directory exists
        os.makedirs(os.getenv("HF_HOME", "/models/hf_cache"), exist_ok=True)
        
        # Import LLaVA components
        from llava.model.builder import load_pretrained_model
        from llava.utils import disable_torch_init
        
        disable_torch_init()
        
        model_name = HF_MODEL_PATH.split("/")[-1]
        
        # Load model - will download on first run
        tokenizer, model, image_processor, context_len = load_pretrained_model(
            model_path=HF_MODEL_PATH,
            model_base=None,
            model_name=model_name,
            load_8bit=False,
            load_4bit=False,
        )
        
        model_state["tokenizer"] = tokenizer
        model_state["model"] = model
        model_state["image_processor"] = image_processor
        model_state["context_len"] = context_len
        model_state["ready"] = True
        MODEL_LOADED.set(1)
        
        logger.info("✓ LLaVA model loaded successfully")
        
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

def run_llava_inference(
    prompt: str,
    pil_image: Image.Image,
    max_new_tokens: int,
    temperature: float,
    top_p: float,
) -> str:
    """Run LLaVA inference synchronously."""
    from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN
    from llava.conversation import conv_templates
    from llava.mm_utils import tokenizer_image_token, process_images
    
    tokenizer = model_state["tokenizer"]
    model = model_state["model"]
    image_processor = model_state["image_processor"]
    
    # Process image
    image_tensor = process_images([pil_image], image_processor, model.config)[0]
    image_tensor = image_tensor.to(dtype=torch.float16, device="cuda")
    
    # Build conversation prompt
    conv = conv_templates[CONV_MODE].copy()
    
    # Prepend image token
    if model.config.mm_use_im_start_end:
        from llava.constants import DEFAULT_IM_START_TOKEN, DEFAULT_IM_END_TOKEN
        inp = DEFAULT_IM_START_TOKEN + DEFAULT_IMAGE_TOKEN + DEFAULT_IM_END_TOKEN + "\n" + prompt
    else:
        inp = DEFAULT_IMAGE_TOKEN + "\n" + prompt
    
    conv.append_message(conv.roles[0], inp)
    conv.append_message(conv.roles[1], None)
    full_prompt = conv.get_prompt()
    
    # Tokenize
    input_ids = tokenizer_image_token(
        full_prompt,
        tokenizer,
        IMAGE_TOKEN_INDEX,
        return_tensors="pt"
    ).unsqueeze(0).cuda()
    
    # Generate
    with torch.inference_mode():
        output_ids = model.generate(
            input_ids,
            images=image_tensor.unsqueeze(0),
            image_sizes=[pil_image.size],
            do_sample=True if temperature > 0 else False,
            temperature=temperature if temperature > 0 else None,
            top_p=top_p if temperature > 0 else None,
            max_new_tokens=max_new_tokens,
            use_cache=True,
        )
    
    # Decode output
    outputs = tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0].strip()
    
    return outputs


def stream_llava_inference(
    prompt: str,
    pil_image: Image.Image,
    max_new_tokens: int,
    temperature: float,
    top_p: float,
):
    """Stream tokens while generating."""
    from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN
    from llava.conversation import conv_templates
    from llava.mm_utils import tokenizer_image_token, process_images

    tokenizer = model_state["tokenizer"]
    model = model_state["model"]
    image_processor = model_state["image_processor"]

    image_tensor = process_images([pil_image], image_processor, model.config)[0]
    image_tensor = image_tensor.to(dtype=torch.float16, device="cuda")

    conv = conv_templates[CONV_MODE].copy()
    if model.config.mm_use_im_start_end:
        from llava.constants import DEFAULT_IM_START_TOKEN, DEFAULT_IM_END_TOKEN
        inp = DEFAULT_IM_START_TOKEN + DEFAULT_IMAGE_TOKEN + DEFAULT_IM_END_TOKEN + "\n" + prompt
    else:
        inp = DEFAULT_IMAGE_TOKEN + "\n" + prompt

    conv.append_message(conv.roles[0], inp)
    conv.append_message(conv.roles[1], None)
    prompt_text = conv.get_prompt()

    input_ids = tokenizer_image_token(
        prompt_text,
        tokenizer,
        IMAGE_TOKEN_INDEX,
        return_tensors="pt"
    ).unsqueeze(0).cuda()

    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

    generation_kwargs = {
        "inputs": input_ids,
        "images": [image_tensor],
        "max_new_tokens": max_new_tokens,
        "do_sample": temperature > 0,
        "temperature": temperature,
        "top_p": top_p,
        "use_cache": True,
        "streamer": streamer,
    }

    def _generate():
        with torch.inference_mode():
            model.generate(**generation_kwargs)

    thread = threading.Thread(target=_generate, daemon=True)
    thread.start()

    for text in streamer:
        yield text


async def run_inference(request: InferenceRequest) -> InferenceResponse:
    """Run inference on a single request."""
    if not model_state["ready"]:
        raise HTTPException(status_code=503, detail="Model not ready")
    
    start_time = time.time()
    
    try:
        # Decode image (required for LLaVA)
        if not request.image_bytes:
            # Create blank placeholder image if none provided
            pil_image = Image.new("RGB", (336, 336), color=(0, 0, 0))
        else:
            try:
                image_data = base64.b64decode(request.image_bytes)
                pil_image = Image.open(io.BytesIO(image_data)).convert("RGB")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid image data: {e}")
        
        # Run inference in thread pool
        loop = asyncio.get_event_loop()
        generated_text = await loop.run_in_executor(
            None,
            lambda: run_llava_inference(
                prompt=request.prompt,
                pil_image=pil_image,
                max_new_tokens=request.max_new_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
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
    logger.info("Starting LLaVA inference server...")
    
    # Load model in background
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, load_model)
    
    # Setup signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda s, f: shutdown_event.set())
    
    yield
    
    # Shutdown
    logger.info("Shutting down LLaVA inference server...")
    shutdown_event.set()


app = FastAPI(
    title="LLaVA CAD-Coder Inference Service",
    description="GPU-accelerated CAD code generation using CAD-Coder LLaVA",
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
    """Stream tokens from the LLaVA generator."""
    if not model_state["ready"]:
        raise HTTPException(status_code=503, detail="Model not ready")

    try:
        if not request.image_bytes:
            pil_image = Image.new("RGB", (336, 336), color=(0, 0, 0))
        else:
            image_data = base64.b64decode(request.image_bytes)
            pil_image = Image.open(io.BytesIO(image_data)).convert("RGB")

        def token_generator():
            for chunk in stream_llava_inference(
                prompt=request.prompt,
                pil_image=pil_image,
                max_new_tokens=request.max_new_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
            ):
                yield chunk

        return StreamingResponse(token_generator(), media_type="text/plain")
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
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
        "service": "LLaVA CAD-Coder Inference",
        "model": HF_MODEL_PATH,
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
