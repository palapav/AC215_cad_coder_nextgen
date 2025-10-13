import os
import json
import logging
from typing import List, Dict

from vertexai.preview.vision_models import MultiModalEmbeddingModel

from config import RETRY_ATTEMPTS, RETRY_DELAY
from storage_utils import load_image_from_gcs, read_gcs_text, extract_image_filename, find_matching_image_uri
from processing_utils import chunk_code_text, retry_with_backoff

class EmbeddingGenerator:
    def __init__(self):
        self.model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")
        logging.info("Multimodal embedding model initialized")
    
    def get_image_embedding_with_retry(self, image_uri: str) -> List[float]:
        """Get image embedding with retry logic."""
        def _embed_image():
            img = load_image_from_gcs(image_uri)
            embeddings = self.model.get_embeddings(image=img)
            return embeddings.image_embedding
        
        try:
            return retry_with_backoff(_embed_image, max_attempts=RETRY_ATTEMPTS, base_delay=RETRY_DELAY)
        except Exception as e:
            logging.error(f"Failed to embed image {image_uri}: {e}")
            return [0.0] * 1408
    
    def get_text_embeddings_with_retry(self, text_chunks: List[str]) -> List[List[float]]:
        """Get text embeddings with retry logic."""
        embeddings = []
        
        for i, chunk in enumerate(text_chunks):
            def _embed_text():
                response = self.model.get_embeddings(contextual_text=chunk)
                if hasattr(response, 'text_embedding'):
                    return response.text_embedding
                elif hasattr(response, '_raw_prediction') and hasattr(response._raw_prediction, 'text_embedding'):
                    return list(response._raw_prediction.text_embedding)
                else:
                    logging.warning("Unexpected response format for text embedding")
                    return [0.0] * 1408
            
            try:
                emb = retry_with_backoff(_embed_text, max_attempts=RETRY_ATTEMPTS, base_delay=RETRY_DELAY)
                embeddings.append(emb)
                logging.info(f"✅ Successfully embedded text chunk {i+1}/{len(text_chunks)}")
            except Exception as e:
                logging.error(f"Failed to embed chunk {i+1}: {e}")
                embeddings.append([0.0] * 1408)
        
        return embeddings
    
    def generate_embeddings(self, files: List[str]) -> List[Dict]:
        """Generate embeddings for all files."""
        logging.info("--- GENERATING MULTIMODAL EMBEDDINGS ---")
        
        datapoints = []
        image_files = [f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff"))]
        text_files = [f for f in files if f.lower().endswith((".jsonl", ".txt"))]
        
        logging.info(f"Found {len(image_files)} image files and {len(text_files)} text files")

        # Process images
        for uri in image_files:
            try:
                emb = self.get_image_embedding_with_retry(uri)
                datapoints.append({
                    "id": f"img::{len(datapoints)}",
                    "vector": emb,
                    "metadata": {
                        "uri": uri, 
                        "type": "image",
                        "filename": os.path.basename(uri),
                        "paired_item": None
                    }
                })
                logging.info(f"[IMG] Successfully embedded: {uri}")
            except Exception as e:
                logging.error(f"Error embedding image {uri}: {e}")

        # Process text files
        for uri in text_files:
            try:
                if uri.lower().endswith(".jsonl"):
                    self._process_jsonl_file(uri, image_files, datapoints)
                else:
                    self._process_text_file(uri, datapoints)
            except Exception as e:
                logging.error(f"Error processing text file {uri}: {e}")

        logging.info(f"✅ Embeddings generated. Total datapoints: {len(datapoints)}")
        return datapoints
    
    def _process_jsonl_file(self, uri: str, image_files: List[str], datapoints: List[Dict]):
        """Process a JSONL file."""
        content = read_gcs_text(uri)
        chunks_processed = 0
        
        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                obj = json.loads(line)
                code_text = obj.get("code", "")
                item_id = obj.get("id", f"line_{line_num}")
                image_path = obj.get("image_path", "")
                
                if code_text:
                    image_filename = extract_image_filename(image_path)
                    matching_image_uri = find_matching_image_uri(image_files, image_filename) if image_filename else None
                    
                    chunks = chunk_code_text(code_text)
                    chunk_embeddings = self.get_text_embeddings_with_retry(chunks)
                    
                    for chunk_num, (chunk, emb) in enumerate(zip(chunks, chunk_embeddings)):
                        if not chunk.strip() or len(emb) == 0:
                            continue
                            
                        datapoint = {
                            "id": f"code::{len(datapoints)}",
                            "vector": emb,
                            "metadata": {
                                "source_uri": uri, 
                                "type": "code", 
                                "chunk": len(chunks) > 1,
                                "item_id": item_id,
                                "paired_image": matching_image_uri,
                                "paired_image_filename": image_filename,
                                "line_number": line_num,
                                "chunk_number": chunk_num,
                                "total_chunks": len(chunks),
                                "content_preview": chunk[:100] + "..." if len(chunk) > 100 else chunk
                            }
                        }
                        datapoints.append(datapoint)
                        chunks_processed += 1
                        
                        # Update image metadata if paired
                        if matching_image_uri:
                            for dp in datapoints:
                                if dp.get("metadata", {}).get("uri") == matching_image_uri:
                                    dp["metadata"]["paired_item"] = item_id
                                    break
                                
            except json.JSONDecodeError:
                logging.warning(f"JSON decode error in line {line_num}, skipping")
                continue
        
        logging.info(f"[CODE-JSONL] Processed {chunks_processed} code chunks from: {uri}")
    
    def _process_text_file(self, uri: str, datapoints: List[Dict]):
        """Process a plain text file."""
        content = read_gcs_text(uri)
        chunks = chunk_code_text(content)
        chunk_embeddings = self.get_text_embeddings_with_retry(chunks)
        
        for chunk_num, (chunk, emb) in enumerate(zip(chunks, chunk_embeddings)):
            if not chunk.strip() or len(emb) == 0:
                continue
                
            datapoints.append({
                "id": f"txt::{len(datapoints)}",
                "vector": emb,
                "metadata": {
                    "source_uri": uri, 
                    "type": "text", 
                    "chunk": True,
                    "chunk_number": chunk_num,
                    "total_chunks": len(chunks)
                }
            })
        
        logging.info(f"[TXT] Processed {len(chunks)} chunks from: {uri}")