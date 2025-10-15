# CAD Coder - Multimodal RAG Pipeline

Retrieval-Augmented Generation system for CAD code generation using text and image queries.

## System Architecture

```
GCS Bucket → Chunking → Multimodal Embeddings → Vector DB (Vertex AI) → RAG Retrieval → LLM Prompt
```

## Components

| File | Purpose |
|------|---------|
| `config.py` | Configuration and environment variables |
| `storage_utils.py` | GCS data loading (collection) |
| `processing_utils.py` | Text chunking (500 chars, 50 overlap) |
| `embedding_generator.py` | Multimodal embeddings with metadata |
| `vector_search.py` | Vertex AI index management |
| `clean_and_reindex.py` | Delete old vectors, upload new ones |
| `rag_retrieval.py` | Query interface (text, image, multimodal) |
| `test_rag.py` | Test suite |

## Setup

### 1. Authentication

**IMPORTANT**: The Docker setup uses your local `key.json` service account file.

```bash
# Ensure key.json is in RAG_new folder
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/key.json"

# Verify
echo $GOOGLE_APPLICATION_CREDENTIALS
```

### 2. Environment Variables

Create `.env` file:
```bash
PROJECT_ID=cad-coder-nextgen
GCS_DATA_URI=gs://cad-coder-bucket/rag-data
LOCATION=us-central1
```

### 3. Build Docker Image

```bash
cd RAG_new
docker build -t rag-pipeline .
```

## Usage

### Clean and Re-Index

Delete old vectors (without CAD code metadata) and upload new ones:

```bash
# Preview what will be deleted
docker-compose run --rm rag-pipeline python clean_and_reindex.py --mode info

# Delete old + upload new vectors (~5-10 min)
docker-compose run --rm rag-pipeline python clean_and_reindex.py --mode delete-and-reindex
```

### Run Tests

```bash
# Single text query
docker-compose run --rm rag-pipeline python test_rag.py single

# Multimodal query (text + image)
docker-compose run --rm rag-pipeline python test_rag.py multimodal

# All tests
docker-compose run --rm rag-pipeline python test_rag.py
```

### Query RAG System

**Text Query:**
```bash
docker-compose run --rm rag-pipeline python rag_retrieval.py \
  --mode text \
  --query "box with mounting holes" \
  --top-k 3 \
  --filter-type code
```

**Multimodal Query (Text + Image):**
```bash
docker-compose run --rm rag-pipeline python rag_retrieval.py \
  --mode multimodal \
  --query "cylindrical part with center hole" \
  --image "gs://cad-coder-bucket/rag-data/test_0.png" \
  --top-k 3
```

**Get Formatted Prompt:**
```bash
docker-compose run --rm rag-pipeline python rag_retrieval.py \
  --mode prompt \
  --query "mounting bracket" \
  --top-k 3
```

## Authentication in Docker

The docker-compose.yml mounts your local credentials:

```yaml
volumes:
  - ./key.json:/app/key.json:ro
environment:
  - GOOGLE_APPLICATION_CREDENTIALS=/app/key.json
```

**Requirements:**
- `key.json` must exist in RAG_new folder
- Service account must have:
  - `roles/aiplatform.user`
  - `roles/storage.objectViewer`

## Pipeline Flow

### 1. Data Collection
```python
# storage_utils.py
files = list_gcs_files("gs://cad-coder-bucket/rag-data")
# Returns: ["gs://.../file1.jsonl", "gs://.../image1.png", ...]
```

### 2. Chunking
```python
# processing_utils.py
chunks = chunk_code_text(code, chunk_size=500, overlap=50)
# Splits long CAD code into manageable chunks
```

### 3. Embedding Generation
```python
# embedding_generator.py
# For each code chunk:
datapoint = {
    "datapoint_id": "code_item123_c0",
    "feature_vector": [1408-dim embedding],
    "restricts": [
        {"namespace": "type", "allow_list": ["code"]},
        {"namespace": "cad_code", "allow_list": ["import cadquery..."]},
        {"namespace": "item_id", "allow_list": ["item123"]}
    ]
}
```

