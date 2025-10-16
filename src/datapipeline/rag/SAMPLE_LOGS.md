# Sample Pipeline Logs

## 1. Clean and Re-Index Pipeline

```bash
$ docker-compose run --rm rag-pipeline python clean_and_reindex.py --mode delete-and-reindex
```

**Output:**
```
================================================================================
Clean and Re-Index Script
================================================================================
2025-10-15 16:30:12,345 - INFO - Found index: cadcoder-mm-index
2025-10-15 16:30:12,345 - INFO - Resource: projects/604447465953/locations/us-central1/indexes/2526503997792059392

Scanning GCS bucket: gs://cad-coder-bucket/rag-data
2025-10-15 16:30:12,799 - INFO - Found 52 supported files in gs://cad-coder-bucket/rag-data

Generating datapoint IDs from GCS data...
2025-10-15 16:30:13,123 - INFO - Found 200 expected datapoint IDs

================================================================================
STEP 1: DELETING OLD VECTORS
================================================================================
Will attempt to delete 200 datapoint(s)

Proceed with deletion? (yes/no): yes

Deleting 200 datapoints from index...
2025-10-15 16:30:15,456 - INFO - Deleting batch 1 (100 datapoints)...
2025-10-15 16:30:16,123 - INFO -   ✅ Batch 1 deleted
2025-10-15 16:30:16,456 - INFO - Deleting batch 2 (100 datapoints)...
2025-10-15 16:30:17,123 - INFO -   ✅ Batch 2 deleted

✅ Deletion complete!
Old vectors (without CAD code metadata) have been removed

================================================================================
STEP 2: RE-INDEXING WITH NEW METADATA
================================================================================
Generating new embeddings with CAD code in metadata...
2025-10-15 16:30:17,456 - INFO - --- GENERATING MULTIMODAL EMBEDDINGS ---
2025-10-15 16:30:47,234 - INFO - ✅ Embedded text chunk 1/200
2025-10-15 16:30:47,567 - INFO - ✅ Embedded text chunk 2/200
...
2025-10-15 16:35:12,890 - INFO - ✅ Embedded text chunk 200/200

2025-10-15 16:35:12,890 - INFO - Generated 200 datapoints with updated metadata
2025-10-15 16:35:12,890 - INFO -   - 150 datapoints have CAD code in metadata ✅

Upserting new datapoints to index...
2025-10-15 16:35:13,123 - INFO - Upserting batch 1 (100 datapoints)...
2025-10-15 16:35:14,456 - INFO -   ✅ Batch 1 upserted
2025-10-15 16:35:14,789 - INFO - Upserting batch 2 (100 datapoints)...
2025-10-15 16:35:16,123 - INFO -   ✅ Batch 2 upserted

✅ Re-indexing complete!

================================================================================
✅ SUCCESS!
================================================================================
All vectors updated with CAD code metadata!

You can now test RAG retrieval:
  python test_rag.py metadata
  python demo.py
  python rag_retrieval.py --mode text --query 'your query'
================================================================================
```

**Time**: ~5-10 minutes

---

## 2. Single Text Query Test

```bash
$ docker-compose run --rm rag-pipeline python test_rag.py single
```

**Output:**
```
/Users/aditya/.../site-packages/vertexai/_model_garden/_model_garden_models.py:278: UserWarning: This feature is deprecated...
  warning_logs.show_deprecation_warning()

================================================================================
TEST 1: Single Text Query
================================================================================

Query: 'Create a box with rounded corners'

2025-10-15 16:43:58,123 - INFO - Multimodal embedding model initialized
2025-10-15 16:43:58,456 - INFO - RAG Retriever initialized with index: cadcoder-mm-index
2025-10-15 16:43:58,789 - INFO - Querying with text: 'Create a box with rounded corners...'
2025-10-15 16:43:59,575 - INFO - Retrieved 3 results
Retrieved 3 results:

--- Result 1 ---
ID: code_test_36_c4
Distance: 0.3039
Type: code
Item ID: test_36
CAD Code Preview:
import cadquery as cq result = cq.Workplane("XY").box(50, 30, 10).edges().fillet(2)
...

--- Result 2 ---
ID: code_test_12_c4
Distance: 0.3040
Type: code
Item ID: test_12
CAD Code Preview:
import cadquery as cq result = ( cq.Workplane("XY") .box(40, 20, 8) .edges("|Z")...

--- Result 3 ---
ID: code_test_5_c4
Distance: 0.3048
Type: code
Item ID: test_5
CAD Code Preview:
import cadquery as cq result = cq.Workplane("front").rect(30, 20).extrude(10).ed...


--------------------------------------------------------------------------------
RAG CONTEXT (formatted for LLM):
--------------------------------------------------------------------------------

Here are relevant CAD code examples:


--- Example 1 (Distance: 0.3039) ---
Item ID: test_36

CAD Code:
```python
import cadquery as cq
result = cq.Workplane("XY").box(50, 30, 10).edges().fillet(2)
```


--- Example 2 (Distance: 0.3040) ---
Item ID: test_12

CAD Code:
```python
import cadquery as cq
result = (
    cq.Workplane("XY")
    .box(40, 20, 8)
    .edges("|Z")
    .fillet(1.5)
)
```


--- Example 3 (Distance: 0.3048) ---
Item ID: test_5

CAD Code:
```python
import cadquery as cq
result = cq.Workplane("front").rect(30, 20).extrude(10).edges().fillet(1)
```
```

