from pymongo import MongoClient
from datetime import datetime
import os

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.getenv("MONGO_DB", "cad_coder")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db["history"]


def add_record(
    user_id,
    prompt,
    cad_code,
    gcs_uri=None,
    image_uri=None,
    input_type="text"
):
    """Insert a new multimodal record into MongoDB."""
    doc = {
        "user_id": user_id,
        "prompt": prompt,
        "cad_code": cad_code,
        "gcs_uri": gcs_uri,
        "image_uri": image_uri,
        "input_type": input_type,  # "text" / "image" / "both"
        "timestamp": datetime.utcnow()
    }
    collection.insert_one(doc)


def get_history(limit=10, user_id=None):
    """Retrieve recent history, optionally filtered by user_id."""
    query = {}
    if user_id:
        query["user_id"] = user_id

    cursor = collection.find(query).sort("timestamp", -1).limit(limit)
    results = []
    for item in cursor:
        item_dict = dict(item)
        # Convert ObjectId to string for JSON serialization
        if "_id" in item_dict:
            item_dict["_id"] = str(item_dict["_id"])
        results.append(item_dict)
    return results

def get_all_prompts(limit=200):
    """
    Retrieve all prompts + responses (cad_code) for RAG.
    """
    cursor = collection.find(
        {"prompt": {"$ne": None}},
        {"prompt": 1, "cad_code": 1}
    ).sort("timestamp", -1).limit(limit)

    results = []
    for item in cursor:
        results.append({
            "prompt": item.get("prompt", ""),
            "response": item.get("cad_code", "")
        })

    return results



def get_history_images(limit=20, user_id=None):
    """Retrieve records that contain image history."""
    query = {"image_uri": {"$ne": None}}
    if user_id:
        query["user_id"] = user_id

    cursor = collection.find(query).sort("timestamp", -1).limit(limit)
    results = []
    for item in cursor:
        item_dict = dict(item)
        # Convert ObjectId to string for JSON serialization
        if "_id" in item_dict:
            item_dict["_id"] = str(item_dict["_id"])
        results.append(item_dict)
    return results
