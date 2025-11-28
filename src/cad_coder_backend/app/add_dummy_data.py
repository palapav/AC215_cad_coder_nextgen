#!/usr/bin/env python3
"""
Script to add dummy data to MongoDB for testing.
Run this script to populate your MongoDB with sample CAD generation records.
"""

import sys
import os
from datetime import datetime, timedelta

# Import from services (script is now in app directory)
from services.db_service import add_record, collection

def add_dummy_data():
    """Add sample dummy data to MongoDB."""
    
    dummy_records = [
        {
            "user_id": "user_001",
            "prompt": "Create a simple cube with dimensions 10x10x10",
            "cad_code": "cube = Part.makeBox(10, 10, 10)\nPart.show(cube)",
            "gcs_uri": None,
            "image_uri": None,
            "input_type": "text"
        },
        {
            "user_id": "user_001",
            "prompt": "Generate a cylinder with radius 5 and height 20",
            "cad_code": "cylinder = Part.makeCylinder(5, 20)\nPart.show(cylinder)",
            "gcs_uri": None,
            "image_uri": "/images/cylinder_ref.png",
            "input_type": "image"
        },
        {
            "user_id": "user_002",
            "prompt": "Design a gear with 20 teeth and module 2",
            "cad_code": "gear = Part.makeGear(20, 2)\nPart.show(gear)",
            "gcs_uri": "gs://cad-coder-bucket/gears/gear_001.step",
            "image_uri": None,
            "input_type": "text"
        },
        {
            "user_id": "user_002",
            "prompt": "Create a bracket with mounting holes",
            "cad_code": "bracket = Part.makeBox(50, 30, 5)\n# Add holes\nhole1 = Part.makeCylinder(3, 5)\nPart.show(bracket)",
            "gcs_uri": None,
            "image_uri": "/images/bracket_design.png",
            "input_type": "both"
        },
        {
            "user_id": "default",
            "prompt": "Generate a sphere with radius 15",
            "cad_code": "sphere = Part.makeSphere(15)\nPart.show(sphere)",
            "gcs_uri": None,
            "image_uri": None,
            "input_type": "text"
        },
        {
            "user_id": "default",
            "prompt": "Create a rectangular plate 100x50x5mm",
            "cad_code": "plate = Part.makeBox(100, 50, 5)\nPart.show(plate)",
            "gcs_uri": "gs://cad-coder-bucket/plates/plate_001.step",
            "image_uri": None,
            "input_type": "text"
        },
    ]
    
    # Show connection info (mask URI for security)
    mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017")
    mongo_db = os.getenv("MONGO_DB", "cad_coder")
    
    # Mask the connection string for security (show only first part)
    if "@" in mongo_uri:
        # MongoDB Atlas connection string
        masked_uri = mongo_uri.split("@")[0].split("://")[0] + "://****@" + mongo_uri.split("@")[1].split("/")[0]
    else:
        masked_uri = mongo_uri
    
    print("Adding dummy data to MongoDB...")
    print(f"Connection: {masked_uri}")
    print(f"Database: {mongo_db}")
    print(f"Collection: history")
    print("-" * 50)
    
    added_count = 0
    for record in dummy_records:
        try:
            add_record(
                user_id=record["user_id"],
                prompt=record["prompt"],
                cad_code=record["cad_code"],
                gcs_uri=record["gcs_uri"],
                image_uri=record["image_uri"],
                input_type=record["input_type"]
            )
            added_count += 1
            print(f"✓ Added record {added_count}: {record['prompt'][:50]}...")
        except Exception as e:
            print(f"✗ Failed to add record: {e}")
    
    print("-" * 50)
    print(f"Successfully added {added_count} records to MongoDB!")
    
    # Show summary
    total_count = collection.count_documents({})
    print(f"\nTotal records in database: {total_count}")
    
    # Show records by user
    print("\nRecords by user:")
    for user_id in ["user_001", "user_002", "default"]:
        count = collection.count_documents({"user_id": user_id})
        print(f"  - {user_id}: {count} records")

if __name__ == "__main__":
    # Load environment variables if .env exists
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get DB name for verification instructions
    mongo_db = os.getenv("MONGO_DB", "cad_coder")
    
    try:
        add_dummy_data()
        print("\n✅ Dummy data added successfully!")
        print("\nTo verify the data:")
        print("1. Check via API: curl http://localhost:8000/history/?limit=10")
        print("2. Check MongoDB Atlas:")
        print("   - Go to https://cloud.mongodb.com")
        print("   - Navigate to your cluster → Browse Collections")
        print(f"   - Look for database: {mongo_db} → collection: history")
        print("3. Use MongoDB Compass:")
        print("   - Connect using your MONGO_URI from .env file")
        print(f"   - Browse the '{mongo_db}.history' collection")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. Your .env file has MONGO_URI set to your MongoDB Atlas connection string")
        print("2. Your MongoDB Atlas cluster is accessible (check network access/whitelist)")
        print("3. Your credentials are correct in the MONGO_URI")
        sys.exit(1)

