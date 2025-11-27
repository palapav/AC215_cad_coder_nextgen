"""Production RAG helper that reuses the src/datapipeline/rag retrieval stack."""
from __future__ import annotations

import base64
import logging
import os
import random
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional, Tuple, Union

from dotenv import load_dotenv

from app.services.db_service import get_all_prompts

load_dotenv()

try:
    from PIL import Image
except ImportError:  # pragma: no cover - Pillow always installed
    Image = None

logger = logging.getLogger(__name__)

CURRENT_FILE = Path(__file__).resolve()
APP_DIR = CURRENT_FILE.parents[1]  # /app/app
PROJECT_ROOT = APP_DIR.parent      # /app


def _find_rag_dir() -> Optional[Path]:
    """Locate the rag folder (mounted in Docker or in local repo)."""
    candidates = []
    env_dir = os.getenv("RAG_DIR")
    if env_dir:
        candidates.append(Path(env_dir))
    candidates.extend(
        [
            PROJECT_ROOT / "rag",
            PROJECT_ROOT / "datapipeline" / "rag",
            PROJECT_ROOT.parent / "datapipeline" / "rag",
            CURRENT_FILE.parents[3] / "src" / "datapipeline" / "rag",
        ]
    )
    for path in candidates:
        if path and path.exists():
            return path
    return None


RAG_DIR = _find_rag_dir()
if RAG_DIR and str(RAG_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_DIR))

ENABLE_RAG = os.getenv("ENABLE_RAG", "true").lower() == "true"

try:
    from rag_retrieval import MultimodalRAGRetriever  # type: ignore
except Exception as exc:  # pragma: no cover - optional dependency
    MultimodalRAGRetriever = None  # type: ignore
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

_retriever: Optional["MultimodalRAGRetriever"] = None


def _ensure_google_credentials() -> str:
    """Ensure GOOGLE_APPLICATION_CREDENTIALS points to the service account key."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and Path(creds_path).exists():
        return creds_path
    if RAG_DIR:
        fallback = RAG_DIR / "key.json"
        if fallback.exists():
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(fallback)
            return str(fallback)
    raise RuntimeError(
        "GOOGLE_APPLICATION_CREDENTIALS not set and key.json not found in RAG_DIR."
    )


def _get_retriever() -> Optional["MultimodalRAGRetriever"]:
    global _retriever
    if not ENABLE_RAG:
        return None
    if MultimodalRAGRetriever is None:
        logger.warning("RAG disabled: unable to import rag_retrieval (%s)", _IMPORT_ERROR)
        return None
    if RAG_DIR is None:
        logger.warning("RAG disabled: rag directory not found")
        return None
    if _retriever is None:
        creds = _ensure_google_credentials()
        logger.info("Initializing RAG retriever (creds: %s)", creds)
        project_id = os.getenv("RAG_PROJECT_ID", os.getenv("PROJECT_ID", "cad-coder-nextgen"))
        location = os.getenv("RAG_LOCATION", os.getenv("LOCATION", "us-central1"))
        _retriever = MultimodalRAGRetriever(project_id=project_id, location=location)
    return _retriever


def _write_temp_image_from_pil(image: "Image.Image") -> Tuple[str, callable]:
    temp = NamedTemporaryFile(delete=False, suffix=".png")
    image.save(temp.name, format="PNG")
    temp.close()
    def cleanup() -> None:
        try:
            Path(temp.name).unlink(missing_ok=True)
        except OSError:
            pass
    return temp.name, cleanup


def _write_temp_image_from_base64(data_url: str) -> Tuple[str, callable]:
    header, encoded = data_url.split(",", 1)
    suffix = ".png" if "png" in header else ".jpg"
    temp = NamedTemporaryFile(delete=False, suffix=suffix)
    temp.write(base64.b64decode(encoded))
    temp.close()
    def cleanup() -> None:
        try:
            Path(temp.name).unlink(missing_ok=True)
        except OSError:
            pass
    return temp.name, cleanup


def _prepare_image_source(
    image_obj: Optional["Image.Image"],
    image_reference: Optional[str],
) -> Tuple[Optional[str], Optional[callable]]:
    """Return a path-like image source and cleanup callback."""
    if image_obj is not None and Image is not None:
        return _write_temp_image_from_pil(image_obj)
    if image_reference:
        if image_reference.startswith("data:image"):
            return _write_temp_image_from_base64(image_reference)
        path = Path(image_reference)
        if path.exists():
            return str(path), None
        # Could be a GCS URI or remote path
        return image_reference, None
    return None, None


def retrieve_context(
    prompt: str,
    image: Optional["Image.Image"] = None,
    image_reference: Optional[str] = None,
    top_k: int = 3,
) -> dict:
    """
    Retrieve relevant CAD code context for the given prompt/image.

    Returns a dictionary:
        {
            "context": str,
            "results": [ ... ],
            "used": bool
        }
    """
    retriever = _get_retriever()
    if retriever is None:
        return {"context": "", "results": [], "used": False}

    image_source, cleanup = _prepare_image_source(image, image_reference)
    try:
        if image_source:
            results = retriever.query_multimodal(prompt, image_source, top_k=top_k)
        else:
            results = retriever.query_text(prompt, top_k=top_k)
        context = retriever.get_rag_context(results)
        return {
            "context": context or "",
            "results": [r.to_dict() for r in results],
            "used": bool(results),
        }
    except Exception as exc:
        logger.warning("RAG retrieval failed: %s", exc)
        return {"context": "", "results": [], "used": False}
    finally:
        if cleanup:
            cleanup()


def retrieve_similar_context(prompt: str, *, top_k: int = 3) -> list[dict]:
    """Legacy API used by /history/context for quick suggestions."""
    rag_payload = retrieve_context(prompt=prompt, top_k=top_k)
    if rag_payload.get("used"):
        return rag_payload.get("results", [])

    # Fallback: sample prompts from DB so UI still shows something
    all_prompts = get_all_prompts()
    if not all_prompts:
        return [{"text": "No context available"}]
    sample = random.sample(all_prompts, min(top_k, len(all_prompts)))
    return [{"text": item.get("prompt") or item} for item in sample]
