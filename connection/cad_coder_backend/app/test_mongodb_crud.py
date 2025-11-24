#!/usr/bin/env python3
"""
Comprehensive test script for MongoDB CRUD operations with text and image data.
Tests:
- Writing text data
- Writing image data (as base64 encoded strings)
- Reading/retrieving text data
- Reading/retrieving image data
- Querying by different fields
- Updating records
"""

import base64
import os
from datetime import datetime
from services.db_service import (
    add_record, 
    get_history, 
    get_history_images,
    collection,
    db
)

def create_test_image_base64():
    """Create a simple test image as base64 string (1x1 red pixel PNG)"""
    # Minimal valid PNG: 1x1 red pixel
    png_data = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
    )
    return base64.b64encode(png_data).decode('utf-8')

def test_write_text_data():
    """Test 1: Write text-only data to MongoDB"""
    print("\n" + "="*60)
    print("TEST 1: Writing Text Data")
    print("="*60)
    
    test_record = {
        "user_id": "test_user_text",
        "prompt": "Create a test cube with text input only",
        "cad_code": "cube = Part.makeBox(5, 5, 5)\nPart.show(cube)",
        "gcs_uri": None,
        "image_uri": None,
        "input_type": "text"
    }
    
    try:
        add_record(
            user_id=test_record["user_id"],
            prompt=test_record["prompt"],
            cad_code=test_record["cad_code"],
            gcs_uri=test_record["gcs_uri"],
            image_uri=test_record["image_uri"],
            input_type=test_record["input_type"]
        )
        print("✅ SUCCESS: Text data written to MongoDB")
        print(f"   - User ID: {test_record['user_id']}")
        print(f"   - Prompt: {test_record['prompt']}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_write_image_data():
    """Test 2: Write image data (as base64) to MongoDB"""
    print("\n" + "="*60)
    print("TEST 2: Writing Image Data (Base64)")
    print("="*60)
    
    # Create test image as base64
    image_base64 = create_test_image_base64()
    
    test_record = {
        "user_id": "test_user_image",
        "prompt": "Generate CAD from this test image",
        "cad_code": "cylinder = Part.makeCylinder(3, 10)\nPart.show(cylinder)",
        "gcs_uri": None,
        "image_uri": "/test/images/test_image.png",
        "image_data": image_base64,  # Store actual image data
        "input_type": "image"
    }
    
    try:
        # Add image data to the document
        doc = {
            "user_id": test_record["user_id"],
            "prompt": test_record["prompt"],
            "cad_code": test_record["cad_code"],
            "gcs_uri": test_record["gcs_uri"],
            "image_uri": test_record["image_uri"],
            "image_data": test_record["image_data"],  # Base64 encoded image
            "input_type": test_record["input_type"],
            "timestamp": datetime.utcnow()
        }
        collection.insert_one(doc)
        print("✅ SUCCESS: Image data (base64) written to MongoDB")
        print(f"   - User ID: {test_record['user_id']}")
        print(f"   - Image URI: {test_record['image_uri']}")
        print(f"   - Image data size: {len(image_base64)} characters (base64)")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_write_both_text_and_image():
    """Test 3: Write record with both text and image"""
    print("\n" + "="*60)
    print("TEST 3: Writing Text + Image Data")
    print("="*60)
    
    image_base64 = create_test_image_base64()
    
    test_record = {
        "user_id": "test_user_both",
        "prompt": "Create a bracket based on this image and description",
        "cad_code": "bracket = Part.makeBox(20, 15, 3)\nPart.show(bracket)",
        "gcs_uri": "gs://test-bucket/brackets/test_001.step",
        "image_uri": "/test/images/bracket_ref.png",
        "image_data": image_base64,
        "input_type": "both"
    }
    
    try:
        doc = {
            "user_id": test_record["user_id"],
            "prompt": test_record["prompt"],
            "cad_code": test_record["cad_code"],
            "gcs_uri": test_record["gcs_uri"],
            "image_uri": test_record["image_uri"],
            "image_data": test_record["image_data"],
            "input_type": test_record["input_type"],
            "timestamp": datetime.utcnow()
        }
        collection.insert_one(doc)
        print("✅ SUCCESS: Text + Image data written to MongoDB")
        print(f"   - User ID: {test_record['user_id']}")
        print(f"   - Input type: {test_record['input_type']}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_read_text_data():
    """Test 4: Read/retrieve text data from MongoDB"""
    print("\n" + "="*60)
    print("TEST 4: Reading Text Data")
    print("="*60)
    
    try:
        # Query for text-only records
        text_records = collection.find({
            "user_id": "test_user_text",
            "input_type": "text"
        }).limit(5)
        
        records = []
        for record in text_records:
            record_dict = dict(record)
            if "_id" in record_dict:
                record_dict["_id"] = str(record_dict["_id"])
            records.append(record_dict)
        
        if records:
            print(f"✅ SUCCESS: Retrieved {len(records)} text record(s)")
            for i, rec in enumerate(records, 1):
                print(f"\n   Record {i}:")
                print(f"   - ID: {rec.get('_id', 'N/A')}")
                print(f"   - User: {rec.get('user_id', 'N/A')}")
                print(f"   - Prompt: {rec.get('prompt', 'N/A')[:50]}...")
                print(f"   - CAD Code: {rec.get('cad_code', 'N/A')[:50]}...")
                print(f"   - Has image: {'image_data' in rec or rec.get('image_uri')}")
            return True
        else:
            print("⚠️  WARNING: No text records found")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_read_image_data():
    """Test 5: Read/retrieve image data from MongoDB"""
    print("\n" + "="*60)
    print("TEST 5: Reading Image Data")
    print("="*60)
    
    try:
        # Query for records with image data
        image_records = collection.find({
            "$or": [
                {"image_data": {"$exists": True}},
                {"image_uri": {"$ne": None}}
            ]
        }).limit(5)
        
        records = []
        for record in image_records:
            record_dict = dict(record)
            if "_id" in record_dict:
                record_dict["_id"] = str(record_dict["_id"])
            # Don't print full base64, just show it exists
            if "image_data" in record_dict:
                record_dict["image_data"] = f"[Base64 data: {len(record_dict['image_data'])} chars]"
            records.append(record_dict)
        
        if records:
            print(f"✅ SUCCESS: Retrieved {len(records)} image record(s)")
            for i, rec in enumerate(records, 1):
                print(f"\n   Record {i}:")
                print(f"   - ID: {rec.get('_id', 'N/A')}")
                print(f"   - User: {rec.get('user_id', 'N/A')}")
                print(f"   - Image URI: {rec.get('image_uri', 'N/A')}")
                print(f"   - Has image_data: {'image_data' in rec}")
                if 'image_data' in rec and isinstance(rec['image_data'], str) and '[Base64' in rec['image_data']:
                    print(f"   - {rec['image_data']}")
            return True
        else:
            print("⚠️  WARNING: No image records found")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_query_by_user():
    """Test 6: Query records by user_id"""
    print("\n" + "="*60)
    print("TEST 6: Querying by User ID")
    print("="*60)
    
    try:
        test_users = ["test_user_text", "test_user_image", "test_user_both"]
        
        for user_id in test_users:
            count = collection.count_documents({"user_id": user_id})
            print(f"   - {user_id}: {count} record(s)")
        
        print("✅ SUCCESS: User queries working")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_query_by_input_type():
    """Test 7: Query records by input_type"""
    print("\n" + "="*60)
    print("TEST 7: Querying by Input Type")
    print("="*60)
    
    try:
        input_types = ["text", "image", "both"]
        
        for input_type in input_types:
            count = collection.count_documents({"input_type": input_type})
            print(f"   - {input_type}: {count} record(s)")
        
        print("✅ SUCCESS: Input type queries working")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_update_record():
    """Test 8: Update an existing record"""
    print("\n" + "="*60)
    print("TEST 8: Updating a Record")
    print("="*60)
    
    try:
        # Find a test record to update
        test_record = collection.find_one({"user_id": "test_user_text"})
        
        if test_record:
            # Update the CAD code
            new_cad_code = "cube = Part.makeBox(10, 10, 10)\n# Updated code\nPart.show(cube)"
            collection.update_one(
                {"_id": test_record["_id"]},
                {"$set": {
                    "cad_code": new_cad_code,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # Verify update
            updated = collection.find_one({"_id": test_record["_id"]})
            if updated and updated["cad_code"] == new_cad_code:
                print("✅ SUCCESS: Record updated successfully")
                print(f"   - Updated CAD code: {new_cad_code[:50]}...")
                return True
            else:
                print("❌ FAILED: Update verification failed")
                return False
        else:
            print("⚠️  WARNING: No test record found to update")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_delete_test_records():
    """Test 9: Clean up test records (optional)"""
    print("\n" + "="*60)
    print("TEST 9: Cleanup (Deleting Test Records)")
    print("="*60)
    
    try:
        test_users = ["test_user_text", "test_user_image", "test_user_both"]
        total_deleted = 0
        
        for user_id in test_users:
            result = collection.delete_many({"user_id": user_id})
            deleted = result.deleted_count
            total_deleted += deleted
            if deleted > 0:
                print(f"   - Deleted {deleted} record(s) for {user_id}")
        
        if total_deleted > 0:
            print(f"✅ SUCCESS: Deleted {total_deleted} test record(s)")
        else:
            print("⚠️  No test records to delete")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_get_history_function():
    """Test 10: Test the get_history() function"""
    print("\n" + "="*60)
    print("TEST 10: Testing get_history() Function")
    print("="*60)
    
    try:
        # Test without user filter
        all_records = get_history(limit=5)
        print(f"✅ Retrieved {len(all_records)} record(s) (no filter)")
        
        # Test with user filter
        user_records = get_history(limit=5, user_id="default")
        print(f"✅ Retrieved {len(user_records)} record(s) for user 'default'")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_get_history_images_function():
    """Test 11: Test the get_history_images() function"""
    print("\n" + "="*60)
    print("TEST 11: Testing get_history_images() Function")
    print("="*60)
    
    try:
        image_records = get_history_images(limit=5)
        print(f"✅ Retrieved {len(image_records)} image record(s)")
        
        if image_records:
            print(f"   - First record has image_uri: {image_records[0].get('image_uri', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def run_all_tests(cleanup=False):
    """Run all tests"""
    print("\n" + "="*60)
    print("MONGODB CRUD TEST SUITE")
    print("Testing Text and Image Data Operations")
    print("="*60)
    
    results = {}
    
    # Write tests
    results["write_text"] = test_write_text_data()
    results["write_image"] = test_write_image_data()
    results["write_both"] = test_write_both_text_and_image()
    
    # Read tests
    results["read_text"] = test_read_text_data()
    results["read_image"] = test_read_image_data()
    
    # Query tests
    results["query_user"] = test_query_by_user()
    results["query_type"] = test_query_by_input_type()
    
    # Update test
    results["update"] = test_update_record()
    
    # Function tests
    results["get_history"] = test_get_history_function()
    results["get_images"] = test_get_history_images_function()
    
    # Cleanup (optional)
    if cleanup:
        results["cleanup"] = test_delete_test_records()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return results

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Show connection info
    mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017")
    mongo_db = os.getenv("MONGO_DB", "cad_coder")
    
    if "@" in mongo_uri:
        masked_uri = mongo_uri.split("@")[0].split("://")[0] + "://****@" + mongo_uri.split("@")[1].split("/")[0]
    else:
        masked_uri = mongo_uri
    
    print(f"\nMongoDB Connection: {masked_uri}")
    print(f"Database: {mongo_db}")
    print(f"Collection: history")
    
    # Run tests (set cleanup=True to delete test records after)
    run_all_tests(cleanup=False)

