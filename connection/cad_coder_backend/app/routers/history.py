from fastapi import APIRouter, Query, Body
from app.services.db_service import get_history, add_record, collection
from app.services.rag_service import retrieve_similar_context

router = APIRouter(prefix="/history", tags=["History"])

@router.get("/")
async def get_history_records(limit: int = Query(10, ge=1, le=100)):
    """
    Returns the latest generation history.
    """
    records = get_history(limit=limit)
    return {"count": len(records), "records": records}

@router.post("/context")
async def get_rag_context(data: dict = Body(...)):
    """
    Retrieves similar prompts or context from RAG store for a given user prompt.
    """
    prompt = data.get("prompt", "")
    if not prompt:
        return {"context": [], "message": "Empty prompt received."}

    context = retrieve_similar_context(prompt)
    return {"prompt": prompt, "context": context}

@router.get("/test-records")
async def get_test_records():
    """
    Get all test records (for verification).
    """
    test_users = ["test_user_text", "test_user_image", "test_user_both"]
    records = []
    for user_id in test_users:
        user_records = get_history(limit=10, user_id=user_id)
        records.extend(user_records)
    return {"count": len(records), "records": records}

@router.get("/test-images")
async def get_test_images():
    """
    Get all test records with image data.
    """
    records = collection.find({
        "$or": [
            {"image_data": {"$exists": True}},
            {"user_id": {"$in": ["test_user_image", "test_user_both"]}}
        ]
    }).limit(10)
    
    results = []
    for item in records:
        item_dict = dict(item)
        if "_id" in item_dict:
            item_dict["_id"] = str(item_dict["_id"])
        # Don't return full base64 in API response (too large)
        if "image_data" in item_dict:
            item_dict["image_data"] = f"[Base64: {len(item_dict['image_data'])} chars]"
        results.append(item_dict)
    
    return {"count": len(results), "records": results}

@router.post("/add-dummy-data")
async def add_dummy_data_endpoint():
    """
    Add sample dummy data to MongoDB for testing purposes.
    """
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
    
    added_count = 0
    errors = []
    
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
        except Exception as e:
            errors.append(f"Failed to add '{record['prompt'][:30]}...': {str(e)}")
    
    return {
        "message": f"Added {added_count} dummy records to MongoDB",
        "added_count": added_count,
        "errors": errors if errors else None
    }
