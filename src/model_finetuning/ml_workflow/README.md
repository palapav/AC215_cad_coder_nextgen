# ML Workflow on Modal Labs

A production-ready ML workflow system for container segmentation that integrates data preprocessing, model training, evaluation, validation, and deployment. The workflow can be triggered automatically from GCP (mocked) and includes validation checks to ensure only models meeting performance thresholds are deployed.

## 📖 Documentation

- **[DATA_PREPARATION.md](./DATA_PREPARATION.md)** - Guide for preparing training data in the required format
- **[WANDB_GUIDE.md](./WANDB_GUIDE.md)** - Complete guide for setting up and using WandB experiment tracking
- **[WORKFLOW_EXPLANATION.md](./WORKFLOW_EXPLANATION.md)** - Complete technical explanation of the workflow, rubric mapping, and detailed step-by-step breakdown

## Quick Start

### Prerequisites

- **Modal Labs account**: Sign up at https://modal.com
- **WandB account** (optional but recommended): Sign up at https://wandb.ai
- **Python 3.11+** with virtual environment

### Install Dependencies

```bash
# Activate your virtual environment
source .venv/bin/activate  # or: conda activate your_env

# Install Modal CLI
pip install modal
modal token new  # Authenticate with Modal

# Install datasets library (for data preparation)
pip install datasets
```

### Prepare Training Data

Before running the workflow, you need to prepare your training data. See **[DATA_PREPARATION.md](./DATA_PREPARATION.md)** for complete instructions.

**Quick example** (if you have `src/data/dataset.jsonl`):

```bash
python src/model_finetuning/prepare_training_data.py
```

### Optional: Set Up Weights & Biases (WandB) Tracking

To track training runs in WandB, see **[WANDB_GUIDE.md](./WANDB_GUIDE.md)** for setup instructions.

**Quick setup**:
```bash
modal secret create wandb-secret WANDB_API_KEY=your_api_key_here
```

### Run the Workflow

```bash
# Test mode: Run on limited samples (quick pipeline test)
modal run src/model_finetuning/modal_workflow.py \
  --workflow-id test_quick \
  --trigger-type manual \
  --max-training-samples 100 \
  --max-test-samples 50

# Full dataset run
modal run src/model_finetuning/modal_workflow.py \
  --workflow-id production_run_001 \
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

### Full Dataset Run

```bash
modal run src/model_finetuning/modal_workflow.py \
  --workflow-id container_seg_v1 \
  --trigger-type manual \
  --deploy-to-modal
```

### Test Mode (Limited Samples)

Run the complete pipeline on a small subset of data to quickly verify the workflow:

```bash
# Test with 100 training samples and 50 test samples
modal run src/model_finetuning/modal_workflow.py \
  --workflow-id test_pipeline \
  --trigger-type manual \
  --max-training-samples 100 \
  --max-test-samples 50 \
  --deploy-to-modal
```

This is useful for:
- **Quick validation**: Test the entire pipeline end-to-end without processing the full dataset
- **Development**: Verify code changes work correctly before running expensive full training
- **CI/CD**: Run pipeline tests in automated environments with limited resources

> **Note**: Make sure you've prepared your training data first. See [DATA_PREPARATION.md](./DATA_PREPARATION.md) for instructions.

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

## Configuration

### Training Configuration

Edit `config.py` to adjust training parameters:

```python
TRAINING_CONFIG = {
    "base_model": "Qwen/Qwen3-VL-2B-Instruct",
    "num_epochs": 1,
    "batch_size": 1,  # Reduced for memory efficiency
    "gradient_accumulation_steps": 8,  # Effective batch size = 8
    "learning_rate": 2e-5,
    "max_len": 2048,  # Sequence length
    "gradient_checkpointing": True,  # Memory optimization
    "log_to_wandb": True,
    "wandb_project": "CAD-Coder-ML-Workflow",
}
```

### Performance Thresholds

Models must meet these thresholds to be deployed:

```python
PERFORMANCE_THRESHOLDS = {
    "min_valid_sample_rate": 0.95,  # 95% minimum
    "min_mean_iou": 0.50,
    "min_median_iou": 0.55,
    "max_failed_generation_rate": 0.05,  # 5% maximum
}
```

## Command-Line Options

```bash
modal run src/model_finetuning/modal_workflow.py \
  --workflow-id <unique_id> \
  --trigger-type <manual|gcp_mock> \
  [--max-training-samples <N>] \
  [--max-test-samples <N>] \
  [--deploy-to-modal <true|false>] \
  [--deploy-to-gcp <true|false>]
