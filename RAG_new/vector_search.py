import logging
from typing import List, Dict
from google.cloud import aiplatform

from config import INDEX_NAME, ENDPOINT_NAME, DEPLOYED_INDEX_ID

class VectorSearchManager:
    def __init__(self, project_id: str, location: str):
        self.project_id = project_id
        self.location = location
        self.index = None
        self.endpoint = None

    def setup_infrastructure(self, dimensions: int):
        """
        Set up the Matching Engine index and endpoint.
        It will reuse existing resources if they match the configured names,
        otherwise it will create them.
        """
        aiplatform.init(project=self.project_id, location=self.location)
        
        # --- 1. Get or Create MatchingEngineIndex ---
        existing_indexes = [
            idx for idx in aiplatform.MatchingEngineIndex.list() 
            if idx.display_name == INDEX_NAME
        ]
        
        if existing_indexes:
            self.index = existing_indexes[0]
            logging.info(f"Reusing existing Index: {self.index.resource_name}")
        else:
            logging.info(f"Attempting to create Tree-AH Index: {INDEX_NAME}, dim={dimensions}")
            
            try:
                # Use the specific create_tree_ah_index method
                self.index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
                    display_name=INDEX_NAME,
                    dimensions=dimensions,
                    distance_measure_type="DOT_PRODUCT_DISTANCE",
                    approximate_neighbors_count=150,
                    leaf_node_embedding_count=1000,
                    leaf_nodes_to_search_percent=5  # Corrected parameter
                )
                logging.info(f"✅ Tree-AH index created successfully: {self.index.resource_name}")
                
            except Exception as e:
                logging.warning(f"Tree-AH index creation failed: {e}. Falling back to Brute Force.")
                
                # Use the specific create_brute_force_index method as a fallback
                self.index = aiplatform.MatchingEngineIndex.create_brute_force_index(
                    display_name=INDEX_NAME,
                    dimensions=dimensions,
                    distance_measure_type="DOT_PRODUCT_DISTANCE",
                )
                logging.info(f"✅ Brute Force index created as a fallback: {self.index.resource_name}")

        # --- 2. Get or Create MatchingEngineIndexEndpoint ---
        existing_endpoints = [
            ep for ep in aiplatform.MatchingEngineIndexEndpoint.list() 
            if ep.display_name == ENDPOINT_NAME
        ]
        
        if existing_endpoints:
            self.endpoint = existing_endpoints[0]
            logging.info(f"Reusing existing IndexEndpoint: {self.endpoint.resource_name}")
        else:
            logging.info(f"Creating IndexEndpoint: {ENDPOINT_NAME}")
            self.endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
                display_name=ENDPOINT_NAME,
                public_endpoint_enabled=True  # Specify public network access
            )
            logging.info(f"IndexEndpoint created: {self.endpoint.resource_name}")

        # --- 3. Deploy Index to Endpoint ---
        if self.endpoint.deployed_indexes and any(di.id == DEPLOYED_INDEX_ID for di in self.endpoint.deployed_indexes):
            logging.info(f"Index '{self.index.display_name}' already deployed as '{DEPLOYED_INDEX_ID}'")
        else:
            logging.info(f"Deploying index to endpoint as '{DEPLOYED_INDEX_ID}' ...")
            self.endpoint.deploy_index(
                index=self.index,
                deployed_index_id=DEPLOYED_INDEX_ID
            )
            logging.info("✅ Index deployment completed.")

    def upsert_datapoints(self, datapoints: List[Dict]):
        """
        Upsert vectors (datapoints) into the deployed index in batches.
        """
        if not datapoints:
            logging.warning("No datapoints provided to upsert.")
            return

        logging.info(f"Preparing to upsert {len(datapoints)} datapoints...")
        
        # Split upsert into batches of 1000 to avoid potential request size limits
        for i in range(0, len(datapoints), 1000):
            batch = datapoints[i:i+1000]
            
            # The SDK now handles the IndexDatapoint conversion internally
            self.index.upsert_datapoints(datapoints=batch)

            logging.info(f"Upserted batch {i//1000 + 1}/{ -(-len(datapoints) // 1000)}")

        logging.info("✅ All datapoints upserted successfully.")


