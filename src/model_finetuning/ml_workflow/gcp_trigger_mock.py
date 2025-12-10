#!/usr/bin/env python3
"""
Mock GCP trigger service for automated retraining.
Simulates GCP Pub/Sub or Cloud Functions triggering ML workflow.
"""

import json
import logging
import os
from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Counter for ensuring unique workflow IDs within the same second
_workflow_counter = 0


class TriggerType(Enum):
    """Types of triggers for ML workflow."""
    NEW_DATA = "new_data"
    CODE_UPDATE = "code_update"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


class GCPTriggerMock:
    """
    Mock GCP trigger service that simulates Pub/Sub or Cloud Functions.
    In production, this would be replaced with actual GCP Pub/Sub subscriber
    or Cloud Functions HTTP endpoint.
    """
    
    def __init__(self, project_id: str = "cad-coder-nextgen", region: str = "us-central1"):
        self.project_id = project_id
        self.region = region
        self.trigger_history: List[Dict] = []
        logger.info(f"Initialized GCP Trigger Mock (project: {project_id}, region: {region})")
    
    def trigger_retraining(
        self,
        trigger_type: TriggerType = TriggerType.MANUAL,
        metadata: Optional[Dict] = None,
        workflow_id: Optional[str] = None
    ) -> Dict:
        """
        Simulate triggering ML workflow retraining.
        
        Args:
            trigger_type: Type of trigger (new_data, code_update, scheduled, manual)
            metadata: Additional metadata about the trigger
            workflow_id: Optional workflow ID for tracking
            
        Returns:
            Dictionary with trigger information
        """
        if workflow_id is None:
            global _workflow_counter
            _workflow_counter += 1
            # Use microseconds and counter to ensure uniqueness
            now = datetime.now()
            workflow_id = f"workflow_{now.strftime('%Y%m%d_%H%M%S')}_{now.microsecond:06d}_{_workflow_counter:04d}"
        
        trigger_event = {
            "workflow_id": workflow_id,
            "trigger_type": trigger_type.value,
            "timestamp": datetime.now().isoformat(),
            "project_id": self.project_id,
            "region": self.region,
            "metadata": metadata or {},
            "status": "triggered"
        }
        
        self.trigger_history.append(trigger_event)
        
        logger.info(f"🚀 Triggered ML workflow: {workflow_id} (type: {trigger_type.value})")
        
        return trigger_event
    
    def trigger_from_new_data(
        self,
        data_path: str,
        data_version: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> Dict:
        """
        Simulate trigger from new data available in GCS.
        
        Args:
            data_path: GCS path to new data (e.g., gs://bucket/new_data/)
            data_version: Optional data version identifier
            workflow_id: Optional workflow ID
            
        Returns:
            Dictionary with trigger information
        """
        metadata = {
            "data_path": data_path,
            "data_version": data_version,
            "source": "gcs"
        }
        
        return self.trigger_retraining(
            trigger_type=TriggerType.NEW_DATA,
            metadata=metadata,
            workflow_id=workflow_id
        )
    
    def trigger_from_code_update(
        self,
        commit_hash: str,
        branch: str = "main",
        changed_files: Optional[List[str]] = None,
        workflow_id: Optional[str] = None
    ) -> Dict:
        """
        Simulate trigger from codebase update (e.g., GitHub webhook).
        
        Args:
            commit_hash: Git commit hash
            branch: Git branch name
            changed_files: List of changed files
            workflow_id: Optional workflow ID
            
        Returns:
            Dictionary with trigger information
        """
        metadata = {
            "commit_hash": commit_hash,
            "branch": branch,
            "changed_files": changed_files or [],
            "source": "github"
        }
        
        return self.trigger_retraining(
            trigger_type=TriggerType.CODE_UPDATE,
            metadata=metadata,
            workflow_id=workflow_id
        )
    
    def trigger_scheduled(
        self,
        schedule_name: str = "daily_retraining",
        workflow_id: Optional[str] = None
    ) -> Dict:
        """
        Simulate scheduled trigger (e.g., Cloud Scheduler).
        
        Args:
            schedule_name: Name of the schedule
            workflow_id: Optional workflow ID
            
        Returns:
            Dictionary with trigger information
        """
        metadata = {
            "schedule_name": schedule_name,
            "source": "cloud_scheduler"
        }
        
        return self.trigger_retraining(
            trigger_type=TriggerType.SCHEDULED,
            metadata=metadata,
            workflow_id=workflow_id
        )
    
    def get_trigger_history(self, limit: int = 10) -> List[Dict]:
        """Get recent trigger history."""
        return self.trigger_history[-limit:]
    
    def simulate_pubsub_message(self, message_data: Dict) -> Dict:
        """
        Simulate receiving a Pub/Sub message.
        In production, this would be handled by a Pub/Sub subscriber.
        
        Args:
            message_data: Dictionary containing message data
            
        Returns:
            Trigger event dictionary
        """
        # Parse message data (simulating Pub/Sub message format)
        trigger_type_str = message_data.get("trigger_type", "manual")
        try:
            trigger_type = TriggerType(trigger_type_str)
        except ValueError:
            trigger_type = TriggerType.MANUAL
        
        return self.trigger_retraining(
            trigger_type=trigger_type,
            metadata=message_data.get("metadata", {}),
            workflow_id=message_data.get("workflow_id")
        )


# HTTP endpoint simulation (for Cloud Functions)
def handle_http_trigger(request_data: Dict) -> Dict:
    """
    Simulate Cloud Functions HTTP endpoint handler.
    In production, this would be deployed as a Cloud Function.
    
    Args:
        request_data: HTTP request data (JSON body)
        
    Returns:
        Response dictionary
    """
    trigger_mock = GCPTriggerMock()
    
    trigger_type_str = request_data.get("trigger_type", "manual")
    try:
        trigger_type = TriggerType(trigger_type_str)
    except ValueError:
        trigger_type = TriggerType.MANUAL
    
    trigger_event = trigger_mock.trigger_retraining(
        trigger_type=trigger_type,
        metadata=request_data.get("metadata", {}),
        workflow_id=request_data.get("workflow_id")
    )
    
    return {
        "status": "success",
        "message": "ML workflow triggered",
        "trigger_event": trigger_event
    }


if __name__ == "__main__":
    # Test the mock trigger service
    trigger_mock = GCPTriggerMock()
    
    # Test different trigger types
    print("Testing GCP Trigger Mock...")
    
    # 1. New data trigger
    event1 = trigger_mock.trigger_from_new_data(
        data_path="gs://cad-coder-nextgen-data/new_training_data/",
        data_version="v3"
    )
    print(f"\n1. New Data Trigger:\n{json.dumps(event1, indent=2)}")
    
    # 2. Code update trigger
    event2 = trigger_mock.trigger_from_code_update(
        commit_hash="abc123def456",
        branch="main",
        changed_files=["src/model_finetuning/centralized_train.py"]
    )
    print(f"\n2. Code Update Trigger:\n{json.dumps(event2, indent=2)}")
    
    # 3. Scheduled trigger
    event3 = trigger_mock.trigger_scheduled(schedule_name="daily_retraining")
    print(f"\n3. Scheduled Trigger:\n{json.dumps(event3, indent=2)}")
    
    # 4. Pub/Sub message simulation
    pubsub_message = {
        "trigger_type": "new_data",
        "metadata": {
            "data_path": "gs://bucket/new_data/",
            "data_version": "v4"
        }
    }
    event4 = trigger_mock.simulate_pubsub_message(pubsub_message)
    print(f"\n4. Pub/Sub Message Trigger:\n{json.dumps(event4, indent=2)}")
    
    # Get history
    history = trigger_mock.get_trigger_history()
    print(f"\nTrigger History ({len(history)} events):")
    for event in history:
        print(f"  - {event['workflow_id']}: {event['trigger_type']} at {event['timestamp']}")