**Time**: ~2-3 seconds

---

## 3. Multimodal Query Test

```bash
$ docker-compose run --rm rag-pipeline python test_rag.py multimodal
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

2025-10-15 16:45:12,123 - INFO - Querying with text: 'box with holes' and image: gs://cad-coder-bucket/rag-data/test_0.png
2025-10-15 16:45:13,456 - INFO - Retrieved 3 results

Retrieved 3 results:

1. code_test_5_c4 (distance: 0.2845)
   Code: import cadquery as cq result = cq.Workplane("XY").rect(50, 30).extrude(5)...

2. code_test_12_c1 (distance: 0.2912)
   Code: import cadquery as cq result = (cq.Workplane("XY").box(40, 20, 8)...

3. code_test_23_c0 (distance: 0.3001)
   Code: import cadquery as cq result = cq.Workplane("front").rect(30, 20)...

--------------------------------------------------------------------------------
Sample RAG Context (for first test case):
--------------------------------------------------------------------------------

Here are relevant CAD code examples:

--- Example 1 (Distance: 0.2845) ---
Item ID: test_5

CAD Code:
```python
import cadquery as cq
result = cq.Workplane("XY").rect(50, 30).extrude(5).faces(">Z").workplane().pushPoints([(15, 10), (-15, -10)]).circle(2).cutThruAll()
```

--- Example 2 (Distance: 0.2912) ---
Item ID: test_12

CAD Code:
```python
import cadquery as cq
result = (
    cq.Workplane("XY")
    .box(40, 20, 8)
    .faces(">Z")
    .workplane()
    .rect(30, 15)
    .cutBlind(3)
)
```

--------------------------------------------------------------------------------
Test Case 2: Test 1 - Cylindrical part
Text: 'cylindrical part'
Image: gs://cad-coder-bucket/rag-data/test_1.png
--------------------------------------------------------------------------------

Retrieved 3 results:

1. code_test_18_c0 (distance: 0.2634)
   Code: import cadquery as cq result = cq.Workplane("XY").circle(10).extrude(20)...

2. code_test_31_c2 (distance: 0.2789)
   Code: import cadquery as cq result = (cq.Workplane("XY").circle(8).extrude...

3. code_test_9_c1 (distance: 0.2845)
   Code: import cadquery as cq result = cq.Workplane("front").circle(12).extru...

--------------------------------------------------------------------------------
Test Case 3: Test 2 - Mechanical component
Text: 'mechanical component'
Image: gs://cad-coder-bucket/rag-data/test_2.png
--------------------------------------------------------------------------------

Retrieved 3 results:

1. code_test_42_c0 (distance: 0.3123)
   Code: import cadquery as cq result = cq.Workplane("XY").rect(60, 40).extrud...

2. code_test_27_c3 (distance: 0.3245)
   Code: import cadquery as cq result = (cq.Workplane("XY").box(50, 50, 10)...

3. code_test_15_c2 (distance: 0.3301)
   Code: import cadquery as cq result = cq.Workplane("front").box(45, 30, 12)...
```

**Time**: ~5-6 seconds (3 queries)

---

## 4. Command-Line Query

```bash
$ docker-compose run --rm rag-pipeline python rag_retrieval.py \
    --mode multimodal \
    --query "mounting bracket" \
    --image "gs://cad-coder-bucket/rag-data/test_0.png" \
    --top-k 3
```

