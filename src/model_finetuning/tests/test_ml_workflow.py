"""Unit tests for ML workflow components."""
import pytest
import json
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add ml_workflow to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml_workflow'))


# ============================================================================
# Config Tests
# ============================================================================
class TestConfig:
    """Test ML workflow configuration."""

    def test_performance_thresholds_exist(self):
        """Test that performance thresholds are defined."""
        from config import PERFORMANCE_THRESHOLDS
        
        assert "min_valid_sample_rate" in PERFORMANCE_THRESHOLDS
        assert "min_mean_iou" in PERFORMANCE_THRESHOLDS
        assert "min_median_iou" in PERFORMANCE_THRESHOLDS
        assert "max_failed_generation_rate" in PERFORMANCE_THRESHOLDS

    def test_training_config_exist(self):
        """Test that training config is defined."""
        from config import TRAINING_CONFIG
        
        assert "base_model" in TRAINING_CONFIG
        assert "num_epochs" in TRAINING_CONFIG
        assert "batch_size" in TRAINING_CONFIG
        assert "learning_rate" in TRAINING_CONFIG

    def test_evaluation_config_exist(self):
        """Test that evaluation config is defined."""
        from config import EVALUATION_CONFIG
        
        assert "n_samples" in EVALUATION_CONFIG
        assert "n_workers" in EVALUATION_CONFIG
        assert "timeout" in EVALUATION_CONFIG

    def test_workflow_status_values(self):
        """Test workflow status values."""
        from config import WORKFLOW_STATUS
        
        assert WORKFLOW_STATUS["PENDING"] == "pending"
        assert WORKFLOW_STATUS["COMPLETED"] == "completed"
        assert WORKFLOW_STATUS["FAILED"] == "failed"
        assert WORKFLOW_STATUS["REJECTED"] == "rejected"

    def test_data_paths_defined(self):
        """Test that data paths are defined."""
        from config import DATA_PATHS
        
        assert "client1" in DATA_PATHS
        assert "client2" in DATA_PATHS
        assert "combined" in DATA_PATHS
        assert "validation" in DATA_PATHS
        assert "test" in DATA_PATHS


