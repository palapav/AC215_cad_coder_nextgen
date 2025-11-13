"""
Simple placeholder for RAG pipeline (retrieval-augmented generation)
"""
from app.services.db_service import get_all_prompts
import random

def retrieve_similar_context(prompt: str):
    """
    Retrieves context similar to the user's prompt from stored prompts (RAG-style).
    This can later call real src/rag modules for vector retrieval.
    """
    all_prompts = get_all_prompts()
    if not all_prompts:
        return [{"text": "No context available"}]

    # Simple placeholder similarity using random sample
    return random.sample(all_prompts, min(3, len(all_prompts)))

#Later, you’ll replace this with:
#from src.rag.rag_retrieval import retrieve_context
#return retrieve_context(prompt)