**Output:**
```
2025-10-15 16:50:12,123 - INFO - Multimodal embedding model initialized
2025-10-15 16:50:12,456 - INFO - RAG Retriever initialized with index: cadcoder-mm-index

================================================================================
MULTIMODAL QUERY (Text + Image)
Text: mounting bracket
Image: gs://cad-coder-bucket/rag-data/test_0.png
================================================================================

2025-10-15 16:50:12,789 - INFO - Querying with text: 'mounting bracket' and image: gs://cad-coder-bucket/rag-data/test_0.png
2025-10-15 16:50:13,234 - INFO - Retrieved 3 results

--- Result 1 ---
ID: code_test_8_c2
Distance: 0.2756
Type: code
Item ID: test_8
Paired Image: gs://cad-coder-bucket/rag-data/test_8.png

CAD Code Preview:
import cadquery as cq
result = (
    cq.Workplane("XY")
    .rect(60, 40)
    .extrude(8)
    .faces(">Z")
    .workplane()
    .pushPoints([(20, 15), (-20, -15)])
    .circle(3)
    .cutThruAll()
    .faces(">Z")
    .workplane()
    .rect(50, 30)
    .cutBlind(4)
)

--- Result 2 ---
ID: code_test_21_c0
Distance: 0.2834
Type: code
Item ID: test_21

CAD Code Preview:
import cadquery as cq
result = cq.Workplane("XY").box(50, 30, 6).faces(">Z").workplane().rect(40, 20).cutBlind(3)

--- Result 3 ---
ID: code_test_33_c1
Distance: 0.2901
Type: code
Item ID: test_33

CAD Code Preview:
import cadquery as cq
result = (
    cq.Workplane("front")
    .rect(55, 35)
    .extrude(7)
    .edges("|Z")
    .fillet(2)
)

================================================================================
RAG CONTEXT FOR LLM:
================================================================================

Here are relevant CAD code examples:

--- Example 1 (Distance: 0.2756) ---
Item ID: test_8
Associated Image: gs://cad-coder-bucket/rag-data/test_8.png

CAD Code:
```python
import cadquery as cq
result = (
    cq.Workplane("XY")
    .rect(60, 40)
    .extrude(8)
    .faces(">Z")
    .workplane()
    .pushPoints([(20, 15), (-20, -15)])
    .circle(3)
    .cutThruAll()
    .faces(">Z")
    .workplane()
    .rect(50, 30)
    .cutBlind(4)
)
```

--- Example 2 (Distance: 0.2834) ---
Item ID: test_21

CAD Code:
```python
import cadquery as cq
result = cq.Workplane("XY").box(50, 30, 6).faces(">Z").workplane().rect(40, 20).cutBlind(3)
```

--- Example 3 (Distance: 0.2901) ---
Item ID: test_33

CAD Code:
```python
import cadquery as cq
result = (
    cq.Workplane("front")
    .rect(55, 35)
    .extrude(7)
    .edges("|Z")
    .fillet(2)
)
```

================================================================================
COMPLETE PROMPT (Ready for LLM):
================================================================================

You are an expert CAD programmer using CadQuery/Python.

Given the following user request and relevant code examples, generate CAD code that fulfills the request.

User Request: mounting bracket

Here are relevant CAD code examples:

--- Example 1 (Distance: 0.2756) ---
Item ID: test_8
Associated Image: gs://cad-coder-bucket/rag-data/test_8.png

CAD Code:
```python
import cadquery as cq
result = (
    cq.Workplane("XY")
    .rect(60, 40)
    .extrude(8)
    .faces(">Z")
    .workplane()
    .pushPoints([(20, 15), (-20, -15)])
    .circle(3)
    .cutThruAll()
    .faces(">Z")
    .workplane()
    .rect(50, 30)
    .cutBlind(4)
)
```

[... examples 2 and 3 ...]

Instructions:
1. Study the provided examples to understand the coding patterns
2. Generate complete, working CadQuery code
3. Include imports and proper syntax
4. Add comments explaining key steps
5. Ensure the code is similar in style to the examples

Generated CAD Code:

================================================================================
📝 This prompt is ready to send to any LLM of your choice!
   (But we're NOT calling an LLM in this demo)
================================================================================
```

**Time**: ~2 seconds

---

## Performance Summary

| Operation | Time | Notes |
|-----------|------|-------|
| Delete 200 vectors | ~2s | Batch operation |
| Generate 200 embeddings | ~5min | Rate limited by API |
| Upsert 200 vectors | ~3s | Batch upload |
| Single query | ~1-2s | Embedding + search |
| Multimodal query | ~2-3s | Slightly slower (image loading) |
| Batch 3 queries | ~5-6s | Sequential processing |

## Distance Interpretation

- **< 0.3**: Excellent match (highly relevant)
- **0.3 - 0.4**: Good match (relevant)
- **0.4 - 0.5**: Fair match (somewhat relevant)
- **> 0.5**: Poor match (not very relevant)