# ============================================================================
# Validation Tests
# ============================================================================
class TestModelValidator:
    """Test model validation functionality."""

    def test_validator_initialization(self):
        """Test validator initializes with default thresholds."""
        from validation import ModelValidator
        
        validator = ModelValidator()
        assert validator.thresholds is not None
        assert "min_valid_sample_rate" in validator.thresholds

    def test_validator_custom_thresholds(self):
        """Test validator with custom thresholds."""
        from validation import ModelValidator
        
        custom_thresholds = {
            "min_valid_sample_rate": 0.90,
            "min_mean_iou": 0.40,
            "min_median_iou": 0.45,
            "max_failed_generation_rate": 0.10
        }
        
        validator = ModelValidator(thresholds=custom_thresholds)
        assert validator.thresholds["min_valid_sample_rate"] == 0.90

    def test_validate_passing_results(self):
        """Test validation with passing results."""
        from validation import ModelValidator
        
        validator = ModelValidator()
        
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
        
        is_valid, details = validator.validate_from_dict(passing_results)
        
        assert is_valid is True
        assert details["passed"] is True
        assert "checks" in details
        assert all(check["passed"] for check in details["checks"].values())

    def test_validate_failing_results(self):
        """Test validation with failing results."""
        from validation import ModelValidator
        
        validator = ModelValidator()
        
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
        
        is_valid, details = validator.validate_from_dict(failing_results)
        
        assert is_valid is False
        assert details["passed"] is False
        assert "failed_checks" in details
        assert len(details["failed_checks"]) > 0

    def test_validate_partial_failure(self):
        """Test validation with partial failure."""
        from validation import ModelValidator
        
        validator = ModelValidator()
        
        partial_results = {
            "Best of N": {
                "Valid Sample Rate (%)": 96.0,  # Passing
                "Mean IOU": 0.55,  # Passing
                "Median IOU": 0.45,  # Failing
                "Mean IOU (Adjusted)": 0.50
            },
            "Error Analysis": {
                "Failed Gen (%)": 2.0  # Passing
            }
        }
        
        is_valid, details = validator.validate_from_dict(partial_results)
        
        assert is_valid is False
        assert "median_iou" in details.get("failed_checks", [])

    def test_validate_from_file_not_found(self, tmp_path):
        """Test validation with non-existent file."""
        from validation import ModelValidator
        
        validator = ModelValidator()
        
        is_valid, details = validator.validate_evaluation_results(
            str(tmp_path / "nonexistent.json")
        )
        
        assert is_valid is False
        assert "error" in details

    def test_validate_from_invalid_json(self, tmp_path):
        """Test validation with invalid JSON file."""
        from validation import ModelValidator
        
        validator = ModelValidator()
        
        # Create invalid JSON file
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json {{{")
        
        is_valid, details = validator.validate_evaluation_results(str(invalid_file))
        
        assert is_valid is False
        assert "error" in details

    def test_validate_from_valid_file(self, tmp_path):
        """Test validation with valid JSON file."""
        from validation import ModelValidator
        
        validator = ModelValidator()
        
        # Create valid JSON file
        valid_results = {
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
        
        valid_file = tmp_path / "valid.json"
        valid_file.write_text(json.dumps(valid_results))
        
        is_valid, details = validator.validate_evaluation_results(str(valid_file))
        
        assert is_valid is True


# ============================================================================
# GCP Trigger Mock Tests
# ============================================================================
class TestGCPTriggerMock:
    """Test GCP trigger mock functionality."""

    def test_trigger_initialization(self):
        """Test trigger mock initializes correctly."""
        from gcp_trigger_mock import GCPTriggerMock
        
        trigger = GCPTriggerMock(project_id="test-project", region="us-central1")
        
        assert trigger.project_id == "test-project"
        assert trigger.region == "us-central1"
        assert trigger.trigger_history == []

    def test_trigger_retraining_manual(self):
        """Test manual trigger."""
        from gcp_trigger_mock import GCPTriggerMock, TriggerType
        
        trigger = GCPTriggerMock()
        event = trigger.trigger_retraining(trigger_type=TriggerType.MANUAL)
        
        assert "workflow_id" in event
        assert event["trigger_type"] == "manual"
        assert event["status"] == "triggered"

    def test_trigger_from_new_data(self):
        """Test new data trigger."""
        from gcp_trigger_mock import GCPTriggerMock
        
        trigger = GCPTriggerMock()
        event = trigger.trigger_from_new_data(
            data_path="gs://bucket/data/",
            data_version="v2"
        )
        
        assert event["trigger_type"] == "new_data"
        assert event["metadata"]["data_path"] == "gs://bucket/data/"
        assert event["metadata"]["data_version"] == "v2"

    def test_trigger_from_code_update(self):
        """Test code update trigger."""
        from gcp_trigger_mock import GCPTriggerMock
        
        trigger = GCPTriggerMock()
        event = trigger.trigger_from_code_update(
            commit_hash="abc123",
            branch="main",
            changed_files=["train.py"]
        )
        
        assert event["trigger_type"] == "code_update"
        assert event["metadata"]["commit_hash"] == "abc123"
        assert event["metadata"]["branch"] == "main"

    def test_trigger_scheduled(self):
        """Test scheduled trigger."""
        from gcp_trigger_mock import GCPTriggerMock
        
        trigger = GCPTriggerMock()
        event = trigger.trigger_scheduled(schedule_name="daily")
        
        assert event["trigger_type"] == "scheduled"
        assert event["metadata"]["schedule_name"] == "daily"

    def test_trigger_history(self):
        """Test trigger history tracking."""
        from gcp_trigger_mock import GCPTriggerMock, TriggerType
        
        trigger = GCPTriggerMock()
        trigger.trigger_retraining(trigger_type=TriggerType.MANUAL)
        trigger.trigger_retraining(trigger_type=TriggerType.SCHEDULED)
        
        history = trigger.get_trigger_history()
        
        assert len(history) == 2
        assert history[0]["trigger_type"] == "manual"
        assert history[1]["trigger_type"] == "scheduled"

    def test_simulate_pubsub_message(self):
        """Test Pub/Sub message simulation."""
        from gcp_trigger_mock import GCPTriggerMock
        
        trigger = GCPTriggerMock()
        message = {
            "trigger_type": "new_data",
            "metadata": {"data_path": "gs://bucket/data/"}
        }
        
        event = trigger.simulate_pubsub_message(message)
        
        assert event["trigger_type"] == "new_data"

    def test_handle_http_trigger(self):
        """Test HTTP trigger handler."""
        from gcp_trigger_mock import handle_http_trigger
        
        request_data = {
            "trigger_type": "manual",
            "metadata": {"reason": "test"}
        }
        
        response = handle_http_trigger(request_data)
        
        assert response["status"] == "success"
        assert "trigger_event" in response


# ============================================================================
# Deployment Tests
# ============================================================================
class TestModelDeployment:
    """Test model deployment functionality."""

    def test_deployment_initialization(self):
        """Test deployment service initializes correctly."""
        from deployment import ModelDeployment
        
        deployment = ModelDeployment(
            modal_app_name="test-app",
            gcp_project_id="test-project"
        )
        
        assert deployment.modal_app_name == "test-app"
        assert deployment.gcp_project_id == "test-project"
        assert deployment.deployment_history == []

    def test_deploy_to_modal(self):
        """Test Modal deployment."""
        from deployment import ModelDeployment
        
        deployment = ModelDeployment()
        result = deployment.deploy_to_modal(
            model_path="/path/to/model.pt",
            workflow_id="test-workflow"
        )
        
        assert result["platform"] == "modal"
        assert result["status"] == "deployed"
        assert "model_version" in result
        assert "timestamp" in result

    def test_deploy_to_gcp_mock(self):
        """Test GCP mock deployment."""
        from deployment import ModelDeployment
        
        deployment = ModelDeployment()
        result = deployment.deploy_to_gcp_mock(
            model_path="/path/to/model.pt",
            workflow_id="test-workflow"
        )
        
        assert result["platform"] == "gcp"
        assert result["status"] == "deployed"
        assert "endpoint_name" in result

    def test_deploy_validated_model(self):
        """Test combined deployment."""
        from deployment import ModelDeployment
        
        deployment = ModelDeployment()
        validation_results = {
            "passed": True,
            "checks": {"mean_iou": {"passed": True}}
        }
        
        result = deployment.deploy_validated_model(
            model_path="/path/to/model.pt",
            validation_results=validation_results,
            workflow_id="test-workflow",
            deploy_to_modal=True,
            deploy_to_gcp=True
        )
        
        assert len(result["deployments"]) == 2
        assert "validation_results" in result

    def test_deployment_history(self):
        """Test deployment history tracking."""
        from deployment import ModelDeployment
        
        deployment = ModelDeployment()
        deployment.deploy_to_modal(
            model_path="/path/to/model.pt",
            workflow_id="workflow-1"
        )
        deployment.deploy_to_gcp_mock(
            model_path="/path/to/model.pt",
            workflow_id="workflow-2"
        )
        
        history = deployment.get_deployment_history()
        
        assert len(history) == 2


# ============================================================================
# Workflow Integration Tests
# ============================================================================
class TestWorkflowIntegration:
    """Test workflow integration functionality."""

    def test_integration_initialization(self):
        """Test workflow integration initializes correctly."""
        from workflow_integration import WorkflowIntegration
        
        integration = WorkflowIntegration()
        assert integration.trigger_mock is not None

    def test_trigger_workflow_from_gcp(self):
        """Test triggering workflow from GCP."""
        from workflow_integration import WorkflowIntegration
        from gcp_trigger_mock import TriggerType
        
        integration = WorkflowIntegration()
        result = integration.trigger_workflow_from_gcp(
            trigger_type=TriggerType.MANUAL,
            metadata={"test": "data"}
        )
        
        assert "trigger_event" in result
        assert "modal_workflow" in result
        assert "next_steps" in result

    def test_handle_pubsub_message(self):
        """Test handling Pub/Sub message."""
        from workflow_integration import WorkflowIntegration
        
        integration = WorkflowIntegration()
        message = {
            "trigger_type": "new_data",
            "metadata": {"data_path": "gs://bucket/data/"}
        }
        
        result = integration.handle_pubsub_message(message)
        
        assert "trigger_event" in result
        assert result["trigger_event"]["trigger_type"] == "new_data"

    def test_handle_http_request(self):
        """Test handling HTTP request."""
        from workflow_integration import WorkflowIntegration
        
        integration = WorkflowIntegration()
        request = {
            "trigger_type": "manual",
            "metadata": {}
        }
        
        result = integration.handle_http_request(request)
        
        assert "trigger_event" in result


# ============================================================================
# Orchestrator Tests
# ============================================================================
class TestWorkflowOrchestrator:
    """Test workflow orchestrator functionality."""

    def test_orchestrator_initialization(self):
        """Test orchestrator initializes correctly."""
        from orchestrator import WorkflowOrchestrator, TriggerType
        
        orchestrator = WorkflowOrchestrator(
            workflow_id="test-workflow",
            trigger_type=TriggerType.MANUAL,
            enable_validation=True,
            deploy_on_success=False
        )
        
        assert orchestrator.workflow_id == "test-workflow"
        assert orchestrator.trigger_type == TriggerType.MANUAL
        assert orchestrator.enable_validation is True
        assert orchestrator.deploy_on_success is False

    def test_orchestrator_run_without_deployment(self):
        """Test orchestrator run without deployment."""
        from orchestrator import WorkflowOrchestrator, TriggerType
        
        orchestrator = WorkflowOrchestrator(
            workflow_id="test-workflow",
            trigger_type=TriggerType.MANUAL,
            enable_validation=False,
            deploy_on_success=False
        )
        
        # Mock data availability
        with patch.object(orchestrator, '_check_data_available', return_value=False):
            results = orchestrator.run()
        
        assert "workflow_id" in results
        assert "status" in results
        assert "duration_seconds" in results

    def test_orchestrator_status_updates(self):
        """Test orchestrator status updates."""
        from orchestrator import WorkflowOrchestrator, TriggerType
        from config import WORKFLOW_STATUS
        
        orchestrator = WorkflowOrchestrator(
            workflow_id="test-workflow",
            trigger_type=TriggerType.MANUAL
        )
        
        assert orchestrator.status == WORKFLOW_STATUS["PENDING"]
        
        orchestrator._update_status(WORKFLOW_STATUS["TRAINING"])
        assert orchestrator.status == WORKFLOW_STATUS["TRAINING"]

    def test_trigger_type_enum(self):
        """Test TriggerType enum values."""
        from orchestrator import TriggerType
        
        assert TriggerType.SCHEDULED.value == "scheduled"
        assert TriggerType.NEW_DATA.value == "new_data"
        assert TriggerType.CODE_UPDATE.value == "code_update"
        assert TriggerType.MANUAL.value == "manual"

