from pymongo import MongoClient
from datetime import datetime
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.getenv("MONGO_DB", "cad_coder")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db["history"]

def add_record(user_id, prompt, cad_code, gcs_uri=None):
    doc = {
        "user_id": user_id,
        "prompt": prompt,
        "cad_code": cad_code,
        "gcs_uri": gcs_uri,
        "timestamp": datetime.utcnow()
    }
    collection.insert_one(doc)

def get_history(limit=10):
    cursor = collection.find().sort("timestamp", -1).limit(limit)
    return [dict(item) for item in cursor]
