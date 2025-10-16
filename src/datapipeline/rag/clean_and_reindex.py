"""
Clean existing vectors and re-index with updated metadata.

This script:
1. Generates datapoint IDs from your GCS data (same as pipeline would create)
2. Deletes those datapoints from the index
3. Re-generates embeddings with NEW metadata (including CAD code)
4. Upserts the new datapoints

NO REDEPLOYMENT NEEDED - just delete old vectors and add new ones!
"""

import logging
from vertexai import init as vertex_init
from google.cloud import aiplatform

from config import load_config, INDEX_NAME
from storage_utils import list_gcs_files
from embedding_generator import EmbeddingGenerator
from vector_search import VectorSearchManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_datapoint_ids_from_gcs(files: list) -> list:
    """
    Generate the datapoint IDs that would be created from the GCS files.
    This matches the ID generation logic in embedding_generator.py.
    """
    import os
    import json
    from storage_utils import read_gcs_text
    
    datapoint_ids = []
    
    # Get image files
    image_files = [f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    text_files = [f for f in files if f.lower().endswith((".jsonl", ".txt"))]
    
    # Image IDs: img_0, img_1, img_2, ...
    for i in range(len(image_files)):
        datapoint_ids.append(f"img_{i}")
    
    # Code IDs: code_{item_id}_c{chunk_index}
    for uri in text_files:
        if uri.lower().endswith(".jsonl"):
            try:
                content = read_gcs_text(uri)
                for line in content.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        obj = json.loads(line)
                        item_id = obj.get("id")
                        code = obj.get("code", "")
                        
                        if item_id and code:
                            # Estimate number of chunks (500 char chunks)
                            chunk_size = 500
                            num_chunks = max(1, (len(code) + chunk_size - 1) // chunk_size)
                            
                            for chunk_idx in range(num_chunks):
                                datapoint_ids.append(f"code_{item_id}_c{chunk_idx}")
                    
                    except json.JSONDecodeError:
                        continue
            
            except Exception as e:
                logging.warning(f"Error processing {uri}: {e}")
    
    return datapoint_ids


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clean and re-index vectors with updated metadata"
    )
    parser.add_argument(
        "--mode",
        choices=["delete-only", "delete-and-reindex", "info"],
        default="info",
        help="Operation mode"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompts"
    )
    
    args = parser.parse_args()
    
    logging.info("="*80)
    logging.info("Clean and Re-Index Script")
    logging.info("="*80)
    
    # Load config
    config = load_config()
    
    # Initialize Vertex AI
    aiplatform.init(project=config["project_id"], location=config["location"])
    vertex_init(project=config["project_id"], location=config["location"])
    
    # Get index
    indexes = aiplatform.MatchingEngineIndex.list(filter=f'display_name="{INDEX_NAME}"')
    if not indexes:
        logging.error(f"Index '{INDEX_NAME}' not found!")
        return
    
    index = indexes[0]
    logging.info(f"Found index: {index.display_name}")
    logging.info(f"Resource: {index.resource_name}")
    
    # List GCS files
    logging.info(f"\nScanning GCS bucket: {config['gcs_uri']}")
    files = list_gcs_files(config["gcs_uri"])
    logging.info(f"Found {len(files)} files in GCS")
    
    # Generate expected datapoint IDs
    logging.info("\nGenerating datapoint IDs from GCS data...")
    datapoint_ids = get_datapoint_ids_from_gcs(files)
    logging.info(f"Found {len(datapoint_ids)} expected datapoint IDs")
    
    if args.mode == "info":
        logging.info("\n" + "="*80)
        logging.info("INFORMATION")
        logging.info("="*80)
        logging.info(f"Index: {index.display_name}")
        logging.info(f"GCS Files: {len(files)}")
        logging.info(f"Expected Datapoints: {len(datapoint_ids)}")
        logging.info("\nSample datapoint IDs:")
        for id in datapoint_ids[:10]:
            logging.info(f"  - {id}")
        if len(datapoint_ids) > 10:
            logging.info(f"  ... and {len(datapoint_ids) - 10} more")
        
        logging.info("\nTo delete old vectors and re-index:")
        logging.info("  python clean_and_reindex.py --mode delete-and-reindex")
        logging.info("\nTo delete only (without re-indexing):")
        logging.info("  python clean_and_reindex.py --mode delete-only")
        logging.info("="*80)
        return
    
    # Delete existing datapoints
    if args.mode in ["delete-only", "delete-and-reindex"]:
        logging.info("\n" + "="*80)
        logging.info("STEP 1: DELETING OLD VECTORS")
        logging.info("="*80)
        logging.info(f"Will attempt to delete {len(datapoint_ids)} datapoint(s)")
        
        if not args.yes:
            confirm = input("\nProceed with deletion? (yes/no): ")
            if confirm.lower() != "yes":
                logging.info("Cancelled")
                return
        
        logging.info(f"\nDeleting {len(datapoint_ids)} datapoints from index...")
        
        try:
            # Delete in batches to avoid potential request size limits
            batch_size = 100
            for i in range(0, len(datapoint_ids), batch_size):
                batch = datapoint_ids[i:i+batch_size]
                logging.info(f"Deleting batch {i//batch_size + 1} ({len(batch)} datapoints)...")
                
                try:
                    index.remove_datapoints(datapoint_ids=batch)
                    logging.info(f"  ✅ Batch {i//batch_size + 1} deleted")
                except Exception as e:
                    # Some IDs might not exist, which is okay
                    logging.warning(f"  ⚠️  Batch {i//batch_size + 1} error (some IDs may not exist): {e}")
            
            logging.info(f"\n✅ Deletion complete!")
            logging.info("Old vectors (without CAD code metadata) have been removed")
        
        except Exception as e:
            logging.error(f"❌ Error during deletion: {e}")
            return
    
    # Re-index with new metadata
    if args.mode == "delete-and-reindex":
        logging.info("\n" + "="*80)
        logging.info("STEP 2: RE-INDEXING WITH NEW METADATA")
        logging.info("="*80)
        logging.info("Generating new embeddings with CAD code in metadata...")
        
        # Generate embeddings (with NEW metadata format including CAD code)
        embedding_generator = EmbeddingGenerator()
        datapoints = embedding_generator.generate_embeddings(files)
        
        if not datapoints:
            logging.error("❌ No datapoints generated!")
            return
        
        logging.info(f"Generated {len(datapoints)} datapoints with updated metadata")
        
        # Verify CAD code is present
        code_datapoints = [dp for dp in datapoints if any(
            r.get("namespace") == "cad_code" for r in dp.get("restricts", [])
        )]
        logging.info(f"  - {len(code_datapoints)} datapoints have CAD code in metadata ✅")
        
        # Upsert new datapoints
        logging.info("\nUpserting new datapoints to index...")
        
        try:
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(datapoints), batch_size):
                batch = datapoints[i:i+batch_size]
                logging.info(f"Upserting batch {i//batch_size + 1} ({len(batch)} datapoints)...")
                index.upsert_datapoints(datapoints=batch)
                logging.info(f"  ✅ Batch {i//batch_size + 1} upserted")
            
            logging.info(f"\n✅ Re-indexing complete!")
        
        except Exception as e:
            logging.error(f"❌ Error during upsert: {e}")
            raise
    
    # Final summary
    logging.info("\n" + "="*80)
    logging.info("✅ SUCCESS!")
    logging.info("="*80)
    
    if args.mode == "delete-only":
        logging.info("Old vectors have been deleted.")
        logging.info("To re-index with new metadata, run:")
        logging.info("  python clean_and_reindex.py --mode delete-and-reindex")
    
    elif args.mode == "delete-and-reindex":
        logging.info("All vectors updated with CAD code metadata!")
        logging.info("\nYou can now test RAG retrieval:")
        logging.info("  python test_rag.py metadata")
        logging.info("  python demo.py")
        logging.info("  python rag_retrieval.py --mode text --query 'your query'")
    
    logging.info("="*80)


if __name__ == "__main__":
    main()

