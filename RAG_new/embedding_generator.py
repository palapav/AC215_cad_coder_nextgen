import os
import json
import logging
import re
from typing import List, Dict, Any

from vertexai.preview.vision_models import MultiModalEmbeddingModel

from config import RETRY_ATTEMPTS, RETRY_DELAY
from storage_utils import load_image_from_gcs, read_gcs_text, extract_image_filename, find_matching_image_uri
from processing_utils import chunk_code_text, retry_with_backoff

def _create_restrictions(metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Converts a metadata dictionary to the list of restriction objects
    required by the Vertex AI SDK. It also sanitizes the values.
    """
    restricts = []
    for key, value in metadata.items():
        if value is None:
            continue
        
        # Ensure value is a list of strings
        value_list = [str(value)] if isinstance(value, (str, int, float, bool)) else [str(v) for v in value]

        if value_list:
            # Sanitize tokens for Vertex AI restrictions (letters, numbers, underscores only)
            sanitized_values = [re.sub(r'[^a-zA-Z0-9_]', '_', v)[:100] for v in value_list]
            restricts.append({
                "namespace": key,
                "allow_list": sanitized_values
            })
    return restricts

class EmbeddingGenerator:
    def __init__(self):
        self.model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")
        logging.info("Multimodal embedding model initialized")

    def get_image_embedding_with_retry(self, image_uri: str) -> List[float]:
        def _embed_image():
            img = load_image_from_gcs(image_uri)
            return self.model.get_embeddings(image=img).image_embedding
        try:
            return retry_with_backoff(_embed_image, max_attempts=RETRY_ATTEMPTS, base_delay=RETRY_DELAY)
        except Exception as e:
            logging.error(f"Failed to embed image {image_uri}: {e}")
            return [0.0] * 1408

    def get_text_embeddings_with_retry(self, text_chunks: List[str]) -> List[List[float]]:
        embeddings = []
        for i, chunk in enumerate(text_chunks):
            def _embed_text():
                return self.model.get_embeddings(contextual_text=chunk).text_embedding
            try:
                emb = retry_with_backoff(_embed_text, max_attempts=RETRY_ATTEMPTS, base_delay=RETRY_DELAY)
                embeddings.append(emb)
                logging.info(f"✅ Embedded text chunk {i+1}/{len(text_chunks)}")
            except Exception as e:
                logging.error(f"Failed to embed chunk {i+1}: {e}")
                embeddings.append([0.0] * 1408)
        return embeddings

    def generate_embeddings(self, files: List[str]) -> List[Dict]:
        logging.info("--- GENERATING MULTIMODAL EMBEDDINGS ---")
        datapoints = []
        image_files = [f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        text_files = [f for f in files if f.lower().endswith((".jsonl", ".txt"))]

        for uri in image_files:
            emb = self.get_image_embedding_with_retry(uri)
            metadata = {"uri": uri, "type": "image", "filename": os.path.basename(uri), "paired_item": "None"}
            datapoints.append({
                "datapoint_id": f"img_{len(datapoints)}",
                "feature_vector": emb,
                "restricts": _create_restrictions(metadata)
            })

        paired_images = {}
        for uri in text_files:
            if uri.lower().endswith(".jsonl"):
                self._process_jsonl_file(uri, image_files, datapoints, paired_images)

        # Update metadata for paired images
        for img_uri, item_id in paired_images.items():
            for dp in datapoints:
                # Find image datapoint by matching the sanitized URI in its restrictions
                if dp["restricts"] and dp["restricts"][0].get("namespace") == "uri":
                    sanitized_uri = re.sub(r'[^a-zA-Z0-9_]', '_', img_uri)[:100]
                    if dp["restricts"][0]["allow_list"][0] == sanitized_uri:
                        dp["restricts"].append({"namespace": "paired_item", "allow_list": [item_id]})
                        break
        
        logging.info(f"✅ Embeddings generated. Total datapoints: {len(datapoints)}")
        return datapoints

    def _process_jsonl_file(self, uri: str, image_files: List[str], datapoints: List[Dict], paired_images: Dict):
        content = read_gcs_text(uri)
        for line_num, line in enumerate(content.splitlines(), 1):
            try:
                obj = json.loads(line)
                code, item_id, image_path = obj.get("code"), obj.get("id"), obj.get("image_path")
                if code and item_id:
                    matching_uri = find_matching_image_uri(image_files, extract_image_filename(image_path))
                    if matching_uri:
                        paired_images[matching_uri] = item_id
                    
                    chunks = chunk_code_text(code)
                    embeddings = self.get_text_embeddings_with_retry(chunks)
                    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                        metadata = {"source_uri": uri, "type": "code", "item_id": item_id, "paired_image": matching_uri or "None"}
                        datapoints.append({
                            "datapoint_id": f"code_{item_id}_c{i}",
                            "feature_vector": emb,
                            "restricts": _create_restrictions(metadata)
                        })
            except (json.JSONDecodeError, AttributeError):
                logging.warning(f"Skipping malformed line {line_num} in {uri}")







# import os
# import json
# import logging
# from typing import List, Dict

# from vertexai.preview.vision_models import MultiModalEmbeddingModel

# from config import RETRY_ATTEMPTS, RETRY_DELAY
# from storage_utils import load_image_from_gcs, read_gcs_text, extract_image_filename, find_matching_image_uri
# from processing_utils import chunk_code_text, retry_with_backoff

# class EmbeddingGenerator:
#     def __init__(self):
#         self.model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")
#         logging.info("Multimodal embedding model initialized")
    
#     def get_image_embedding_with_retry(self, image_uri: str) -> List[float]:
#         """Get image embedding with retry logic."""
#         def _embed_image():
#             img = load_image_from_gcs(image_uri)
#             embeddings = self.model.get_embeddings(image=img)
#             return embeddings.image_embedding
        
#         try:
#             return retry_with_backoff(_embed_image, max_attempts=RETRY_ATTEMPTS, base_delay=RETRY_DELAY)
#         except Exception as e:
#             logging.error(f"Failed to embed image {image_uri}: {e}")
#             return [0.0] * 1408
    
#     def get_text_embeddings_with_retry(self, text_chunks: List[str]) -> List[List[float]]:
#         """Get text embeddings with retry logic."""
#         embeddings = []
        
#         for i, chunk in enumerate(text_chunks):
#             def _embed_text():
#                 response = self.model.get_embeddings(contextual_text=chunk)
#                 if hasattr(response, 'text_embedding'):
#                     return response.text_embedding
#                 elif hasattr(response, '_raw_prediction') and hasattr(response._raw_prediction, 'text_embedding'):
#                     return list(response._raw_prediction.text_embedding)
#                 else:
#                     logging.warning("Unexpected response format for text embedding")
#                     return [0.0] * 1408
            
#             try:
#                 emb = retry_with_backoff(_embed_text, max_attempts=RETRY_ATTEMPTS, base_delay=RETRY_DELAY)
#                 embeddings.append(emb)
#                 logging.info(f"✅ Successfully embedded text chunk {i+1}/{len(text_chunks)}")
#             except Exception as e:
#                 logging.error(f"Failed to embed chunk {i+1}: {e}")
#                 embeddings.append([0.0] * 1408)
        
#         return embeddings
    
#     def generate_embeddings(self, files: List[str]) -> List[Dict]:
#         """Generate embeddings for all files."""
#         logging.info("--- GENERATING MULTIMODAL EMBEDDINGS ---")
        
#         datapoints = []
#         image_files = [f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff"))]
#         text_files = [f for f in files if f.lower().endswith((".jsonl", ".txt"))]
        
#         logging.info(f"Found {len(image_files)} image files and {len(text_files)} text files")

#         # Process images
#         for uri in image_files:
#             try:
#                 emb = self.get_image_embedding_with_retry(uri)
#                 datapoints.append({
#                     "datapoint_id": f"img::{len(datapoints)}",
#                     "feature_vector": emb, # CORRECTED KEY
#                     "metadata": {
#                         "uri": uri, 
#                         "type": "image",
#                         "filename": os.path.basename(uri),
#                         "paired_item": None
#                     }
#                 })
#                 logging.info(f"[IMG] Successfully embedded: {uri}")
#             except Exception as e:
#                 logging.error(f"Error embedding image {uri}: {e}")

#         # Process text files
#         for uri in text_files:
#             try:
#                 if uri.lower().endswith(".jsonl"):
#                     self._process_jsonl_file(uri, image_files, datapoints)
#                 else:
#                     self._process_text_file(uri, datapoints)
#             except Exception as e:
#                 logging.error(f"Error processing text file {uri}: {e}")

#         logging.info(f"✅ Embeddings generated. Total datapoints: {len(datapoints)}")
#         return datapoints
    
#     def _process_jsonl_file(self, uri: str, image_files: List[str], datapoints: List[Dict]):
#         """Process a JSONL file."""
#         content = read_gcs_text(uri)
#         chunks_processed = 0
        
#         for line_num, line in enumerate(content.splitlines(), 1):
#             line = line.strip()
#             if not line:
#                 continue
                
#             try:
#                 obj = json.loads(line)
#                 code_text = obj.get("code", "")
#                 item_id = obj.get("id", f"line_{line_num}")
#                 image_path = obj.get("image_path", "")
                
#                 if code_text:
#                     image_filename = extract_image_filename(image_path)
#                     matching_image_uri = find_matching_image_uri(image_files, image_filename) if image_filename else None
                    
#                     chunks = chunk_code_text(code_text)
#                     chunk_embeddings = self.get_text_embeddings_with_retry(chunks)
                    
#                     for chunk_num, (chunk, emb) in enumerate(zip(chunks, chunk_embeddings)):
#                         if not chunk.strip() or len(emb) == 0:
#                             continue
                            
#                         datapoint = {
#                             "datapoint_id": f"code::{len(datapoints)}",
#                             "feature_vector": emb, # CORRECTED KEY
#                             "metadata": {
#                                 "source_uri": uri, 
#                                 "type": "code", 
#                                 "chunk": len(chunks) > 1,
#                                 "item_id": item_id,
#                                 "paired_image": matching_image_uri,
#                                 "paired_image_filename": image_filename,
#                                 "line_number": line_num,
#                                 "chunk_number": chunk_num,
#                                 "total_chunks": len(chunks),
#                                 "content_preview": chunk[:100] + "..." if len(chunk) > 100 else chunk
#                             }
#                         }
#                         datapoints.append(datapoint)
#                         chunks_processed += 1
                        
#                         # Update image metadata if paired
#                         if matching_image_uri:
#                             for dp in datapoints:
#                                 if dp.get("metadata", {}).get("uri") == matching_image_uri:
#                                     dp["metadata"]["paired_item"] = item_id
#                                     break
                                
#             except json.JSONDecodeError:
#                 logging.warning(f"JSON decode error in line {line_num}, skipping")
#                 continue
        
#         logging.info(f"[CODE-JSONL] Processed {chunks_processed} code chunks from: {uri}")
    
#     def _process_text_file(self, uri: str, datapoints: List[Dict]):
#         """Process a plain text file."""
#         content = read_gcs_text(uri)
#         chunks = chunk_code_text(content)
#         chunk_embeddings = self.get_text_embeddings_with_retry(chunks)
        
#         for chunk_num, (chunk, emb) in enumerate(zip(chunks, chunk_embeddings)):
#             if not chunk.strip() or len(emb) == 0:
#                 continue
                
#             datapoints.append({
#                 "datapoint_id": f"txt::{len(datapoints)}",
#                 "feature_vector": emb, # CORRECTED KEY
#                 "metadata": {
#                     "source_uri": uri, 
#                     "type": "text", 
#                     "chunk": True,
#                     "chunk_number": chunk_num,
#                     "total_chunks": len(chunks)
#                 }
#             })
        
#         logging.info(f"[TXT] Processed {len(chunks)} chunks from: {uri}")






# id issue version



# import os
# import json
# import logging
# from typing import List, Dict

# from vertexai.preview.vision_models import MultiModalEmbeddingModel

# from config import RETRY_ATTEMPTS, RETRY_DELAY
# from storage_utils import load_image_from_gcs, read_gcs_text, extract_image_filename, find_matching_image_uri
# from processing_utils import chunk_code_text, retry_with_backoff

# class EmbeddingGenerator:
#     def __init__(self):
#         self.model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")
#         logging.info("Multimodal embedding model initialized")
    
#     def get_image_embedding_with_retry(self, image_uri: str) -> List[float]:
#         """Get image embedding with retry logic."""
#         def _embed_image():
#             img = load_image_from_gcs(image_uri)
#             embeddings = self.model.get_embeddings(image=img)
#             return embeddings.image_embedding
        
#         try:
#             return retry_with_backoff(_embed_image, max_attempts=RETRY_ATTEMPTS, base_delay=RETRY_DELAY)
#         except Exception as e:
#             logging.error(f"Failed to embed image {image_uri}: {e}")
#             return [0.0] * 1408
    
#     def get_text_embeddings_with_retry(self, text_chunks: List[str]) -> List[List[float]]:
#         """Get text embeddings with retry logic."""
#         embeddings = []
        
#         for i, chunk in enumerate(text_chunks):
#             def _embed_text():
#                 response = self.model.get_embeddings(contextual_text=chunk)
#                 if hasattr(response, 'text_embedding'):
#                     return response.text_embedding
#                 elif hasattr(response, '_raw_prediction') and hasattr(response._raw_prediction, 'text_embedding'):
#                     return list(response._raw_prediction.text_embedding)
#                 else:
#                     logging.warning("Unexpected response format for text embedding")
#                     return [0.0] * 1408
            
#             try:
#                 emb = retry_with_backoff(_embed_text, max_attempts=RETRY_ATTEMPTS, base_delay=RETRY_DELAY)
#                 embeddings.append(emb)
#                 logging.info(f"✅ Successfully embedded text chunk {i+1}/{len(text_chunks)}")
#             except Exception as e:
#                 logging.error(f"Failed to embed chunk {i+1}: {e}")
#                 embeddings.append([0.0] * 1408)
        
#         return embeddings
    
#     def generate_embeddings(self, files: List[str]) -> List[Dict]:
#         """Generate embeddings for all files."""
#         logging.info("--- GENERATING MULTIMODAL EMBEDDINGS ---")
        
#         datapoints = []
#         image_files = [f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff"))]
#         text_files = [f for f in files if f.lower().endswith((".jsonl", ".txt"))]
        
#         logging.info(f"Found {len(image_files)} image files and {len(text_files)} text files")

#         # Process images
#         for uri in image_files:
#             try:
#                 emb = self.get_image_embedding_with_retry(uri)
#                 datapoints.append({
#                     "id": f"img::{len(datapoints)}",
#                     "vector": emb,
#                     "metadata": {
#                         "uri": uri, 
#                         "type": "image",
#                         "filename": os.path.basename(uri),
#                         "paired_item": None
#                     }
#                 })
#                 logging.info(f"[IMG] Successfully embedded: {uri}")
#             except Exception as e:
#                 logging.error(f"Error embedding image {uri}: {e}")

#         # Process text files
#         for uri in text_files:
#             try:
#                 if uri.lower().endswith(".jsonl"):
#                     self._process_jsonl_file(uri, image_files, datapoints)
#                 else:
#                     self._process_text_file(uri, datapoints)
#             except Exception as e:
#                 logging.error(f"Error processing text file {uri}: {e}")

#         logging.info(f"✅ Embeddings generated. Total datapoints: {len(datapoints)}")
#         return datapoints
    
#     def _process_jsonl_file(self, uri: str, image_files: List[str], datapoints: List[Dict]):
#         """Process a JSONL file."""
#         content = read_gcs_text(uri)
#         chunks_processed = 0
        
#         for line_num, line in enumerate(content.splitlines(), 1):
#             line = line.strip()
#             if not line:
#                 continue
                
#             try:
#                 obj = json.loads(line)
#                 code_text = obj.get("code", "")
#                 item_id = obj.get("id", f"line_{line_num}")
#                 image_path = obj.get("image_path", "")
                
#                 if code_text:
#                     image_filename = extract_image_filename(image_path)
#                     matching_image_uri = find_matching_image_uri(image_files, image_filename) if image_filename else None
                    
#                     chunks = chunk_code_text(code_text)
#                     chunk_embeddings = self.get_text_embeddings_with_retry(chunks)
                    
#                     for chunk_num, (chunk, emb) in enumerate(zip(chunks, chunk_embeddings)):
#                         if not chunk.strip() or len(emb) == 0:
#                             continue
                            
#                         datapoint = {
#                             "id": f"code::{len(datapoints)}",
#                             "vector": emb,
#                             "metadata": {
#                                 "source_uri": uri, 
#                                 "type": "code", 
#                                 "chunk": len(chunks) > 1,
#                                 "item_id": item_id,
#                                 "paired_image": matching_image_uri,
#                                 "paired_image_filename": image_filename,
#                                 "line_number": line_num,
#                                 "chunk_number": chunk_num,
#                                 "total_chunks": len(chunks),
#                                 "content_preview": chunk[:100] + "..." if len(chunk) > 100 else chunk
#                             }
#                         }
#                         datapoints.append(datapoint)
#                         chunks_processed += 1
                        
#                         # Update image metadata if paired
#                         if matching_image_uri:
#                             for dp in datapoints:
#                                 if dp.get("metadata", {}).get("uri") == matching_image_uri:
#                                     dp["metadata"]["paired_item"] = item_id
#                                     break
                                
#             except json.JSONDecodeError:
#                 logging.warning(f"JSON decode error in line {line_num}, skipping")
#                 continue
        
#         logging.info(f"[CODE-JSONL] Processed {chunks_processed} code chunks from: {uri}")
    
#     def _process_text_file(self, uri: str, datapoints: List[Dict]):
#         """Process a plain text file."""
#         content = read_gcs_text(uri)
#         chunks = chunk_code_text(content)
#         chunk_embeddings = self.get_text_embeddings_with_retry(chunks)
        
#         for chunk_num, (chunk, emb) in enumerate(zip(chunks, chunk_embeddings)):
#             if not chunk.strip() or len(emb) == 0:
#                 continue
                
#             datapoints.append({
#                 "id": f"txt::{len(datapoints)}",
#                 "vector": emb,
#                 "metadata": {
#                     "source_uri": uri, 
#                     "type": "text", 
#                     "chunk": True,
#                     "chunk_number": chunk_num,
#                     "total_chunks": len(chunks)
#                 }
#             })
        
#         logging.info(f"[TXT] Processed {len(chunks)} chunks from: {uri}")