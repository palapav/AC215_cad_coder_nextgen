#!/usr/bin/env python3
"""
Integration script that connects GCP trigger mock to Modal Labs workflow.
This simulates the production setup where GCP triggers would call Modal workflow.
"""

import json
import logging
import os
from typing import Dict, Optional
from datetime import datetime

from gcp_trigger_mock import GCPTriggerMock, TriggerType
from config import GCP_MOCK_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowIntegration:
    """
    Integrates GCP trigger mock with Modal Labs workflow.
    In production, this would be a Cloud Function or Pub/Sub subscriber.
    """
    
    def __init__(self):
        self.trigger_mock = GCPTriggerMock(
            project_id=GCP_MOCK_CONFIG["project_id"],
            region=GCP_MOCK_CONFIG["region"]
        )
        logger.info("Initialized Workflow Integration")
    
    def trigger_workflow_from_gcp(
        self,
        trigger_type: TriggerType,
        metadata: Optional[Dict] = None,
        workflow_id: Optional[str] = None
    ) -> Dict:
        """
        Trigger Modal Labs workflow from GCP trigger event.
        
        Args:
            trigger_type: Type of trigger
            metadata: Additional metadata
            workflow_id: Optional workflow ID
            
        Returns:
            Dictionary with trigger and workflow information
        """
        # Step 1: Receive trigger from GCP (mocked)
        trigger_event = self.trigger_mock.trigger_retraining(
            trigger_type=trigger_type,
            metadata=metadata,
            workflow_id=workflow_id
        )
        
        logger.info(f"📥 Received GCP trigger: {trigger_event['workflow_id']}")
        
        # Step 2: Call Modal Labs workflow
        # In production, this would use Modal client to invoke the workflow
        # For now, we'll return the trigger event with instructions
        
        workflow_info = {
            "trigger_event": trigger_event,
            "modal_workflow": {
                "app_name": "cad-coder-ml-workflow",
                "function": "run_full_workflow",
                "status": "triggered",
                "instruction": "Run: modal run src/model_finetuning/modal_workflow.py --workflow-id {workflow_id}".format(
                    workflow_id=trigger_event["workflow_id"]
                )
            },
            "next_steps": [
                "1. GCP trigger received and validated",
                "2. Modal workflow should be invoked with workflow_id",
                "3. Workflow will run: preprocessing -> training -> evaluation -> validation -> deployment"
            ]
        }
        
        logger.info(f"🚀 Modal workflow triggered: {trigger_event['workflow_id']}")
        
        return workflow_info
    
    def handle_pubsub_message(self, message_data: Dict) -> Dict:
        """
        Handle Pub/Sub message and trigger workflow.
        In production, this would be a Cloud Function triggered by Pub/Sub.
        
        Args:
            message_data: Pub/Sub message data
            
        Returns:
            Workflow trigger information
        """
        # Parse message
        trigger_type_str = message_data.get("trigger_type", "manual")
        try:
            trigger_type = TriggerType(trigger_type_str)
        except ValueError:
            trigger_type = TriggerType.MANUAL
        
        return self.trigger_workflow_from_gcp(
            trigger_type=trigger_type,
            metadata=message_data.get("metadata", {}),
            workflow_id=message_data.get("workflow_id")
        )
    
    def handle_http_request(self, request_data: Dict) -> Dict:
        """
        Handle HTTP request (e.g., from Cloud Scheduler or manual trigger).
        In production, this would be a Cloud Function HTTP endpoint.
        
        Args:
            request_data: HTTP request data
            
        Returns:
            Workflow trigger information
        """
        trigger_type_str = request_data.get("trigger_type", "manual")
        try:
            trigger_type = TriggerType(trigger_type_str)
        except ValueError:
            trigger_type = TriggerType.MANUAL
        
        return self.trigger_workflow_from_gcp(
            trigger_type=trigger_type,
            metadata=request_data.get("metadata", {}),
            workflow_id=request_data.get("workflow_id")
        )


def simulate_gcp_to_modal_workflow():
    """
    Simulate the complete flow from GCP trigger to Modal workflow.
    This demonstrates how the integration works.
    """
    integration = WorkflowIntegration()
    
    print("="*60)
    print("GCP to Modal Labs Workflow Integration Demo")
    print("="*60)
    
    # Scenario 1: New data trigger
    print("\n📥 Scenario 1: New Data Available in GCS")
    print("-" * 60)
    result1 = integration.trigger_workflow_from_gcp(
        trigger_type=TriggerType.NEW_DATA,
        metadata={
            "data_path": "gs://cad-coder-nextgen-data/new_training_data/",
            "data_version": "v3"
        }
    )
    print(json.dumps(result1, indent=2))
    
    # Scenario 2: Code update trigger
    print("\n📥 Scenario 2: Code Update (GitHub Webhook)")
    print("-" * 60)
    result2 = integration.trigger_workflow_from_gcp(
        trigger_type=TriggerType.CODE_UPDATE,
        metadata={
            "commit_hash": "abc123def456",
            "branch": "main",
            "changed_files": ["src/model_finetuning/centralized_train.py"]
        }
    )
    print(json.dumps(result2, indent=2))
    
    # Scenario 3: Scheduled trigger
    print("\n📥 Scenario 3: Scheduled Retraining (Cloud Scheduler)")
    print("-" * 60)
    result3 = integration.trigger_workflow_from_gcp(
        trigger_type=TriggerType.SCHEDULED,
        metadata={
            "schedule_name": "daily_retraining"
        }
    )
    print(json.dumps(result3, indent=2))
    
    print("\n" + "="*60)
    print("✅ Integration demo completed")
    print("="*60)
    print("\nNext steps:")
    print("1. Deploy Modal workflow: modal deploy src/model_finetuning/modal_workflow.py")
    print("2. In production, replace mock with actual GCP Pub/Sub subscriber or Cloud Function")
    print("3. Set up Cloud Scheduler for scheduled retraining")
    print("4. Configure GCS notifications to trigger on new data")


if __name__ == "__main__":
    simulate_gcp_to_modal_workflow()

