#!/usr/bin/env python3
"""
Interactive Demo of Multimodal RAG System for CAD Code Generation

This script demonstrates all the capabilities of the RAG system
with nice formatted output.
"""

import logging
from typing import List
from rag_retrieval import MultimodalRAGRetriever, RetrievalResult, build_llm_prompt
from config import load_config

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise for demo
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

def print_subheader(text: str):
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-'*len(text)}{Colors.ENDC}")

def print_result(result: RetrievalResult, index: int):
    print(f"\n{Colors.OKGREEN}📄 Result {index}{Colors.ENDC}")
    print(f"   ID: {Colors.OKCYAN}{result.datapoint_id}{Colors.ENDC}")
    print(f"   Distance: {Colors.WARNING}{result.distance:.4f}{Colors.ENDC} (lower = more similar)")
    print(f"   Type: {result.type}")
    
    if result.item_id:
        print(f"   Item ID: {result.item_id}")
    
    if result.paired_image:
        print(f"   🖼️  Paired Image: {result.paired_image}")
    
    if result.cad_code:
        print(f"\n   {Colors.BOLD}CAD Code:{Colors.ENDC}")
        code_lines = result.cad_code.split('\n')
        preview_lines = code_lines[:10]  # Show first 10 lines
        for line in preview_lines:
            print(f"   {Colors.OKCYAN}│{Colors.ENDC} {line}")
        
        if len(code_lines) > 10:
            print(f"   {Colors.OKCYAN}│{Colors.ENDC} ... ({len(code_lines) - 10} more lines)")

def demo_single_query(retriever: MultimodalRAGRetriever):
    """Demo 1: Single text query for CAD code."""
    print_header("DEMO 1: Single Text Query")
    
    query = "Create a box with rounded edges"
    print(f"{Colors.BOLD}Query:{Colors.ENDC} '{query}'")
    print(f"{Colors.BOLD}Top K:{Colors.ENDC} 3 results")
    print(f"{Colors.BOLD}Filter:{Colors.ENDC} Only 'code' type\n")
    
    print("🔍 Searching vector database...")
    results = retriever.query_text(query, top_k=3, filter_type="code")
    
    print(f"\n✅ Found {len(results)} relevant CAD code examples:")
    
    for i, result in enumerate(results, 1):
        print_result(result, i)
    
    # Show RAG context
    print_subheader("RAG Context (Formatted for LLM)")
    context = retriever.get_rag_context(results[:2], max_code_length=300)
    print(f"\n{Colors.OKCYAN}{context}{Colors.ENDC}")

def demo_batch_queries(retriever: MultimodalRAGRetriever):
    """Demo 2: Batch queries."""
    print_header("DEMO 2: Batch Text Queries")
    
    queries = [
        "cylinder with a through hole",
        "rectangular plate with mounting holes",
        "simple gear shape"
    ]
    
    print(f"{Colors.BOLD}Processing {len(queries)} queries:{Colors.ENDC}\n")
    for i, q in enumerate(queries, 1):
        print(f"  {i}. {q}")
    
    print(f"\n{Colors.BOLD}Top K per query:{Colors.ENDC} 2 results\n")
    
    print("🔍 Batch processing...")
    all_results = retriever.batch_query_text(queries, top_k=2)
    
    for i, (query, results) in enumerate(zip(queries, all_results), 1):
        print(f"\n{Colors.OKGREEN}Query {i}:{Colors.ENDC} '{query}'")
        
        for j, result in enumerate(results, 1):
            print(f"  {j}. {Colors.OKCYAN}{result.datapoint_id}{Colors.ENDC} "
                  f"(distance: {Colors.WARNING}{result.distance:.4f}{Colors.ENDC})")
            
            if result.cad_code:
                first_line = result.cad_code.split('\n')[0][:70]
                print(f"     Code: {first_line}...")

def demo_metadata_check(retriever: MultimodalRAGRetriever):
    """Demo 3: Verify metadata contains CAD code."""
    print_header("DEMO 3: Metadata Verification")
    
    print("🔍 Retrieving code examples to check metadata...\n")
    
    results = retriever.query_text("CAD code", top_k=5, filter_type="code")
    
    has_code = sum(1 for r in results if r.cad_code)
    missing_code = len(results) - has_code
    
    print(f"Retrieved: {len(results)} code datapoints")
    print(f"{Colors.OKGREEN}✅ With CAD code: {has_code}{Colors.ENDC}")
    
    if missing_code > 0:
        print(f"{Colors.FAIL}❌ Missing CAD code: {missing_code}{Colors.ENDC}")
        print(f"\n{Colors.WARNING}⚠️  Re-run 'python pipeline.py' to re-index with CAD code metadata{Colors.ENDC}")
    else:
        print(f"{Colors.OKGREEN}✅ All results have CAD code!{Colors.ENDC}")
    
    if results and results[0].cad_code:
        print_subheader("Example CAD Code from Metadata")
        print(f"\n{Colors.OKCYAN}{results[0].cad_code[:400]}{Colors.ENDC}")
        if len(results[0].cad_code) > 400:
            print(f"{Colors.OKCYAN}...{Colors.ENDC}")

