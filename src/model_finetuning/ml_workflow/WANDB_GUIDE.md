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
- **Real Training Enabled**: ✅ Training now calls actual training code (not mocked)
- **WandB Integration**: ✅ Fully integrated - training metrics are automatically logged

### ✅ Real Training Active

**Real training is now enabled** - the workflow calls the actual `centralized_train.py` training code, which means:
- ✅ Training loss will be logged to WandB in real-time
- ✅ Training runs will appear in your WandB dashboard
- ✅ All training metrics (loss, learning rate, etc.) are tracked
- ✅ You can see the training process in Modal Labs logs

**When you run the workflow, you should see:**
```
INFO:modal_workflow:📊 WandB logging enabled - training metrics will be tracked
INFO:modal_workflow:   Project: CAD-Coder-ML-Workflow
INFO:modal_workflow:🚀 Starting real training (this will log to WandB if enabled)...
```

This confirms:
- ✅ WandB API key is accessible
- ✅ WandB configuration is loaded
- ✅ Real training is running
- ✅ WandB is logging training metrics

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

See the main [README.md](./README.md) for complete workflow instructions. WandB will automatically log all training metrics when real training runs.

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
- **Main README**: [README.md](./README.md)
- **Workflow Explanation**: [WORKFLOW_EXPLANATION.md](./WORKFLOW_EXPLANATION.md)

---

## Summary

WandB is fully integrated and ready to track training runs. Once you:
1. Set up your WandB account and API key
2. Create the Modal secret with your API key
3. Run the workflow with real training enabled

All training metrics will be automatically logged to your WandB dashboard. See the [Current Status](#current-status) section above for details on what's working.