```

### Arguments

- `--workflow-id`: Unique identifier for this workflow run
- `--trigger-type`: How the workflow was triggered (`manual` or `gcp_mock`)
- `--max-training-samples`: Limit training samples for testing (optional)
- `--max-test-samples`: Limit test samples for evaluation (optional)
- `--deploy-to-modal`: Deploy to Modal Labs (default: `true`)
- `--deploy-to-gcp`: Deploy to GCP Vertex AI (default: `false`)

## Monitoring

### WandB Dashboard

View training metrics and loss curves:

1. Go to https://wandb.ai
2. Navigate to your project: `CAD-Coder-ML-Workflow`
3. View run details, loss curves, and system metrics

### Modal Labs UI

Monitor workflow execution:

1. Go to https://modal.com
2. Navigate to your app: `cad-coder-ml-workflow`
3. View function logs, execution timeline, and resource usage

## Model Output

Trained models are saved to:

- **Path**: `/models/trained/{workflow_id}/final_lora_adapters/`
- **Volume**: `cad-coder-ml-models` (Modal volume)
- **Format**: LoRA adapters (lightweight, efficient)

### Model Files

- `adapter_config.json`: LoRA configuration
- `adapter_model.safetensors`: Trained weights
- `README.md`: Model documentation

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
python src/model_finetuning/validation.py

# Test GCP trigger mock
python src/model_finetuning/gcp_trigger_mock.py

# Test deployment
python src/model_finetuning/deployment.py

# Test integration
python src/model_finetuning/workflow_integration.py
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
├── prepare_training_data.py # Data preparation script
├── README.md                # This file
├── DATA_PREPARATION.md      # Data preparation guide
├── WANDB_GUIDE.md           # WandB setup guide
└── WORKFLOW_EXPLANATION.md  # Detailed technical documentation
```

## Troubleshooting

### No Training Data Found

**Solution**: See [DATA_PREPARATION.md](./DATA_PREPARATION.md) to prepare your data

### Workflow Fails Validation

**Solution**: Check evaluation results against thresholds in `config.py`

### Modal Deployment Fails

**Solution**: Verify Modal credentials and volume space

### GCP Trigger Not Working

**Solution**: Verify trigger mock configuration and workflow ID format

### WandB Not Logging

**Solution**: See [WANDB_GUIDE.md](./WANDB_GUIDE.md) for troubleshooting steps

### CUDA Out of Memory

**Solution**:
1. Reduce `batch_size` in `config.py` (currently 1)
2. Reduce `max_len` in `config.py` (currently 2048)
3. Increase `gradient_accumulation_steps` to maintain effective batch size

### Data Not Found

**Solution**:
1. Verify data is uploaded: `modal volume ls cad-coder-training-data`
2. Check data paths in logs
3. Re-upload data: `modal volume put cad-coder-training-data ./data/partitioned /data/partitioned`

## Support

- **Detailed Workflow Explanation**: [WORKFLOW_EXPLANATION.md](./WORKFLOW_EXPLANATION.md)
- **Data Preparation Guide**: [DATA_PREPARATION.md](./DATA_PREPARATION.md)
- **WandB Setup Guide**: [WANDB_GUIDE.md](./WANDB_GUIDE.md)
- **Modal Labs docs**: https://modal.com/docs
- **GCP Pub/Sub docs**: https://cloud.google.com/pubsub/docs