def demo_prompt_formatting(retriever: MultimodalRAGRetriever):
    """Demo 4: RAG retrieval and prompt formatting (no LLM call)."""
    print_header("DEMO 4: RAG Context + Prompt Formatting")
    
    query = "Create a simple cylinder with a hole through the center"
    
    print(f"{Colors.BOLD}User Request:{Colors.ENDC} '{query}'")
    print(f"{Colors.BOLD}Top K Examples:{Colors.ENDC} 3")
    print(f"{Colors.BOLD}Mode:{Colors.ENDC} RAG Only (No LLM call)\n")
    
    print("🔍 Retrieving relevant CAD code examples...")
    results = retriever.query_text(query, top_k=3, filter_type="code")
    
    print("📝 Formatting context for LLM prompt...\n")
    
    # Show retrieved examples
    print_subheader("Retrieved Examples")
    for i, result in enumerate(results, 1):
        print(f"\n{Colors.OKGREEN}Example {i}:{Colors.ENDC}")
        print(f"  ID: {result.datapoint_id}")
        print(f"  Distance: {result.distance:.4f}")
        if result.cad_code:
            preview = result.cad_code[:150].replace('\n', ' ')
            print(f"  Code: {preview}...")
    
    # Format context
    context = retriever.get_rag_context(results)
    
    # Build prompt (but don't call LLM)
    prompt = build_llm_prompt(query, context)
    
    # Show the formatted prompt
    print_subheader("Complete Prompt (Ready for LLM)")
    print(f"\n{Colors.OKCYAN}{prompt}{Colors.ENDC}\n")
    
    print(f"{Colors.OKGREEN}✅ This prompt is ready to send to any LLM!{Colors.ENDC}")
    print(f"{Colors.WARNING}(But we're NOT actually calling an LLM in this demo){Colors.ENDC}\n")

def demo_comparison(retriever: MultimodalRAGRetriever):
    """Demo 5: Compare retrieval for different query types."""
    print_header("DEMO 5: Query Comparison")
    
    queries = {
        "Specific geometric terms": "fillet edge cylinder radius",
        "Natural language": "create a round container with smooth corners",
        "Technical CAD terms": "extrude workplane chamfer"
    }
    
    for query_type, query in queries.items():
        print(f"\n{Colors.BOLD}{query_type}:{Colors.ENDC} '{query}'")
        results = retriever.query_text(query, top_k=3, filter_type="code")
        
        if results:
            print(f"  Top result: {Colors.OKCYAN}{results[0].datapoint_id}{Colors.ENDC} "
                  f"(distance: {Colors.WARNING}{results[0].distance:.4f}{Colors.ENDC})")
            if results[0].cad_code:
                first_line = results[0].cad_code.split('\n')[0][:60]
                print(f"  Code: {first_line}...")

def main():
    """Run all demos."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                            ║")
    print("║           Multimodal RAG System for CAD Code Generation - DEMO            ║")
    print("║                                                                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    try:
        # Initialize
        print(f"{Colors.BOLD}Initializing RAG system...{Colors.ENDC}")
        config = load_config()
        retriever = MultimodalRAGRetriever(config["project_id"], config["location"])
        print(f"{Colors.OKGREEN}✅ System ready!{Colors.ENDC}\n")
        
        # Run demos
        demo_metadata_check(retriever)
        input(f"\n{Colors.WARNING}Press Enter to continue to Demo 1...{Colors.ENDC}")
        
        demo_single_query(retriever)
        input(f"\n{Colors.WARNING}Press Enter to continue to Demo 2...{Colors.ENDC}")
        
        demo_batch_queries(retriever)
        input(f"\n{Colors.WARNING}Press Enter to continue to Demo 3...{Colors.ENDC}")
        
        demo_comparison(retriever)
        input(f"\n{Colors.WARNING}Press Enter to continue to Demo 4 (Prompt Formatting)...{Colors.ENDC}")
        
        demo_prompt_formatting(retriever)
        
        # Summary
        print_header("DEMO COMPLETE")
        print(f"{Colors.OKGREEN}✅ All demos completed successfully!{Colors.ENDC}\n")
        print(f"{Colors.BOLD}What you can do next:{Colors.ENDC}")
        print(f"  1. Try custom queries: {Colors.OKCYAN}python rag_retrieval.py --mode text --query 'your query'{Colors.ENDC}")
        print(f"  2. See formatted prompts: {Colors.OKCYAN}python rag_retrieval.py --mode prompt --query 'your query'{Colors.ENDC}")
        print(f"  3. Run tests: {Colors.OKCYAN}python test_rag.py{Colors.ENDC}")
        print(f"  4. Use the Python API in your own code")
        print(f"  5. Send the formatted prompt to your LLM of choice\n")
        
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Error: {e}{Colors.ENDC}\n")
        print(f"{Colors.WARNING}Make sure you've run 'python pipeline.py' first!{Colors.ENDC}\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick mode: just run one demo
        config = load_config()
        retriever = MultimodalRAGRetriever(config["project_id"], config["location"])
        demo_single_query(retriever)
    else:
        # Full interactive demo
        main()

