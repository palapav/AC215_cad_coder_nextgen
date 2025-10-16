# RAG Pipeline Design

## Overview

Multimodal Retrieval-Augmented Generation pipeline for CAD code generation using Vertex AI.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Data Collection                              │
│  storage_utils.py: list_gcs_files("gs://bucket/rag-data")          │
│  → Returns: JSONL files (CAD code) + PNG files (images)            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           Chunking                                   │
│  processing_utils.py: chunk_code_text(code, 500, 50)               │
│  → Splits long code into 500-char chunks with 50-char overlap      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Embedding Generation                              │
│  embedding_generator.py: MultiModalEmbeddingModel                   │
│  → Text embeddings: 1408-dim vectors                                │
│  → Image embeddings: 1408-dim vectors                               │
│  → Metadata: CAD code stored in "restricts"                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Vector Database                                 │
│  vector_search.py: Vertex AI Matching Engine                        │
│  → Index type: Tree-AH                                              │
│  → Distance metric: DOT_PRODUCT_DISTANCE                            │
│  → Update method: STREAM_UPDATE (real-time)                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       RAG Retrieval                                  │
│  rag_retrieval.py: Query interface                                  │
│  → Text query: embed text → find neighbors                          │
│  → Image query: embed image → find neighbors                        │
│  → Multimodal: embed(text + image) → find neighbors                │
│  → Returns: Top-K results with CAD code + distances                 │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Context Formatting                                │
│  build_llm_prompt(): Format retrieved examples                      │
│  → System instructions                                               │
│  → Retrieved CAD code examples                                       │
│  → User query                                                        │
│  → Output: Ready-to-use LLM prompt                                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Indexing Phase (One-time Setup)

```python
# Input: GCS bucket with JSONL + PNG files
files = list_gcs_files("gs://cad-coder-bucket/rag-data")

# Process each JSONL file
for jsonl_file in jsonl_files:
    for line in jsonl_file:
        obj = json.loads(line)
        code = obj["code"]
        item_id = obj["id"]
        
        # Chunk code
        chunks = chunk_code_text(code, 500, 50)
        
        # Generate embeddings + store metadata
        for i, chunk in enumerate(chunks):
            embedding = model.get_embeddings(contextual_text=chunk)
            
            datapoint = {
                "datapoint_id": f"code_{item_id}_c{i}",
                "feature_vector": embedding.text_embedding,  # 1408-dim
                "restricts": [
                    {"namespace": "type", "allow_list": ["code"]},
                    {"namespace": "cad_code", "allow_list": [chunk]},  # ACTUAL CODE
                    {"namespace": "item_id", "allow_list": [item_id]},
                    {"namespace": "chunk_index", "allow_list": [str(i)]},
                    {"namespace": "total_chunks", "allow_list": [str(len(chunks))]}
                ]
            }
            
            # Upload to vector DB
            index.upsert_datapoints([datapoint])

# Process images
for image_file in image_files:
    embedding = model.get_embeddings(image=load_image(image_file))
    
    datapoint = {
        "datapoint_id": f"img_{idx}",
        "feature_vector": embedding.image_embedding,
        "restricts": [
            {"namespace": "type", "allow_list": ["image"]},
            {"namespace": "uri", "allow_list": [image_file]}
        ]
    }
    
    index.upsert_datapoints([datapoint])
```

### 2. Query Phase (Runtime)

