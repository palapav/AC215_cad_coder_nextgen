# ML Workflow on Modal Labs

A production-ready ML workflow system for container segmentation that integrates data preprocessing, model training, evaluation, validation, and deployment. The workflow can be triggered automatically from GCP (mocked) and includes validation checks to ensure only models meeting performance thresholds are deployed.

## 📖 Documentation

- **[WORKFLOW_EXPLANATION.md](./WORKFLOW_EXPLANATION.md)** - Complete technical explanation of the workflow, rubric mapping, and detailed step-by-step breakdown

## Quick Start

### Prerequisites

```bash
pip install modal-client
modal token new  # Authenticate with Modal
```

### Run the Workflow

```bash
# Manual trigger
modal run src/ml_workflow/modal_workflow.py \
  --workflow-id test_001 \
  --trigger-type manual \
  --deploy-to-modal
```

## Overview

The workflow executes 5 sequential steps:

1. **Preprocessing** → Prepare container segmentation training data
2. **Training** → Fine-tune Qwen3-VL model on container segmentation task
3. **Evaluation** → Assess model performance on test dataset
4. **Validation** → Check if model meets deployment thresholds
5. **Deployment** → Deploy validated models (only if validation passes)

## Architecture

```
Trigger (GCP Mock/Manual)
    ↓
Modal Labs Workflow Orchestrator
    ↓
Preprocessing → Training → Evaluation → Validation → Deployment
```

## Key Features

✅ **Integrated Pipeline**: Preprocessing, training, and evaluation run sequentially  
✅ **Automated Triggers**: New data, code updates, scheduled, or manual triggers  
✅ **Validation Gating**: Only models meeting performance thresholds are deployed  
✅ **Production Ready**: Modular design with comprehensive error handling  

## Performance Thresholds

Models must meet all thresholds to be deployed:

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Valid Sample Rate | ≥ 95% | Percentage of generated code that executes |
| Mean IOU | ≥ 0.50 | Average Intersection over Union |
| Median IOU | ≥ 0.55 | Median Intersection over Union |
| Failed Generation Rate | ≤ 5% | Percentage of failed code generations |

## Usage Examples

### Manual Trigger

```bash
modal run src/ml_workflow/modal_workflow.py \
  --workflow-id container_seg_v1 \
  --trigger-type manual \
  --deploy-to-modal
```

### Python API

```python
from ml_workflow.workflow_integration import WorkflowIntegration
from ml_workflow.gcp_trigger_mock import TriggerType

integration = WorkflowIntegration()
result = integration.trigger_workflow_from_gcp(
    trigger_type=TriggerType.NEW_DATA,
    metadata={"data_path": "gs://bucket/new_data/", "data_version": "v3"}
)
```

### GCP Trigger Mock

```python
from ml_workflow import GCPTriggerMock, TriggerType

trigger = GCPTriggerMock()

# Trigger from new data
event = trigger.trigger_from_new_data(
    data_path="gs://bucket/new_data/",
    data_version="v3"
)

# Trigger from code update
event = trigger.trigger_from_code_update(
    commit_hash="abc123",
    branch="main"
)
```

## Components

| File | Purpose |
|------|---------|
| `modal_workflow.py` | Main orchestrator - runs all 5 workflow steps |
| `validation.py` | Validates model performance against thresholds |
| `deployment.py` | Deploys validated models to Modal/GCP |
| `gcp_trigger_mock.py` | Simulates GCP Pub/Sub triggers |
| `workflow_integration.py` | Connects triggers to Modal workflow |
| `config.py` | Configuration and performance thresholds |

## Testing

```bash
# Test validation
python src/ml_workflow/validation.py

# Test GCP trigger mock
python src/ml_workflow/gcp_trigger_mock.py

# Test deployment
python src/ml_workflow/deployment.py

# Test integration
python src/ml_workflow/workflow_integration.py
```

## File Structure

```
ml_workflow/
├── config.py                # Configuration and thresholds
├── modal_workflow.py        # Main orchestrator
├── validation.py            # Model validation service
├── deployment.py            # Model deployment service
├── gcp_trigger_mock.py      # GCP trigger simulation
├── workflow_integration.py  # GCP-Modal integration
├── test_workflow.py         # Test suite
├── README.md                # This file
└── WORKFLOW_EXPLANATION.md  # Detailed technical documentation
```

## Troubleshooting

**Workflow fails validation**: Check evaluation results against thresholds in `config.py`

**Modal deployment fails**: Verify Modal credentials and volume space

**GCP trigger not working**: Verify trigger mock configuration and workflow ID format

## Support

- Detailed workflow explanation: [WORKFLOW_EXPLANATION.md](./WORKFLOW_EXPLANATION.md)
- Modal Labs docs: https://modal.com/docs
- GCP Pub/Sub docs: https://cloud.google.com/pubsub/docs
