# Kubernetes Load Testing for CAD-Coder

This directory contains Kubernetes-native load testing configurations and results for demonstrating reliability and scalability of the CAD-Coder application.

## Overview

The load testing suite validates:
1. **Backend API scalability** - How the FastAPI backend handles concurrent requests
2. **Frontend serving capacity** - Static asset delivery under load
3. **Horizontal Pod Autoscaler (HPA) behavior** - Automatic scaling based on CPU/memory metrics
4. **End-to-end latency** - Response times under various load conditions

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Load Test     │────▶│    Ingress      │────▶│   Frontend      │
│   (Locust Pod)  │     │   Controller    │     │   Deployment    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │    Backend      │────▶│  Model Inference│
                        │   Deployment    │     │   (GPU Pods)    │
                        └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   MongoDB       │
                        │   (External)    │
                        └─────────────────┘
```

## Components

### 1. Locust Load Generator (`locust-deployment.yaml`)
Kubernetes deployment for running Locust load tests within the cluster.

### 2. HPA Configuration (`hpa-config.yaml`)
Horizontal Pod Autoscaler configurations for frontend and backend services.

### 3. Load Test Job (`load-test-job.yaml`)
One-time job for running load tests and collecting results.

### 4. Monitoring (`prometheus-rules.yaml`)
Prometheus alerting rules for load testing scenarios.

## Quick Start

### 1. Deploy Load Testing Infrastructure

```bash
# Apply all load testing resources
kubectl apply -f infrastructure/kubernetes/load-testing/

# Or apply individually
kubectl apply -f infrastructure/kubernetes/load-testing/locust-deployment.yaml
kubectl apply -f infrastructure/kubernetes/load-testing/hpa-config.yaml
```

### 2. Run Load Test

```bash
# Run a one-time load test job
kubectl apply -f infrastructure/kubernetes/load-testing/load-test-job.yaml

# Watch the job progress
kubectl logs -f job/cad-coder-load-test -n cad-coder
```

### 3. Access Locust Web UI (Optional)

```bash
# Port-forward to Locust master
kubectl port-forward svc/locust-master -n cad-coder 8089:8089

# Open http://localhost:8089 in browser
```

### 4. Monitor Scaling

```bash
# Watch HPA scaling behavior
kubectl get hpa -n cad-coder -w

# Watch pod scaling
kubectl get pods -n cad-coder -w
```

## Test Scenarios

### Scenario 1: Light Load (Baseline)
- **Users**: 10 concurrent
- **Spawn Rate**: 2 users/second
- **Duration**: 5 minutes
- **Purpose**: Establish baseline metrics

```bash
kubectl apply -f infrastructure/kubernetes/load-testing/scenarios/light-load.yaml
```

### Scenario 2: Medium Load (Normal Operations)
- **Users**: 50 concurrent
- **Spawn Rate**: 5 users/second
- **Duration**: 10 minutes
- **Purpose**: Simulate typical production traffic

```bash
kubectl apply -f infrastructure/kubernetes/load-testing/scenarios/medium-load.yaml
```

### Scenario 3: Heavy Load (Stress Test)
- **Users**: 100 concurrent
- **Spawn Rate**: 10 users/second
- **Duration**: 15 minutes
- **Purpose**: Test autoscaling and system limits

```bash
kubectl apply -f infrastructure/kubernetes/load-testing/scenarios/heavy-load.yaml
```

### Scenario 4: Spike Test
- **Pattern**: 10 → 100 → 10 users (rapid spike)
- **Duration**: 10 minutes
- **Purpose**: Test system recovery from sudden load spikes

## Expected Scaling Behavior

### Backend Service
| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU > 70% | Scale up | Add 1 replica (max 5) |
| CPU < 30% | Scale down | Remove 1 replica (min 1) |
| Memory > 80% | Scale up | Add 1 replica |

### Frontend Service
| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU > 60% | Scale up | Add 1 replica (max 3) |
| CPU < 20% | Scale down | Remove 1 replica (min 1) |

## GPU Inference Load Testing Considerations

### Current Limitations

Load testing GPU-accelerated model inference on GKE presents significant challenges:

1. **GPU Resource Scarcity**: Cloud providers often have limited GPU availability, especially for high-demand SKUs (A100, T4). Obtaining multiple GPU nodes for load testing can be difficult or impossible during peak demand periods.

2. **Cost Constraints**: GPU instances are expensive ($2-4/hour for T4, $4-8/hour for A100). Running sustained load tests with multiple GPU replicas can quickly become cost-prohibitive.

3. **Quota Limitations**: GCP projects have GPU quotas that may restrict the number of concurrent GPU nodes, limiting the ability to test horizontal scaling of inference workloads.

4. **Cold Start Overhead**: GPU pods have significant startup times (1-5 minutes) due to model loading, making rapid autoscaling less effective for handling sudden traffic spikes.

5. **Single-Request Bottleneck**: Unlike CPU workloads, GPU inference typically processes one request at a time per GPU (unless using batching), creating natural throughput limits.

### Recommended Approach for GPU Load Testing

When GPU resources are available:

1. **Staged Testing**: Start with a single GPU pod and gradually increase load to identify the saturation point.

2. **Batch Processing**: Configure inference servers to batch multiple requests, improving throughput.

3. **Queue-Based Architecture**: Implement request queuing to handle bursts without overwhelming GPU resources.

4. **Preemptible/Spot Instances**: Use spot instances for cost-effective load testing (with appropriate handling for preemption).

### What We Can Test Without GPUs

The load testing suite focuses on components that can scale without GPU constraints:

- ✅ Backend API endpoints (health, history, non-inference routes)
- ✅ Frontend static asset serving
- ✅ Database query performance
- ✅ Network latency and throughput
- ✅ Pod scheduling and startup times
- ✅ HPA scaling behavior for CPU-bound workloads

## Results

See the `results/` directory for load test results and analysis:

- `results/baseline-test.md` - Baseline performance metrics
- `results/scaling-test.md` - Autoscaling behavior observations
- `results/summary.md` - Executive summary of findings

## Troubleshooting

### Pods Not Scaling

```bash
# Check HPA status
kubectl describe hpa backend-hpa -n cad-coder

# Check metrics server
kubectl top pods -n cad-coder
```

### Load Test Job Failing

```bash
# Check job status
kubectl describe job cad-coder-load-test -n cad-coder

# Check pod logs
kubectl logs -l job-name=cad-coder-load-test -n cad-coder
```

### High Error Rates

```bash
# Check backend logs
kubectl logs -l component=backend -n cad-coder --tail=100

# Check resource usage
kubectl top pods -n cad-coder
```

## References

- [Locust Documentation](https://docs.locust.io/)
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [GKE Autoscaling](https://cloud.google.com/kubernetes-engine/docs/concepts/horizontalpodautoscaler)

