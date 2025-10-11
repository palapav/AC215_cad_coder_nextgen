"""
RAG indexing pipeline entry point.

It:
- Loads a JSONL manifest with fields: id, image_path, text, gt_code, split
- Encodes image and text (placeholders for now)
- Combines them into a joint embedding (weighted average)
- Upserts into a vector DB (Chroma or FAISS), storing gt_code and metadata
- Writes logs and performs a simple retrieval sanity check

Run:
  python -m src.datapipeline.preprocess_rag --config config.yaml
"""

import os
import json
import argparse
import jsonlines
import numpy as np
import yaml
from tqdm import tqdm

from src.models.model_rag import (
    load_cad_coder_model,
    encode_image,
    encode_text,
    combine_embeddings
)
from src.datapipeline.vector_store import (
    upsert_chroma,
    upsert_faiss,
    simple_retrieve_chroma,
    simple_retrieve_faiss
)


def load_manifest(path: str):
    items = []
    with jsonlines.open(path, mode="r") as reader:
        for obj in reader:
            # expected keys: id, image_path, text, gt_code, split
            if all(k in obj for k in ["id", "image_path", "text", "gt_code"]):
                items.append(obj)
    return items


def main(cfg_path: str):
    # Load config
    with open(cfg_path, "r") as f:
        cfg = yaml.safe_load(f)

    manifest_path = cfg["paths"]["manifest"]
    persist_dir = cfg["paths"]["persist_dir"]
    log_file = cfg["paths"]["log_file"]
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    db_type = cfg["database"]["type"]
    collection_name = cfg["database"]["collection_name"]

    dim = int(cfg["embeddings"]["dim"])
    w_img = float(cfg["embeddings"]["weight_image"])
    w_txt = float(cfg["embeddings"]["weight_text"])
    sanity_k = int(cfg["runtime"]["sanity_k"])
    sanity_query_text = cfg["runtime"]["sanity_query_text"]

    # Load manifest
    items = load_manifest(manifest_path)
    total = len(items)

    with open(log_file, "w") as lf:
        lf.write(f"[INFO] Loaded {total} items from {manifest_path}\n")

    # Load (placeholder) encoders
    model_handles = load_cad_coder_model()

    # Build batches and collect upserts
    ids, embeddings, metadatas, documents = [], [], [], []

    for obj in tqdm(items, desc="Indexing"):
        _id = str(obj["id"])
        image_path = obj["image_path"]
        text = str(obj["text"])
        gt_code = str(obj.get("gt_code", ""))

        img_emb = encode_image(image_path, dim, model_handles)
        txt_emb = encode_text(text, dim, model_handles)
        joint = combine_embeddings(img_emb, txt_emb, w_img, w_txt)

        ids.append(_id)
        embeddings.append(joint.tolist())
        metadatas.append({
            "id": _id,
            "image_path": image_path,
            "text": text[:256],     # store a snippet
            "split": obj.get("split", "unknown")
        })
        # store ground-truth CAD code in the document field (chroma) or metadata (faiss sidecar)
        documents.append(gt_code[:4000])

    # Upsert into vector DB
    os.makedirs(persist_dir, exist_ok=True)
    if db_type.lower() == "chroma":
        upsert_chroma(
            persist_dir=persist_dir,
            collection_name=collection_name,
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
    elif db_type.lower() == "faiss":
        upsert_faiss(
            persist_dir=persist_dir,
            collection_name=collection_name,
            ids=ids,
            embeddings=embeddings,
            metadatas=[{**m, "gt_code": d} for m, d in zip(metadatas, documents)]
        )
    else:
        raise ValueError(f"Unsupported database.type: {db_type}")

    with open(log_file, "a") as lf:
        lf.write(f"[INFO] Upserted {len(ids)} vectors into {db_type} at {persist_dir}\n")

    # Sanity check: retrieve using the text-only joint embedding
    txt_probe = encode_text(sanity_query_text, dim, model_handles)
    # combine with a zero image vector to reuse same combiner logic if desired
    zero_img = np.zeros(dim, dtype=np.float32)
    probe = combine_embeddings(zero_img, txt_probe, w_img=0.0, w_txt=1.0).tolist()

    if db_type.lower() == "chroma":
        results = simple_retrieve_chroma(persist_dir, collection_name, probe, k=sanity_k)
    else:
        results = simple_retrieve_faiss(persist_dir, collection_name, probe, k=sanity_k)

    with open(log_file, "a") as lf:
        lf.write(f"[INFO] Sanity query: \"{sanity_query_text}\" (top-{sanity_k})\n")
        for r in results:
            lf.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("[INFO] Pipeline finished successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="config.yaml")
    args = parser.parse_args()
    main(args.config)
