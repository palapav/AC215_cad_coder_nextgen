# ML Workflow - Kubernetes Resources

This directory contains Kubernetes manifests for automated model retraining and deployment on GKE.

## Overview

The ML workflow provides:

1. **Automated Retraining**: Scheduled CronJob for periodic model retraining
2. **Data-Triggered Retraining**: Trigger retraining when new data is available
3. **Code-Triggered Retraining**: Trigger retraining on codebase updates
4. **Validation Checks**: Ensure models meet performance thresholds before deployment
5. **Conditional Deployment**: Only deploy models that pass validation

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ML Workflow Pipeline                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Trigger │───▶│ Training │───▶│  Eval    │───▶│Validation│  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │                                                │        │
│       │                                                ▼        │
│  ┌────┴────┐                                    ┌──────────┐   │
│  │Scheduled│                                    │  Deploy  │   │
│  │New Data │                                    │(if pass) │   │
│  │Code Upd │                                    └──────────┘   │
│  └─────────┘                                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### Files

| File | Description |
|------|-------------|
| `retraining-cronjob.yaml` | CronJob for scheduled retraining (disabled by default) |
| `configmap.yaml` | Configuration for training and validation thresholds |
| `rbac.yaml` | Service account and permissions |
| `pvc.yaml` | Persistent storage for models and data |

### Performance Thresholds

Models must meet ALL thresholds to be deployed:

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Valid Sample Rate | ≥ 95% | Percentage of samples generating valid CAD code |
| Mean IOU | ≥ 0.50 | Average intersection-over-union score |
| Median IOU | ≥ 0.55 | Median intersection-over-union score |
| Failed Generation Rate | ≤ 5% | Maximum allowed generation failures |

## Usage

### Deploy ML Workflow Resources (Disabled by Default)

```bash
# Apply all ML workflow resources
kubectl apply -f infrastructure/kubernetes/ml-workflow/

# Verify resources
kubectl get cronjob,configmap,serviceaccount -n cad-coder -l component=ml-workflow
```

### Enable Scheduled Retraining

The CronJob is **disabled by default** to prevent unintended training runs:

```bash
# Enable scheduled retraining (runs weekly on Sunday at 2 AM UTC)
kubectl patch cronjob ml-retraining-job -n cad-coder -p '{"spec":{"suspend":false}}'

# Disable scheduled retraining
kubectl patch cronjob ml-retraining-job -n cad-coder -p '{"spec":{"suspend":true}}'
```

### Manually Trigger Retraining

```bash
# Create a one-off job from the CronJob template
kubectl create job ml-retrain-manual-$(date +%s) \
  --from=cronjob/ml-retraining-job \
  -n cad-coder

# Monitor the job
kubectl logs -f job/ml-retrain-manual-<timestamp> -n cad-coder
```

### View Workflow Status

```bash
# List recent jobs
kubectl get jobs -n cad-coder -l component=ml-workflow

# View job logs
kubectl logs job/<job-name> -n cad-coder

# Check CronJob status
kubectl describe cronjob ml-retraining-job -n cad-coder
```

## Configuration

### Modify Training Parameters

Edit `configmap.yaml` to adjust training configuration:

```yaml
data:
  NUM_EPOCHS: "2"           # Increase training epochs
  BATCH_SIZE: "2"           # Increase batch size (requires more GPU memory)
  LEARNING_RATE: "1e-5"     # Adjust learning rate
```

Apply changes:
```bash
kubectl apply -f infrastructure/kubernetes/ml-workflow/configmap.yaml
```

### Modify Validation Thresholds

Edit `configmap.yaml` to adjust deployment thresholds:

```yaml
data:
  MIN_VALID_SAMPLE_RATE: "0.90"  # Lower threshold (less strict)
  MIN_MEAN_IOU: "0.45"           # Lower threshold
```

## Integration with CI/CD

The ML workflow can be triggered from GitHub Actions:

```yaml
# In .github/workflows/deploy.yml
- name: Trigger ML Retraining
  if: contains(github.event.head_commit.modified, 'src/model_finetuning/')
  run: |
    kubectl create job ml-retrain-$(date +%s) \
      --from=cronjob/ml-retraining-job \
      -n cad-coder
```

## Monitoring

### Prometheus Metrics (Future)

The workflow can expose metrics for monitoring:

- `ml_workflow_runs_total`: Total workflow executions
- `ml_workflow_duration_seconds`: Workflow duration
- `ml_workflow_validation_passed`: Validation pass rate
- `ml_model_iou_score`: Model IOU score

### Alerting (Future)

Set up alerts for:

- Workflow failures
- Validation failures
- Training duration anomalies

## Troubleshooting

### Job Stuck in Pending

```bash
# Check pod events
kubectl describe pod -l job-name=<job-name> -n cad-coder

# Common issues:
# - Insufficient resources: Check node capacity
# - PVC not bound: Check storage class availability
```

### Validation Always Failing

```bash
# Check evaluation results
kubectl logs job/<job-name> -n cad-coder | grep -A 20 "Validation"

# Adjust thresholds if needed
kubectl edit configmap ml-workflow-config -n cad-coder
```

### GPU Not Available

The workflow is designed to run without GPU (will be slower):

```bash
# Check GPU node status
kubectl get nodes -l cloud.google.com/gke-accelerator=nvidia-tesla-t4

# Check GPU quota
gcloud compute regions describe us-central1 --format="value(quotas)"
```

## Notes

- **GPU Availability**: Due to cloud provider constraints, GPU nodes may not always be available. The workflow can run on CPU (slower) as a fallback.
- **Cost Considerations**: Training on GPU incurs significant costs. Use scheduled retraining sparingly.
- **Data Requirements**: Ensure training data is available in the configured paths before running the workflow.

