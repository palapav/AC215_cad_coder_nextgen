#!/usr/bin/env python3
"""
Test script for ML workflow components.
Demonstrates validation, GCP trigger, and deployment functionality.
"""

import json
import sys
from pathlib import Path

# Add ml_workflow to path
sys.path.insert(0, str(Path(__file__).parent))

from validation import ModelValidator
from gcp_trigger_mock import GCPTriggerMock, TriggerType
from deployment import ModelDeployment
from workflow_integration import WorkflowIntegration


def test_validation():
    """Test model validation with sample results."""
    print("="*60)
    print("Testing Model Validation")
    print("="*60)
    
    validator = ModelValidator()
    
    # Test with passing results (from actual evaluation)
    passing_results = {
        "Best of N": {
            "Valid Sample Rate (%)": 96.97,
            "Mean IOU": 0.563,
            "Median IOU": 0.617,
            "Mean IOU (Adjusted)": 0.546
        },
        "Error Analysis": {
            "Failed Gen (%)": 1.76
        }
    }
    
    print("\n✅ Testing with PASSING results:")
    is_valid, details = validator.validate_from_dict(passing_results)
    print(f"Validation Result: {'PASS' if is_valid else 'FAIL'}")
    print(json.dumps(details, indent=2))
    
    # Test with failing results
    failing_results = {
        "Best of N": {
            "Valid Sample Rate (%)": 90.0,  # Below threshold
            "Mean IOU": 0.40,  # Below threshold
            "Median IOU": 0.45,  # Below threshold
            "Mean IOU (Adjusted)": 0.36
        },
        "Error Analysis": {
            "Failed Gen (%)": 10.0  # Above threshold
        }
    }
    
    print("\n❌ Testing with FAILING results:")
    is_valid, details = validator.validate_from_dict(failing_results)
    print(f"Validation Result: {'PASS' if is_valid else 'FAIL'}")
    print(json.dumps(details, indent=2))


def test_gcp_trigger():
    """Test GCP trigger mock."""
    print("\n" + "="*60)
    print("Testing GCP Trigger Mock")
    print("="*60)
    
    trigger_mock = GCPTriggerMock()
    
    # Test different trigger types
    print("\n1. New Data Trigger:")
    event1 = trigger_mock.trigger_from_new_data(
        data_path="gs://cad-coder-nextgen-data/new_training_data/",
        data_version="v3"
    )
    print(json.dumps(event1, indent=2))
    
    print("\n2. Code Update Trigger:")
    event2 = trigger_mock.trigger_from_code_update(
        commit_hash="abc123def456",
        branch="main",
        changed_files=["src/model_finetuning/centralized_train.py"]
    )
    print(json.dumps(event2, indent=2))
    
    print("\n3. Scheduled Trigger:")
    event3 = trigger_mock.trigger_scheduled(schedule_name="daily_retraining")
    print(json.dumps(event3, indent=2))
    
    print("\n4. Trigger History:")
    history = trigger_mock.get_trigger_history()
    for event in history:
        print(f"  - {event['workflow_id']}: {event['trigger_type']}")


def test_deployment():
    """Test deployment service."""
    print("\n" + "="*60)
    print("Testing Deployment Service")
    print("="*60)
    
    deployment = ModelDeployment()
    
    # Mock validation results
    validation_results = {
        "passed": True,
        "checks": {
            "valid_sample_rate": {"value": 0.9697, "threshold": 0.95, "passed": True},
            "mean_iou": {"value": 0.563, "threshold": 0.50, "passed": True}
        }
    }
    
    print("\n1. Modal Deployment:")
    modal_result = deployment.deploy_to_modal(
        model_path="/path/to/final_model.pt",
        workflow_id="workflow_test_001"
    )
    print(json.dumps(modal_result, indent=2))
    
    print("\n2. GCP Deployment (Mock):")
    gcp_result = deployment.deploy_to_gcp_mock(
        model_path="/path/to/final_model.pt",
        workflow_id="workflow_test_001"
    )
    print(json.dumps(gcp_result, indent=2))
    
    print("\n3. Combined Deployment:")
    combined_result = deployment.deploy_validated_model(
        model_path="/path/to/final_model.pt",
        validation_results=validation_results,
        workflow_id="workflow_test_001",
        deploy_to_modal=True,
        deploy_to_gcp=True
    )
    print(json.dumps(combined_result, indent=2))


def test_integration():
    """Test workflow integration."""
    print("\n" + "="*60)
    print("Testing Workflow Integration")
    print("="*60)
    
    integration = WorkflowIntegration()
    
    print("\n1. New Data Trigger Integration:")
    result1 = integration.trigger_workflow_from_gcp(
        trigger_type=TriggerType.NEW_DATA,
        metadata={
            "data_path": "gs://bucket/new_data/",
            "data_version": "v3"
        }
    )
    print(json.dumps(result1, indent=2))
    
    print("\n2. Code Update Trigger Integration:")
    result2 = integration.trigger_workflow_from_gcp(
        trigger_type=TriggerType.CODE_UPDATE,
        metadata={
            "commit_hash": "abc123",
            "branch": "main"
        }
    )
    print(json.dumps(result2, indent=2))


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ML Workflow Component Tests")
    print("="*60)
    
    try:
        test_validation()
        test_gcp_trigger()
        test_deployment()
        test_integration()
        
        print("\n" + "="*60)
        print("✅ All tests completed successfully!")
        print("="*60)
        print("\nNext steps:")
        print("1. Deploy Modal workflow: modal deploy src/ml_workflow/modal_workflow.py")
        print("2. Run full workflow: modal run src/ml_workflow/modal_workflow.py")
        print("3. In production, replace mocks with actual GCP services")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

