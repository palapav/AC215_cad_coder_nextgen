"""
ML Workflow module for production-ready training pipeline.

This module provides the complete ML workflow for container segmentation,
including data preprocessing, model training, evaluation, validation, and deployment.
"""

from .workflow_integration import WorkflowIntegration
from .gcp_trigger_mock import GCPTriggerMock, TriggerType
from .validation import ModelValidator
from .deployment import ModelDeployment

__all__ = [
    "WorkflowIntegration",
    "GCPTriggerMock",
    "TriggerType",
    "ModelValidator",
    "ModelDeployment",
]