# # vector_search.py

# import logging
# from typing import List, Dict
# from google.cloud import aiplatform

# from config import INDEX_NAME, ENDPOINT_NAME, DEPLOYED_INDEX_ID

# class VectorSearchManager:
#     def __init__(self, project_id: str, location: str):
#         self.project_id = project_id
#         self.location = location
#         self.index = None
#         self.endpoint = None
    
#     def setup_infrastructure(self, dimensions: int):
#         """Setup index and endpoint."""
#         # Get or create index
#         existing = [idx for idx in aiplatform.MatchingEngineIndex.list() 
#                    if idx.display_name == INDEX_NAME]
        
#         if existing:
#             self.index = existing[0]
#             logging.info(f"Reusing existing Index: {self.index.resource_name}")
#         else:
#             logging.info(f"Attempting to create Tree-AH Index: {INDEX_NAME}, dim={dimensions}")
            
#             try:
#                 # Use the specific create_tree_ah_index method
#                 self.index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
#                     display_name=INDEX_NAME,
#                     dimensions=dimensions,
#                     distance_measure_type="DOT_PRODUCT_DISTANCE",
#                     approximate_neighbors_count=150,
#                     leaf_node_embedding_count=1000,
#                     leaf_nodes_to_search_fraction=0.05
#                 )
#                 logging.info("✅ Tree-AH index created successfully")
                
#             except Exception as e:
#                 logging.warning(f"Tree-AH index creation failed: {e}. Falling back to Brute Force.")
                
#                 # Use the specific create_brute_force_index method as a fallback
#                 self.index = aiplatform.MatchingEngineIndex.create_brute_force_index(
#                     display_name=INDEX_NAME,
#                     dimensions=dimensions,
#                     distance_measure_type="DOT_PRODUCT_DISTANCE",
#                 )
#                 logging.info("✅ Brute Force index created as a fallback.")
            
#             logging.info(f"Index created: {self.index.resource_name}")
        
#         # Get or create endpoint
#         existing = [ep for ep in aiplatform.MatchingEngineIndexEndpoint.list() 
#                    if ep.display_name == ENDPOINT_NAME]
        
#         if existing:
#             self.endpoint = existing[0]
#             logging.info(f"Reusing existing IndexEndpoint: {self.endpoint.resource_name}")
#         else:
#             logging.info(f"Creating IndexEndpoint: {ENDPOINT_NAME}")
#             self.endpoint = aiplatform.MatchingEngineIndexEndpoint.create(display_name=ENDPOINT_NAME)
#             logging.info(f"IndexEndpoint created: {self.endpoint.resource_name}")
        
#         # Deploy index if not already deployed
#         if self.endpoint.deployed_indexes and any(di.id == DEPLOYED_INDEX_ID for di in self.endpoint.deployed_indexes):
#             logging.info(f"Index already deployed as '{DEPLOYED_INDEX_ID}'")
#         else:
#             logging.info(f"Deploying index to endpoint as '{DEPLOYED_INDEX_ID}' ...")
#             self.endpoint.deploy_index(
#                 index=self.index,
#                 deployed_index_id=DEPLOYED_INDEX_ID
#             )
#             logging.info("Index deployment completed.")
    
#     def upsert_datapoints(self, datapoints: List[Dict]):
#         """Upsert vectors into the deployed index."""
#         if not datapoints:
#             logging.warning("No datapoints to upsert.")
#             return
        
#         dp_objs = [
#             aiplatform.IndexDatapoint(
#                 datapoint_id=str(dp["id"]),
#                 feature_vector=dp["vector"],
#             )
#             for dp in datapoints
#         ]
        
#         logging.info(f"Upserting {len(dp_objs)} datapoints ...")
#         # Split upsert into batches of 1000 to avoid potential request size limits
#         for i in range(0, len(dp_objs), 1000):
#             batch = dp_objs[i:i+1000]
#             self.endpoint.upsert_datapoints(
#                 datapoints=batch, 
#                 deployed_index_id=DEPLOYED_INDEX_ID
#             )
#             logging.info(f"Upserted batch {i//1000 + 1}")

#         logging.info("✅ Upsert completed.")