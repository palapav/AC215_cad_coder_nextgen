from pymongo import MongoClient
from datetime import datetime
import os

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.getenv("MONGO_DB", "cad_coder")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db["history"]

def add_record(user_id, prompt, cad_code, gcs_uri=None):
    """Insert a new record into MongoDB."""
    doc = {
        "user_id": user_id,
        "prompt": prompt,
        "cad_code": cad_code,
        "gcs_uri": gcs_uri,
        "timestamp": datetime.utcnow()
    }
    collection.insert_one(doc)

def get_history(limit=10):
    """Retrieve the N most recent history records."""
    cursor = collection.find().sort("timestamp", -1).limit(limit)
    return [dict(item) for item in cursor]

def get_all_prompts():
    """
    Retrieve all prompts stored in MongoDB.
    Used by the RAG service for similarity search.
    """
    cursor = collection.find({}, {"prompt": 1, "_id": 0})
    return [item["prompt"] for item in cursor]

if __name__ == "__main__":
    add_record("tester", "cube", "import cadquery as cq", "gs://test/path")
    print(get_history())

