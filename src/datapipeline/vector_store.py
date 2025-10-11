"""
Vector database integration for RAG indexing.

Supports:
- Chroma persistent collection
- FAISS index (with a JSONL sidecar for metadata)

All comments are in English as requested.
"""

import os
import json
import jsonlines
from typing import List, Dict, Optional

import numpy as np

# Chroma
import chromadb
from chromadb.config import Settings

# FAISS
try:
    import faiss
except ImportError:
    faiss = None


# -----------------------------
# Chroma integration
# -----------------------------

def _get_chroma_collection(persist_dir: str, collection_name: str):
    os.makedirs(persist_dir, exist_ok=True)
    client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=persist_dir
    ))
    coll = client.get_or_create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})
    return client, coll


def upsert_chroma(
    persist_dir: str,
    collection_name: str,
    ids: List[str],
    embeddings: List[List[float]],
    metadatas: List[Dict],
    documents: Optional[List[str]] = None
):
    client, coll = _get_chroma_collection(persist_dir, collection_name)
    coll.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
    client.persist()


# -----------------------------
# FAISS integration
# -----------------------------

def _faiss_index_path(persist_dir: str, collection_name: str) -> str:
    return os.path.join(persist_dir, f"{collection_name}.faiss")

def _faiss_meta_path(persist_dir: str, collection_name: str) -> str:
    return os.path.join(persist_dir, f"{collection_name}.meta.jsonl")


def upsert_faiss(
    persist_dir: str,
    collection_name: str,
    ids: List[str],
    embeddings: List[List[float]],
    metadatas: List[Dict]
):
    assert faiss is not None, "faiss is not installed. Please install faiss-cpu."
    os.makedirs(persist_dir, exist_ok=True)

    emb = np.array(embeddings, dtype=np.float32)
    dim = emb.shape[1]

    index_path = _faiss_index_path(persist_dir, collection_name)
    meta_path = _faiss_meta_path(persist_dir, collection_name)

    # Use cosine similarity via Inner Product on normalized vectors
    # Ensure vectors are normalized
    norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12
    emb = emb / norms

    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
        # Concatenate to existing index by re-building (simple approach)
        existing_ntotal = index.ntotal
        # Recreate an IndexFlatIP and add both old and new is complex without raw embeddings cached.
        # For simplicity, if index exists, we create a new one and append metadata. In production, keep all embeddings cached.
        # Here we just add new vectors if index is IndexFlatIP.
        try:
            index.add(emb)
        except Exception:
            # Rebuild strategy could be implemented here if needed.
            raise RuntimeError("Existing FAISS index type mismatch; consider rebuilding.")
    else:
        index = faiss.IndexFlatIP(dim)
        index.add(emb)

    faiss.write_index(index, index_path)

    # Append metadata sidecar
    with jsonlines.open(meta_path, mode="a") as writer:
        for _id, md in zip(ids, metadatas):
            writer.write({"id": _id, "metadata": md})


# -----------------------------
# Simple retrieval sanity-check
# -----------------------------

def simple_retrieve_chroma(
    persist_dir: str,
    collection_name: str,
    query_embedding: List[float],
    k: int = 3
) -> List[Dict]:
    _, coll = _get_chroma_collection(persist_dir, collection_name)
    res = coll.query(query_embeddings=[query_embedding], n_results=k)
    out = []
    for i in range(len(res["ids"][0])):
        out.append({
            "id": res["ids"][0][i],
            "distance": float(res["distances"][0][i]) if "distances" in res else None,
            "metadata": res["metadatas"][0][i],
            "document": res["documents"][0][i] if "documents" in res and res["documents"] else None
        })
    return out


def simple_retrieve_faiss(
    persist_dir: str,
    collection_name: str,
    query_embedding: List[float],
    k: int = 3
) -> List[Dict]:
    assert faiss is not None, "faiss is not installed. Please install faiss-cpu."
    index_path = _faiss_index_path(persist_dir, collection_name)
    meta_path = _faiss_meta_path(persist_dir, collection_name)

    if not os.path.exists(index_path) or not os.path.exists(meta_path):
        return []

    index = faiss.read_index(index_path)
    q = np.array(query_embedding, dtype=np.float32)
    q = q / (np.linalg.norm(q) + 1e-12)
    D, I = index.search(q.reshape(1, -1), k)

    # Load metadata sidecar
    metas = []
    with jsonlines.open(meta_path, mode="r") as reader:
        for line in reader:
            metas.append(line)

    out = []
    for rank, idx in enumerate(I[0].tolist()):
        if idx < 0 or idx >= len(metas):
            continue
        out.append({
            "rank": rank,
            "score": float(D[0][rank]),
            "id": metas[idx]["id"],
            "metadata": metas[idx]["metadata"]
        })
    return out