```python
# User query
text_query = "box with mounting holes"
image_query = "gs://bucket/reference.png"

# Generate query embedding (multimodal)
image = load_image(image_query)
query_embedding = model.get_embeddings(
    image=image,
    contextual_text=text_query
).image_embedding  # 1408-dim

# Search vector DB
request = FindNeighborsRequest(
    index_endpoint=endpoint.resource_name,
    deployed_index_id="cadcoder_mm_deployed",
    queries=[{
        "datapoint": {
            "feature_vector": query_embedding,
            "restricts": [{"namespace": "type", "allow_list": ["code"]}]
        },
        "neighbor_count": 3
    }],
    return_full_datapoint=True
)

response = client.find_neighbors(request)

# Extract results
for neighbor in response.nearest_neighbors[0].neighbors:
    result = {
        "id": neighbor.datapoint.datapoint_id,
        "distance": neighbor.distance,
        "cad_code": extract_from_restricts(neighbor, "cad_code"),
        "item_id": extract_from_restricts(neighbor, "item_id")
    }
    
    results.append(result)

# Sort by distance (ascending)
results.sort(key=lambda x: x.distance)
```

### 3. Context Formatting

```python
# Format retrieved examples
context = f"""Here are relevant CAD code examples:

--- Example 1 (Distance: {results[0].distance:.4f}) ---
Item ID: {results[0].item_id}

CAD Code:
```python
{results[0].cad_code}
```

--- Example 2 (Distance: {results[1].distance:.4f}) ---
...
"""

# Build complete prompt
prompt = f"""You are an expert CAD programmer using CadQuery/Python.

Given the following user request and relevant code examples, generate CAD code.

User Request: {text_query}

{context}

Instructions:
1. Study the provided examples
2. Generate complete, working CadQuery code
3. Include imports and proper syntax

Generated CAD Code:
"""

# Ready to send to LLM
```

## Key Design Decisions

### 1. Chunking Strategy
- **Size**: 500 characters per chunk
- **Overlap**: 50 characters
- **Reason**: Balances context preservation with manageable embedding size

### 2. Metadata Storage
- **Location**: Stored in vector DB "restricts" field
- **Content**: Full CAD code text stored alongside embedding
- **Benefit**: No need for separate database lookup

### 3. Multimodal Embeddings
- **Model**: `multimodalembedding` (Vertex AI)
- **Dimension**: 1408
- **Usage**: Single embedding space for text + images
- **Query**: Contextual text influences image embedding

### 4. Distance Metric
- **Type**: DOT_PRODUCT_DISTANCE
- **Interpretation**: Lower = more similar
- **Threshold**: <0.3 excellent, 0.3-0.5 good, >0.5 poor

### 5. Index Configuration
- **Type**: Tree-AH (fast approximate search)
- **Update**: STREAM_UPDATE (real-time additions)
- **Neighbors**: 150 approximate neighbors
- **Search**: 7% leaf nodes searched

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Chunk 1KB code | <1ms | In-memory operation |
| Generate embedding | ~400ms | API call to Vertex AI |
| Upsert 1 vector | ~500ms | Network + DB write |
| Index 200 vectors | ~5-10min | Batch upload |
| Query (top-5) | <1sec | Vector search |
| Build prompt | <10ms | String formatting |

## Scalability

- **Current**: 200 vectors (52 files)
- **Tested**: Up to 10K vectors
- **Limit**: Vertex AI supports millions of vectors
- **Bottleneck**: Embedding generation (rate limited by API)

## API Endpoints Used

| Service | Endpoint | Purpose |
|---------|----------|---------|
| Vertex AI Embeddings | `multimodalembedding` | Generate 1408-dim vectors |
| Vertex AI Match Service | `MatchServiceClient` | Vector similarity search |
| GCS | `storage.googleapis.com` | Data storage |

## Security

- **Authentication**: Service account key (`key.json`)
- **Permissions Required**:
  - `aiplatform.indexes.update` (upsert vectors)
  - `aiplatform.indexes.get` (query)
  - `storage.objects.get` (read GCS)
- **Network**: Private or public endpoint (configurable)

## Error Handling

| Error | Handling |
|-------|----------|
| Missing CAD code | Logged, skipped |
| Embedding failure | Retry with backoff (3 attempts) |
| API rate limit | Exponential backoff |
| Malformed JSONL | Log warning, continue |
| Authentication | Fail fast with clear error |

