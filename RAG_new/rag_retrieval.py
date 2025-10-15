"""
RAG Retrieval System for Multimodal CAD Code Generation

This script provides retrieval-augmented generation capabilities for querying
the vector search index with text descriptions or images to retrieve relevant
CAD code examples.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
import re

from google.cloud import aiplatform
from vertexai.preview.vision_models import MultiModalEmbeddingModel, Image

from config import load_config, INDEX_NAME, ENDPOINT_NAME, DEPLOYED_INDEX_ID
from storage_utils import load_image_from_gcs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

@dataclass
class RetrievalResult:
    """Represents a single retrieval result from the vector search."""
    datapoint_id: str
    distance: float
    metadata: Dict[str, Any]
    cad_code: Optional[str] = None
    type: Optional[str] = None
    item_id: Optional[str] = None
    paired_image: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)
    
    def __str__(self):
        s = f"ID: {self.datapoint_id}\n"
        s += f"Distance: {self.distance:.4f}\n"
        s += f"Type: {self.type}\n"
        if self.item_id:
            s += f"Item ID: {self.item_id}\n"
        if self.paired_image:
            s += f"Paired Image: {self.paired_image}\n"
        if self.cad_code:
            preview = self.cad_code[:200] + "..." if len(self.cad_code) > 200 else self.cad_code
            s += f"CAD Code Preview:\n{preview}\n"
        return s


class MultimodalRAGRetriever:
    """Handles retrieval from the multimodal vector search index."""
    
    def __init__(self, project_id: str, location: str):
        self.project_id = project_id
        self.location = location
        
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)
        
        # Load embedding model
        self.embedding_model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")
        logging.info("Multimodal embedding model initialized")
        
        # Load index and endpoint
        self.index = self._get_index()
        self.endpoint = self._get_endpoint()
        
        logging.info(f"RAG Retriever initialized with index: {self.index.display_name}")
    
    def _get_index(self):
        """Get the vector search index."""
        indexes = aiplatform.MatchingEngineIndex.list(filter=f'display_name="{INDEX_NAME}"')
        if not indexes:
            raise ValueError(f"Index '{INDEX_NAME}' not found. Please run pipeline.py first.")
        return indexes[0]
    
    def _get_endpoint(self):
        """Get the index endpoint."""
        endpoints = aiplatform.MatchingEngineIndexEndpoint.list(filter=f'display_name="{ENDPOINT_NAME}"')
        if not endpoints:
            raise ValueError(f"Endpoint '{ENDPOINT_NAME}' not found. Please run pipeline.py first.")
        return endpoints[0]
    
    def _embed_text(self, text: str) -> List[float]:
        """Generate embedding for text query."""
        response = self.embedding_model.get_embeddings(contextual_text=text)
        return response.text_embedding
    
    def _embed_image(self, image_source: Union[str, Image]) -> List[float]:
        """Generate embedding for image query."""
        if isinstance(image_source, str):
            # Load from GCS or local path
            if image_source.startswith("gs://"):
                image = load_image_from_gcs(image_source)
            else:
                image = Image.load_from_file(image_source)
        else:
            image = image_source
        
        response = self.embedding_model.get_embeddings(image=image)
        return response.image_embedding
    
    def _parse_metadata_from_restricts(self, restricts: List[Dict]) -> Dict[str, Any]:
        """Parse metadata from the restricts field returned by Vertex AI."""
        metadata = {}
        for restrict in restricts:
            namespace = restrict.get("namespace", "")
            allow_list = restrict.get("allow_list", [])
            if allow_list:
                # Store the first value (or join if multiple)
                metadata[namespace] = allow_list[0] if len(allow_list) == 1 else allow_list
        return metadata
    
    def query_text(
        self, 
        query: str, 
        top_k: int = 5,
        filter_type: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Query the index with a text description.
        
        Args:
            query: Text description of the CAD object to search for
            top_k: Number of results to return
            filter_type: Optional filter by type ('code' or 'image')
        
        Returns:
            List of RetrievalResult objects
        """
        logging.info(f"Querying with text: '{query[:100]}...'")
        
        # Generate query embedding
        query_embedding = self._embed_text(query)
        
        # Perform vector search
        results = self._search(query_embedding, top_k, filter_type)
        
        logging.info(f"Retrieved {len(results)} results")
        return results
    
    def query_image(
        self, 
        image_source: Union[str, Image], 
        top_k: int = 5,
        filter_type: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Query the index with an image.
        
        Args:
            image_source: GCS URI, local path, or Image object
            top_k: Number of results to return
            filter_type: Optional filter by type ('code' or 'image')
        
        Returns:
            List of RetrievalResult objects
        """
        logging.info(f"Querying with image: {image_source}")
        
        # Generate query embedding
        query_embedding = self._embed_image(image_source)
        
        # Perform vector search
        results = self._search(query_embedding, top_k, filter_type)
        
        logging.info(f"Retrieved {len(results)} results")
        return results
    
    def query_multimodal(
        self,
        text_query: str,
        image_source: Union[str, Image],
        top_k: int = 5,
        filter_type: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Query the index with both text and image (multimodal).
        
        Args:
            text_query: Text description
            image_source: GCS URI, local path, or Image object
            top_k: Number of results to return
            filter_type: Optional filter by type ('code' or 'image')
        
        Returns:
            List of RetrievalResult objects
        """
        logging.info(f"Querying with text: '{text_query}' and image: {image_source}")
        
        # Load image
        if isinstance(image_source, str):
            if image_source.startswith("gs://"):
                image = load_image_from_gcs(image_source)
            else:
                image = Image.load_from_file(image_source)
        else:
            image = image_source
        
        # Generate multimodal embedding (both text and image)
        response = self.embedding_model.get_embeddings(
            image=image,
            contextual_text=text_query
        )
        
        # Use the image embedding (which is contextualized by the text)
        query_embedding = response.image_embedding
        
        # Perform vector search
        results = self._search(query_embedding, top_k, filter_type)
        
        logging.info(f"Retrieved {len(results)} results")
        return results
    
    def _search(
        self, 
        query_embedding: List[float], 
        top_k: int,
        filter_type: Optional[str] = None
    ) -> List[RetrievalResult]:
        """Perform the actual vector search."""
        from google.cloud.aiplatform_v1 import MatchServiceClient
        from google.cloud.aiplatform_v1.types import FindNeighborsRequest, IndexDatapoint
        
        # Get the public endpoint domain
        public_endpoint_domain = self.endpoint.public_endpoint_domain_name
        
        # Build datapoint with optional filter
        restricts = []
        if filter_type:
            restricts.append(
                IndexDatapoint.Restriction(
                    namespace="type",
                    allow_list=[filter_type]
                )
            )
        
        datapoint = IndexDatapoint(
            datapoint_id="temp_query",
            feature_vector=query_embedding,
            restricts=restricts
        )
        
        # Build query
        query = FindNeighborsRequest.Query(
            datapoint=datapoint,
            neighbor_count=top_k
        )
        
        # Create match client and call find_neighbors
        client = MatchServiceClient(
            client_options={"api_endpoint": f"{public_endpoint_domain}:443"}
        )
        
        request = FindNeighborsRequest(
            index_endpoint=self.endpoint.resource_name,
            deployed_index_id=DEPLOYED_INDEX_ID,
            queries=[query],
            return_full_datapoint=True  # Need this to get metadata/restricts
        )
        
        response = client.find_neighbors(request=request)
        
        # Parse results
        results = []
        if response and hasattr(response, 'nearest_neighbors'):
            for query_result in response.nearest_neighbors:
                if hasattr(query_result, 'neighbors'):
                    for neighbor in query_result.neighbors:
                        # Get ID and distance
                        datapoint_id = neighbor.datapoint.datapoint_id if hasattr(neighbor, 'datapoint') else "unknown"
                        distance = neighbor.distance if hasattr(neighbor, 'distance') else 0.0
                        
                        # Get metadata from restricts (check both neighbor and datapoint)
                        restricts_list = []
                        
                        # Try neighbor.restricts first
                        if hasattr(neighbor, 'restricts') and neighbor.restricts:
                            for restrict in neighbor.restricts:
                                restricts_list.append({
                                    "namespace": restrict.namespace,
                                    "allow_list": list(restrict.allow_list)
                                })
                        # Then try neighbor.datapoint.restricts
                        elif hasattr(neighbor, 'datapoint') and hasattr(neighbor.datapoint, 'restricts') and neighbor.datapoint.restricts:
                            for restrict in neighbor.datapoint.restricts:
                                restricts_list.append({
                                    "namespace": restrict.namespace,
                                    "allow_list": list(restrict.allow_list)
                                })
                        
                        metadata = self._parse_metadata_from_restricts(restricts_list)
                        
                        result = RetrievalResult(
                            datapoint_id=datapoint_id,
                            distance=distance,
                            metadata=metadata,
                            cad_code=metadata.get("cad_code"),
                            type=metadata.get("type"),
                            item_id=metadata.get("item_id"),
                            paired_image=metadata.get("paired_image")
                        )
                        results.append(result)
        
        # Sort by distance ascending (lower = more similar)
        results.sort(key=lambda x: x.distance)
        
        return results
    
    def batch_query_text(
        self, 
        queries: List[str], 
        top_k: int = 5
    ) -> List[List[RetrievalResult]]:
        """
        Query the index with multiple text descriptions.
        
        Args:
            queries: List of text descriptions
            top_k: Number of results per query
        
        Returns:
            List of result lists (one per query)
        """
        logging.info(f"Processing batch of {len(queries)} text queries")
        
        all_results = []
        for i, query in enumerate(queries):
            logging.info(f"Processing query {i+1}/{len(queries)}: {query[:50]}...")
            results = self.query_text(query, top_k)
            all_results.append(results)
        
        return all_results
    
    def get_rag_context(
        self, 
        results: List[RetrievalResult],
        include_images: bool = True,
        max_code_length: int = 2000
    ) -> str:
        """
        Format retrieval results as context for LLM prompt.
        
        Args:
            results: List of retrieval results
            include_images: Whether to mention paired images
            max_code_length: Maximum length of code to include per result
        
        Returns:
            Formatted context string for LLM
        """
        context_parts = ["Here are relevant CAD code examples:\n"]
        
        for i, result in enumerate(results, 1):
            context_parts.append(f"\n--- Example {i} (Distance: {result.distance:.4f}) ---")
            
            if result.item_id:
                context_parts.append(f"Item ID: {result.item_id}")
            
            if include_images and result.paired_image:
                context_parts.append(f"Associated Image: {result.paired_image}")
            
            if result.cad_code:
                code = result.cad_code
                if len(code) > max_code_length:
                    code = code[:max_code_length] + "\n... (truncated)"
                context_parts.append(f"\nCAD Code:\n```python\n{code}\n```")
            
            context_parts.append("")  # Empty line separator
        
        return "\n".join(context_parts)


def build_llm_prompt(query: str, context: str) -> str:
    """
    Build a prompt that WOULD be sent to an LLM (for demonstration purposes).
    
    This shows how to format the RAG context for LLM consumption,
    but does NOT actually call an LLM.
    
    Args:
        query: User's request
        context: Retrieved RAG context
    
    Returns:
        Formatted prompt string
    """
    prompt = f"""You are an expert CAD programmer using CadQuery/Python.

Given the following user request and relevant code examples, generate CAD code that fulfills the request.

User Request: {query}

{context}

Instructions:
1. Study the provided examples to understand the coding patterns
2. Generate complete, working CadQuery code
3. Include imports and proper syntax
4. Add comments explaining key steps
5. Ensure the code is similar in style to the examples

Generated CAD Code:
"""
    return prompt


def main():
    """Main function for testing RAG retrieval."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Multimodal RAG Retrieval")
    parser.add_argument("--mode", choices=["text", "image", "multimodal", "batch", "prompt"], default="text",
                       help="Query mode: text, image, multimodal (text+image), batch, or prompt")
    parser.add_argument("--query", type=str, help="Text query")
    parser.add_argument("--image", type=str, help="Image path or GCS URI")
    parser.add_argument("--batch-file", type=str, help="JSON file with batch queries")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("--filter-type", choices=["code", "image"], help="Filter by type")
    parser.add_argument("--output", type=str, help="Output JSON file for results")
    
    args = parser.parse_args()
    
    # Load config and initialize retriever
    config = load_config()
    retriever = MultimodalRAGRetriever(config["project_id"], config["location"])
    
    # Process based on mode
    if args.mode == "text":
        if not args.query:
            args.query = "Create a simple box with rounded edges"
        
        print(f"\n{'='*80}")
        print(f"TEXT QUERY: {args.query}")
        print(f"{'='*80}\n")
        
        results = retriever.query_text(args.query, top_k=args.top_k, filter_type=args.filter_type)
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(result)
        
        # Show RAG context
        print(f"\n{'='*80}")
        print("RAG CONTEXT FOR LLM:")
        print(f"{'='*80}\n")
        context = retriever.get_rag_context(results)
        print(context)
    
    elif args.mode == "image":
        if not args.image:
            print("Error: --image required for image mode")
            return
        
        print(f"\n{'='*80}")
        print(f"IMAGE QUERY: {args.image}")
        print(f"{'='*80}\n")
        
        results = retriever.query_image(args.image, top_k=args.top_k, filter_type=args.filter_type)
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(result)
        
        context = retriever.get_rag_context(results)
        print(f"\n{'='*80}")
        print("RAG CONTEXT FOR LLM:")
        print(f"{'='*80}\n")
        print(context)
    
    elif args.mode == "multimodal":
        if not args.query or not args.image:
            print("Error: Both --query and --image required for multimodal mode")
            print("Example: python rag_retrieval.py --mode multimodal --query 'box with holes' --image 'gs://bucket/image.png'")
            return
        
        print(f"\n{'='*80}")
        print(f"MULTIMODAL QUERY (Text + Image)")
        print(f"Text: {args.query}")
        print(f"Image: {args.image}")
        print(f"{'='*80}\n")
        
        results = retriever.query_multimodal(
            args.query, 
            args.image, 
            top_k=args.top_k, 
            filter_type=args.filter_type
        )
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(result)
        
        # Show RAG context
        context = retriever.get_rag_context(results)
        print(f"\n{'='*80}")
        print("RAG CONTEXT FOR LLM:")
        print(f"{'='*80}\n")
        print(context)
        
        # Also show prompt
        prompt = build_llm_prompt(args.query, context)
        print(f"\n{'='*80}")
        print("COMPLETE PROMPT (Ready for LLM):")
        print(f"{'='*80}\n")
        print(prompt)
    
    elif args.mode == "batch":
        if not args.batch_file:
            # Use example queries
            queries = [
                "Create a cylinder with a hole through the center",
                "Make a rectangular plate with mounting holes",
                "Design a gear with 20 teeth"
            ]
        else:
            with open(args.batch_file, 'r') as f:
                queries = json.load(f)
        
        print(f"\n{'='*80}")
        print(f"BATCH QUERY: {len(queries)} queries")
        print(f"{'='*80}\n")
        
        all_results = retriever.batch_query_text(queries, top_k=args.top_k)
        
        for i, (query, results) in enumerate(zip(queries, all_results), 1):
            print(f"\n{'='*80}")
            print(f"Query {i}: {query}")
            print(f"{'='*80}\n")
            
            for j, result in enumerate(results, 1):
                print(f"Result {j}: {result.datapoint_id} (distance: {result.distance:.4f})")
                if result.cad_code:
                    preview = result.cad_code[:100].replace('\n', ' ')
                    print(f"  Code: {preview}...")
        
        # Save to file if requested
        if args.output:
            output_data = []
            for query, results in zip(queries, all_results):
                output_data.append({
                    "query": query,
                    "results": [r.to_dict() for r in results]
                })
            
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"\nResults saved to: {args.output}")
    
    elif args.mode == "prompt":
        if not args.query:
            args.query = "Create a simple box with rounded edges"
        
        print(f"\n{'='*80}")
        print(f"RAG CONTEXT + PROMPT FORMATTING (No LLM Call)")
        print(f"Query: {args.query}")
        print(f"{'='*80}\n")
        
        # Retrieve examples
        results = retriever.query_text(args.query, top_k=args.top_k, filter_type="code")
        
        # Format context
        context = retriever.get_rag_context(results)
        
        # Build prompt (but don't send to LLM)
        prompt = build_llm_prompt(args.query, context)
        
        print("\n--- RETRIEVED EXAMPLES ---")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.datapoint_id} (distance: {result.distance:.4f})")
            if result.cad_code:
                preview = result.cad_code[:150].replace('\n', ' ')
                print(f"   Code: {preview}...")
        
        print("\n--- RAG CONTEXT (Formatted for LLM) ---")
        print(context)
        
        print("\n--- COMPLETE PROMPT (Ready for LLM) ---")
        print(prompt)
        
        print("\n" + "="*80)
        print("📝 This prompt is ready to send to any LLM of your choice!")
        print("   (But we're NOT calling an LLM in this demo)")
        print("="*80)
        
        if args.output:
            output_data = {
                "query": args.query,
                "retrieved_examples": [r.to_dict() for r in results],
                "context": context,
                "prompt": prompt
            }
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"\nData saved to: {args.output}")


if __name__ == "__main__":
    main()