### 4. Vector Search
```python
# rag_retrieval.py
results = retriever.query_multimodal(
    text_query="box with holes",
    image_source="gs://.../test_0.png",
    top_k=3
)
# Returns: List[RetrievalResult] with CAD code
```

### 5. RAG Context Formatting
```python
context = retriever.get_rag_context(results)
prompt = build_llm_prompt(query, context)
# Ready to send to any LLM
```

## Sample Output

### Text Query
```bash
docker-compose run --rm rag-pipeline python test_rag.py single
```

**Output:**
```
================================================================================
TEST 1: Single Text Query
================================================================================

Query: 'Create a box with rounded corners'

Retrieved 3 results:

--- Result 1 ---
ID: code_test_36_c4
Distance: 0.3039
Type: code
Item ID: test_36
CAD Code Preview:
import cadquery as cq result = cq.Workplane("XY").box(50, 30, 10).edges().fillet(2)
...

RAG CONTEXT (formatted for LLM):

Here are relevant CAD code examples:

--- Example 1 (Distance: 0.3039) ---
Item ID: test_36

CAD Code:
```python
import cadquery as cq
result = cq.Workplane("XY").box(50, 30, 10).edges().fillet(2)
```
```

### Multimodal Query
```bash
docker-compose run --rm rag-pipeline python test_rag.py multimodal
```

**Output:**
```
================================================================================
TEST 4: Multimodal Query (Text + Image)
================================================================================

--------------------------------------------------------------------------------
Test Case 1: Test 0 - Box with holes
Text: 'box with holes'
Image: gs://cad-coder-bucket/rag-data/test_0.png
--------------------------------------------------------------------------------

Retrieved 3 results:

1. code_test_5_c4 (distance: 0.2845)
   Code: import cadquery as cq result = cq.Workplane("XY").rect(50, 30).extrude(5)...

2. code_test_12_c1 (distance: 0.2912)
   Code: import cadquery as cq result = (cq.Workplane("XY").box(40, 20, 8)...

3. code_test_23_c0 (distance: 0.3001)
   Code: import cadquery as cq result = cq.Workplane("front").rect(30, 20)...
```

## API Reference

### Query Modes

| Mode | Description | Input |
|------|-------------|-------|
| `text` | Text-only query | `--query "text"` |
| `image` | Image-only query | `--image "gs://..."` |
| `multimodal` | Text + Image | `--query "text" --image "gs://..."` |
| `prompt` | Get formatted LLM prompt | `--query "text"` |

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--top-k` | int | 5 | Number of results |
| `--filter-type` | str | None | Filter by "code" or "image" |
| `--output` | str | None | Save results to JSON file |

## Python API

```python
from rag_retrieval import MultimodalRAGRetriever, build_llm_prompt
from config import load_config

# Initialize
config = load_config()
retriever = MultimodalRAGRetriever(config["project_id"], config["location"])

# Query
results = retriever.query_multimodal(
    text_query="box with holes",
    image_source="gs://bucket/image.png",
    top_k=3,
    filter_type="code"
)

# Get CAD code
for r in results:
    print(f"Distance: {r.distance:.4f}")
    print(f"CAD Code:\n{r.cad_code}\n")

# Format for LLM
context = retriever.get_rag_context(results)
prompt = build_llm_prompt("Create a mounting bracket", context)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Authentication error | Verify `key.json` exists and `GOOGLE_APPLICATION_CREDENTIALS` is set |
| No CAD code in results | Run `clean_and_reindex.py --mode delete-and-reindex` |
| Image not found | Check GCS URI: `gsutil ls gs://cad-coder-bucket/rag-data/` |
| Docker network error | Ensure `network_mode: host` in docker-compose.yml |

## Performance

- **Chunking**: 500 chars/chunk, 50 char overlap
- **Embeddings**: 1408-dim multimodal vectors
- **Indexing**: ~5-10 min for 200 vectors
- **Query**: <1 sec for top-k retrieval
- **Distance**: <0.3 = excellent, 0.3-0.5 = good, >0.5 = poor match

