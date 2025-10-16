# Quick Start Guide

## Prerequisites

1. ✅ Docker installed
2. ✅ `key.json` service account file in `RAG_new/` folder
3. ✅ `.env` file configured

## Authentication Setup

Your terminal should already have:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="key.json"
```

Docker will mount this file into the container automatically.

## 1. Build

```bash
cd RAG_new
docker build -t rag-pipeline .
```

## 2. Test

```bash
# Single text query
docker-compose run --rm rag-pipeline python test_rag.py single

# Multimodal (text + image)
docker-compose run --rm rag-pipeline python test_rag.py multimodal

# All tests
docker-compose run --rm rag-pipeline python test_rag.py
```

## 3. Query

```bash
# Text only
docker-compose run --rm rag-pipeline python rag_retrieval.py \
  --mode text --query "box with holes" --top-k 3

# Text + Image
docker-compose run --rm rag-pipeline python rag_retrieval.py \
  --mode multimodal \
  --query "cylinder" \
  --image "gs://cad-coder-bucket/rag-data/test_0.png" \
  --top-k 3
```

## 4. Clean & Re-index (if needed)

```bash
docker-compose run --rm rag-pipeline python clean_and_reindex.py --mode delete-and-reindex
```

## Expected Output

```
Retrieved 3 results:

--- Result 1 ---
ID: code_test_36_c4
Distance: 0.3039
Type: code
CAD Code Preview:
import cadquery as cq
result = cq.Workplane("XY").box(50, 30, 10).edges().fillet(2)
```

Done! 🚀

