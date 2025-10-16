import time
import logging
from typing import List

def chunk_code_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Chunk CadQuery code while preserving structure."""
    text = text.strip()
    if not text:
        return []
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    lines = text.split('\n')
    current_chunk = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if len(current_chunk) + len(line) + 1 > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            
            if overlap > 0:
                overlap_lines = current_chunk.split('\n')[-2:]
                current_chunk = '\n'.join(overlap_lines) + '\n' + line
            else:
                current_chunk = line
        else:
            current_chunk = current_chunk + '\n' + line if current_chunk else line
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def retry_with_backoff(func, max_attempts: int = 3, base_delay: int = 5, *args, **kwargs):
    """Retry function with exponential backoff."""
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            logging.warning(f"Attempt {attempt+1}/{max_attempts} failed: {e}")
            
            if attempt < max_attempts - 1:
                wait_time = base_delay * (2 ** attempt)
                logging.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                logging.error(f"All {max_attempts} attempts failed")
    
    raise last_exception