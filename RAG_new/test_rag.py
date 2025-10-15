"""
Simple test script to demonstrate RAG retrieval capabilities.
Run this after pipeline.py has successfully indexed your data.
"""

import logging
from rag_retrieval import MultimodalRAGRetriever, build_llm_prompt
from config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def test_single_text_query():
    """Test a single text query."""
    print("\n" + "="*80)
    print("TEST 1: Single Text Query")
    print("="*80 + "\n")
    
    config = load_config()
    retriever = MultimodalRAGRetriever(config["project_id"], config["location"])
    
    # Example query
    query = "Create a box with rounded corners"
    
    print(f"Query: '{query}'\n")
    
    # Retrieve top 3 code examples
    results = retriever.query_text(query, top_k=3, filter_type="code")
    
    print(f"Retrieved {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        print(f"--- Result {i} ---")
        print(f"ID: {result.datapoint_id}")
        print(f"Distance: {result.distance:.4f}")
        print(f"Type: {result.type}")
        if result.item_id:
            print(f"Item ID: {result.item_id}")
        if result.cad_code:
            # Show first 200 characters
            preview = result.cad_code[:200] + "..." if len(result.cad_code) > 200 else result.cad_code
            print(f"CAD Code Preview:\n{preview}")
        print()
    
    # Show formatted context for LLM
    print("\n" + "-"*80)
    print("RAG CONTEXT (formatted for LLM):")
    print("-"*80 + "\n")
    
    context = retriever.get_rag_context(results, max_code_length=500)
    print(context)


def test_batch_queries():
    """Test batch text queries."""
    print("\n" + "="*80)
    print("TEST 2: Batch Text Queries")
    print("="*80 + "\n")
    
    config = load_config()
    retriever = MultimodalRAGRetriever(config["project_id"], config["location"])
    
    # Multiple queries
    queries = [
        "cylinder with a hole",
        "rectangular plate with holes",
        "simple box shape"
    ]
    
    print(f"Processing {len(queries)} queries:\n")
    
    all_results = retriever.batch_query_text(queries, top_k=2)
    
    for i, (query, results) in enumerate(zip(queries, all_results), 1):
        print(f"\n--- Query {i}: '{query}' ---")
        print(f"Top {len(results)} results:")
        
        for j, result in enumerate(results, 1):
            print(f"  {j}. {result.datapoint_id} (distance: {result.distance:.4f})")
            if result.item_id:
                print(f"     Item: {result.item_id}")
            if result.cad_code:
                # Show just first line
                first_line = result.cad_code.split('\n')[0][:80]
                print(f"     Code: {first_line}...")


def test_prompt_formatting():
    """Test RAG retrieval and prompt formatting (no LLM call)."""
    print("\n" + "="*80)
    print("TEST 3: RAG Retrieval + Prompt Formatting")
    print("="*80 + "\n")
    
    config = load_config()
    retriever = MultimodalRAGRetriever(config["project_id"], config["location"])
    
    query = "Create a simple cylinder with a through hole"
    
    print(f"Query: '{query}'\n")
    print("Retrieving relevant CAD code examples...\n")
    
    # Retrieve examples
    results = retriever.query_text(query, top_k=3, filter_type="code")
    
    # Format context
    context = retriever.get_rag_context(results)
    
    # Build prompt (but don't call LLM)
    prompt = build_llm_prompt(query, context)
    
    print("-"*80)
    print("RETRIEVED EXAMPLES:")
    print("-"*80)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.datapoint_id} (distance: {result.distance:.4f})")
        if result.cad_code:
            preview = result.cad_code[:100].replace('\n', ' ')
            print(f"   {preview}...")
    
    print("\n" + "-"*80)
    print("RAG CONTEXT (Formatted for LLM):")
    print("-"*80)
    print(context)
    
    print("\n" + "-"*80)
    print("COMPLETE PROMPT (Ready to send to LLM):")
    print("-"*80)
    print(prompt)
    
    print("\n" + "-"*80)
    print(f"✅ Retrieved {len(results)} examples")
    print("📝 Prompt is ready to send to any LLM (but we're NOT calling one)")
    print("-"*80)


