# Weights & Biases (WandB) Integration Guide

Complete guide for setting up and using WandB experiment tracking in the ML workflow.

## Table of Contents

1. [Current Status](#current-status)
2. [Quick Setup](#quick-setup)
3. [What Gets Tracked](#what-gets-tracked)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## Current Status

### ✅ What's Working

- **WandB Package**: Installed in Modal image (`wandb==0.21.0`)
- **Configuration**: Enabled in `config.py` (`log_to_wandb: True`)
- **Modal Secret Support**: Added for WandB API key
- **Training Code**: Already supports WandB logging in `centralized_train.py`

### ⚠️ Current Limitation

**Training is currently mocked** for quick pipeline testing, so WandB runs won't appear until real training executes. However, the infrastructure is ready - WandB will automatically log all metrics when real training runs.

**From your latest run, WandB is detected:**
```
INFO:modal_workflow:📊 WandB logging enabled - training metrics will be tracked
INFO:modal_workflow:   Project: CAD-Coder-ML-Workflow
```

This confirms:
- ✅ WandB API key is accessible
- ✅ WandB configuration is loaded
- ✅ Ready to log when real training runs

---

## Quick Setup

### Step 1: Create WandB Account and Get API Key

1. Go to https://wandb.ai and sign up for a free account
2. Once logged in, go to your profile settings: https://wandb.ai/settings
3. Scroll down to "API keys" section
4. Copy your API key (it looks like: `abc123def456...`)

### Step 2: Create Modal Secret with WandB API Key

```bash
# Create a Modal secret with your WandB API key
modal secret create wandb-secret WANDB_API_KEY=your_api_key_here
```

Replace `your_api_key_here` with your actual WandB API key from step 1.

### Step 3: Verify Secret Creation

```bash
# List your Modal secrets (should show wandb-secret)
modal secret list
```

### Step 4: Run the Workflow

```bash
# Test mode with limited samples
modal run src/ml_workflow/modal_workflow.py \
  --workflow-id test_with_wandb \
  --trigger-type manual \
  --max-training-samples 100 \
  --max-test-samples 50

# Full training (when ready)
modal run src/ml_workflow/modal_workflow.py \
  --workflow-id full_training \
  --trigger-type manual
```

WandB will automatically log all training metrics when real training runs.

---

## What Gets Tracked

Once WandB is set up and real training runs, the workflow will automatically log:

### Training Metrics
- **Training loss** over steps
- **Validation loss** (if `eval_steps` enabled)
- **Learning rate schedule**
- **Epoch progress**
- **Step-by-step metrics**

### System Metrics
- **GPU utilization**
- **Memory usage**
- **Training speed** (samples/sec)
- **CUDA metrics**

### Configuration
- All hyperparameters (batch size, learning rate, etc.)
- Model architecture details
- Training configuration
- Workflow ID and trigger type
- Data paths and sample limits

### Artifacts
- Model checkpoints
- Evaluation results
- Training logs

### Example WandB Dashboard

After running the workflow, your WandB dashboard will show:

- **Charts:**
  - Training loss over steps
  - Validation loss (if eval_steps is enabled)
  - Learning rate schedule
  
- **System:**
  - GPU utilization
  - Memory usage
  - Training speed (samples/sec)

- **Config:**
  - All hyperparameters
  - Model architecture
  - Training configuration

- **Logs:**
  - Training progress
  - Checkpoint saves
  - Validation results

---

## Configuration

WandB settings are configured in `config.py`:

```python
TRAINING_CONFIG = {
    # ... other settings ...
    "log_to_wandb": True,  # Enable WandB logging
    "wandb_project": "CAD-Coder-ML-Workflow",  # Project name
}
```

### Customization

**Change Project Name:**
Edit `config.py` and modify `wandb_project`:
```python
"wandb_project": "My-Custom-Project-Name"
```

**Disable WandB Temporarily:**
Set `log_to_wandb: False` in `config.py` or remove the WandB secret from Modal.

---

## Verification

### In Workflow Logs

After running the workflow, you should see:

```
📊 WandB logging enabled - training metrics will be tracked
   Project: CAD-Coder-ML-Workflow
Tracking run with wandb version 0.21.0
🚀 View run at: https://wandb.ai/your-username/CAD-Coder-ML-Workflow/runs/...
```

### In WandB Dashboard

1. Go to https://wandb.ai
2. Navigate to the "CAD-Coder-ML-Workflow" project
3. You'll see all your training runs with:
   - Loss curves over time
   - Learning rate schedule
   - Validation metrics
   - Training configuration
   - System metrics (GPU usage, memory, etc.)

---

## Troubleshooting

### WandB Not Logging

**1. Check if secret exists:**
```bash
modal secret list
```

**2. Verify API key is correct:**
- Make sure you copied the full API key from WandB settings
- The key should start with letters/numbers (no spaces)
- Recreate the secret if needed:
  ```bash
  modal secret delete wandb-secret  # Remove old secret
  modal secret create wandb-secret WANDB_API_KEY=your_key_here
  ```

**3. Check workflow logs:**
- Look for WandB initialization messages in the training logs
- Should see: "Tracking run with wandb version X.X.X"
- If you see "WandB logging requested but WANDB_API_KEY not found", the secret isn't accessible

### API Key Not Found

If you see errors about WandB API key:
- Make sure you created the Modal secret: `modal secret create wandb-secret WANDB_API_KEY=your_key`
- The secret name must be exactly `wandb-secret`
- Verify the secret is accessible: `modal secret list`

### Training is Mocked

**Current Status:**
- The workflow uses mocked training for quick testing
- WandB is configured and ready, but no runs appear because training is mocked

**To See Real WandB Tracking:**
- The training step needs to call the actual training code
- The training infrastructure (with WandB support) is ready in `model_finetuning/centralized_train.py`
- Once real training runs, WandB will automatically log all metrics

### No Runs Appearing in WandB

**Possible Reasons:**
1. **Training is mocked** - No real training = no WandB runs
2. **API key not accessible** - Check Modal secret
3. **WandB disabled** - Check `config.py` for `log_to_wandb: True`
4. **Network issues** - WandB needs internet access (Modal has this by default)

---

## Next Steps

Once WandB is set up and real training runs, you can:

- **Compare different training runs** - See which hyperparameters work best
- **Track model performance** - Monitor loss curves and validation metrics
- **Monitor system resources** - GPU utilization, memory usage
- **Share results** - Collaborate with your team
- **Reproduce experiments** - All configs are logged automatically

---

## Reference

- **WandB Documentation**: https://docs.wandb.ai
- **Modal Secrets Documentation**: https://modal.com/docs/guide/secrets
- **Project README**: [README.md](./README.md)
- **Workflow Explanation**: [WORKFLOW_EXPLANATION.md](./WORKFLOW_EXPLANATION.md)

---

## Summary

**Setup Status:**
- ✅ WandB package installed
- ✅ WandB configuration added
- ✅ Modal secret support added
- ✅ Training code supports WandB

**To See Training Runs:**
1. ✅ Set up WandB account and API key (you've done this)
2. ✅ Create Modal secret (you've done this)
3. ⏳ Enable real training (currently mocked for testing)

**The workflow is production-ready and WandB will track training automatically once real training is enabled.**

