"""
Delete all vectors from the Vertex AI Vector Search index.

This script removes all existing datapoints from the index without destroying
the index infrastructure itself. After deletion, you can re-upsert with updated metadata.
"""

import logging
from typing import List
from google.cloud import aiplatform

from config import load_config, INDEX_NAME

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class VectorCleaner:
    """Manages deletion of vectors from Vertex AI Vector Search index."""
    
    def __init__(self, project_id: str, location: str):
        self.project_id = project_id
        self.location = location
        
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)
        
        # Get the index
        self.index = self._get_index()
        
        logging.info(f"Connected to index: {self.index.display_name}")
        logging.info(f"Index resource: {self.index.resource_name}")
    
    def _get_index(self):
        """Get the vector search index."""
        indexes = aiplatform.MatchingEngineIndex.list(filter=f'display_name="{INDEX_NAME}"')
        if not indexes:
            raise ValueError(f"Index '{INDEX_NAME}' not found.")
        return indexes[0]
    
    def get_all_datapoint_ids(self) -> List[str]:
        """
        Get all datapoint IDs from the index.
        
        Note: Vertex AI doesn't provide a direct API to list all datapoint IDs,
        so we'll need to track them or use a known pattern.
        
        Returns:
            List of datapoint IDs to delete
        """
        logging.warning("Vertex AI doesn't provide a direct API to list all datapoint IDs.")
        logging.info("Generating expected datapoint IDs based on indexing pattern...")
        
        # Based on embedding_generator.py, we have:
        # - Image IDs: "img_0", "img_1", etc.
        # - Code IDs: "code_{item_id}_c{chunk_index}"
        
        # We'll need to estimate based on what was indexed
        # For safety, let's return a range that covers the expected IDs
        
        datapoint_ids = []
        
        # Add image IDs (assume up to 100 images)
        for i in range(100):
            datapoint_ids.append(f"img_{i}")
        
        # Add code IDs - this is trickier since we don't know all item_ids
        # We'll need a different approach
        
        logging.warning("Cannot automatically determine all datapoint IDs.")
        logging.info("You have two options:")
        logging.info("1. Delete index and recreate (slower but complete)")
        logging.info("2. Use remove_all_datapoints() if available")
        
        return datapoint_ids
    
    def delete_all_datapoints_by_pattern(self, max_images: int = 100):
        """
        Delete datapoints by attempting common ID patterns.
        
        This is a best-effort approach since Vertex AI doesn't provide
        a list_all_datapoints API.
        """
        logging.info("Attempting to delete datapoints by pattern...")
        logging.warning("This may not delete all datapoints if IDs don't match expected patterns.")
        
        datapoint_ids = []
        
        # Try to delete image datapoints
        for i in range(max_images):
            datapoint_ids.append(f"img_{i}")
        
        if datapoint_ids:
            logging.info(f"Attempting to delete {len(datapoint_ids)} datapoints...")
            try:
                self.index.remove_datapoints(datapoint_ids=datapoint_ids)
                logging.info(f"✅ Successfully deleted {len(datapoint_ids)} datapoints")
            except Exception as e:
                logging.warning(f"Some datapoints may not exist: {e}")
                logging.info("This is expected if not all IDs were present")
    
    def delete_index_completely(self):
        """
        Delete the entire index.
        
        WARNING: This will require you to recreate and redeploy the index,
        which takes ~30-60 minutes.
        """
        logging.warning("⚠️  You are about to DELETE the entire index!")
        logging.warning(f"Index: {self.index.display_name}")
        logging.warning(f"Resource: {self.index.resource_name}")
        logging.warning("This will require redeployment (~30-60 minutes)")
        
        confirm = input("\nType 'DELETE' to confirm: ")
        
        if confirm == "DELETE":
            logging.info("Deleting index...")
            self.index.delete()
            logging.info("✅ Index deleted successfully")
            logging.info("You will need to run pipeline.py to recreate everything")
        else:
            logging.info("Deletion cancelled")


def main():
    """Main function with command-line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Delete vectors from Vertex AI Vector Search index"
    )
    parser.add_argument(
        "--mode",
        choices=["pattern", "delete-index", "info"],
        default="info",
        help="Deletion mode: pattern (try common IDs), delete-index (remove entire index), info (show info)"
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=100,
        help="Maximum number of image IDs to try (for pattern mode)"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompts"
    )
    
    args = parser.parse_args()
    
    # Load config and initialize
    config = load_config()
    cleaner = VectorCleaner(config["project_id"], config["location"])
    
    if args.mode == "info":
        print("\n" + "="*80)
        print("INDEX INFORMATION")
        print("="*80)
        print(f"Index Name: {cleaner.index.display_name}")
        print(f"Resource: {cleaner.index.resource_name}")
        print(f"Description: {cleaner.index.description}")
        print("\nTo delete vectors, use:")
        print("  --mode pattern       # Try to delete by common ID patterns")
        print("  --mode delete-index  # Delete entire index (requires redeployment)")
        print("="*80 + "\n")
    
    elif args.mode == "pattern":
        print("\n" + "="*80)
        print("PATTERN-BASED DELETION")
        print("="*80)
        print("This will attempt to delete datapoints using common ID patterns.")
        print("⚠️  Note: This may not delete ALL vectors if IDs don't match patterns.")
        print(f"Trying up to {args.max_images} image IDs...\n")
        
        if not args.confirm:
            confirm = input("Continue? (y/n): ")
            if confirm.lower() != 'y':
                print("Cancelled")
                return
        
        cleaner.delete_all_datapoints_by_pattern(max_images=args.max_images)
        
        print("\n⚠️  IMPORTANT: This method may not have deleted all vectors.")
        print("If you want to be certain, use --mode delete-index instead.")
    
    elif args.mode == "delete-index":
        print("\n" + "="*80)
        print("DELETE ENTIRE INDEX")
        print("="*80)
        print("⚠️  WARNING: This will delete the entire index infrastructure!")
        print("You will need to:")
        print("  1. Re-create the index")
        print("  2. Re-deploy to endpoint (~30-60 minutes)")
        print("  3. Re-upsert all vectors\n")
        
        cleaner.delete_index_completely()


if __name__ == "__main__":
    main()