def test_multimodal_query():
    """Test multimodal query (text + image)."""
    print("\n" + "="*80)
    print("TEST 4: Multimodal Query (Text + Image)")
    print("="*80 + "\n")
    
    config = load_config()
    retriever = MultimodalRAGRetriever(config["project_id"], config["location"])
    
    # Test with different text + image combinations
    test_cases = [
        {
            "text": "box with holes",
            "image": "gs://cad-coder-bucket/rag-data/test_0.png",
            "description": "Test 0 - Box with holes"
        },
        {
            "text": "cylindrical part",
            "image": "gs://cad-coder-bucket/rag-data/test_1.png",
            "description": "Test 1 - Cylindrical part"
        },
        {
            "text": "mechanical component",
            "image": "gs://cad-coder-bucket/rag-data/test_2.png",
            "description": "Test 2 - Mechanical component"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'-'*80}")
        print(f"Test Case {i}: {test_case['description']}")
        print(f"Text: '{test_case['text']}'")
        print(f"Image: {test_case['image']}")
        print(f"{'-'*80}\n")
        
        try:
            results = retriever.query_multimodal(
                text_query=test_case['text'],
                image_source=test_case['image'],
                top_k=3,
                filter_type="code"
            )
            
            print(f"Retrieved {len(results)} results:\n")
            
            for j, result in enumerate(results, 1):
                print(f"{j}. {result.datapoint_id} (distance: {result.distance:.4f})")
                if result.cad_code:
                    preview = result.cad_code[:100].replace('\n', ' ')
                    print(f"   Code: {preview}...")
                print()
            
            # Show formatted context for first test case
            if i == 1:
                print("\n" + "-"*80)
                print("Sample RAG Context (for first test case):")
                print("-"*80)
                context = retriever.get_rag_context(results[:2], max_code_length=300)
                print(context)
        
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


def test_metadata_retrieval():
    """Test to verify metadata (CAD code) is properly stored and retrieved."""
    print("\n" + "="*80)
    print("TEST 5: Metadata Retrieval Verification")
    print("="*80 + "\n")
    
    config = load_config()
    retriever = MultimodalRAGRetriever(config["project_id"], config["location"])
    
    # Retrieve some code examples
    results = retriever.query_text("CAD code", top_k=5, filter_type="code")
    
    print(f"Retrieved {len(results)} code datapoints\n")
    
    has_code = 0
    missing_code = 0
    
    for result in results:
        if result.cad_code:
            has_code += 1
        else:
            missing_code += 1
    
    print(f"✅ Results with CAD code: {has_code}")
    print(f"❌ Results missing CAD code: {missing_code}")
    
    if has_code > 0:
        print("\n✅ SUCCESS: CAD code is being stored and retrieved correctly!")
        print("\nExample CAD code from first result:")
        print("-"*80)
        if results[0].cad_code:
            print(results[0].cad_code[:500])
    else:
        print("\n❌ WARNING: No CAD code found in metadata!")
        print("You may need to re-run pipeline.py to re-index with the updated metadata.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        
        if test_name == "single":
            test_single_text_query()
        elif test_name == "batch":
            test_batch_queries()
        elif test_name == "prompt":
            test_prompt_formatting()
        elif test_name == "metadata":
            test_metadata_retrieval()
        elif test_name == "multimodal":
            test_multimodal_query()
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: single, batch, prompt, metadata, multimodal")
    else:
        # Run all tests
        print("\nRunning all RAG tests...\n")
        
        try:
            test_metadata_retrieval()
        except Exception as e:
            print(f"Metadata test failed: {e}")
        
        try:
            test_single_text_query()
        except Exception as e:
            print(f"Single query test failed: {e}")
        
        try:
            test_batch_queries()
        except Exception as e:
            print(f"Batch query test failed: {e}")
        
        try:
            test_prompt_formatting()
        except Exception as e:
            print(f"Prompt formatting test failed: {e}")
        
        try:
            test_multimodal_query()
        except Exception as e:
            print(f"Multimodal test failed: {e}")
        
        print("\n" + "="*80)
        print("All tests completed!")
        print("="*80)

