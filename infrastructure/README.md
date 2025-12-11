# CAD-Coder Infrastructure

This directory contains all infrastructure-as-code and deployment configurations for the CAD-Coder application.

## Directory Structure

```
infrastructure/
├── pulumi/                    # Infrastructure provisioning with Pulumi
│   ├── __main__.py            # Main Pulumi program
│   ├── Pulumi.yaml            # Project configuration
│   ├── Pulumi.staging.yaml    # Staging stack configuration
│   ├── Pulumi.production.yaml # Production stack configuration
│   └── requirements.txt       # Python dependencies
├── kubernetes/                # Kubernetes deployment manifests
│   ├── namespace.yaml         # Namespace and resource quotas
│   ├── configmap.yaml         # Application configuration
│   ├── secrets.yaml           # Secret templates
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── qwen-inference-deployment.yaml
│   ├── llava-inference-deployment.yaml
│   ├── ingress.yaml           # Ingress and networking
│   ├── load-testing-job.yaml  # Load testing Kubernetes jobs
│   └── kustomization.yaml     # Kustomize configuration
├── load-testing/              # Load testing with Locust
│   ├── locustfile.py          # Load test scenarios
│   ├── Dockerfile             # Locust container
│   ├── docker-compose.yml     # Distributed load testing
│   └── requirements.txt
└── README.md                  # This file
```

## Prerequisites

- Google Cloud SDK (`gcloud`)
- Pulumi CLI
- kubectl
- Docker
- Python 3.11+

## Quick Start

### 1. Set Up GCP Authentication

```bash
# Authenticate to GCP
gcloud auth login
gcloud auth application-default login

# Set project
gcloud config set project cad-coder-nextgen
```

### 2. Deploy Infrastructure with Pulumi

```bash
cd infrastructure/pulumi

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize Pulumi (first time only)
pulumi login
pulumi stack init staging

# Preview changes
pulumi preview

# Deploy infrastructure
pulumi up
```

### 3. Deploy Application to GKE

```bash
# Get GKE credentials
gcloud container clusters get-credentials cad-coder-staging \
    --zone us-central1-a \
    --project cad-coder-nextgen

# Apply Kubernetes manifests
kubectl apply -k infrastructure/kubernetes/

# Or apply individually
kubectl apply -f infrastructure/kubernetes/namespace.yaml
kubectl apply -f infrastructure/kubernetes/configmap.yaml
kubectl apply -f infrastructure/kubernetes/backend-deployment.yaml
kubectl apply -f infrastructure/kubernetes/frontend-deployment.yaml
```

### 4. Configure Secrets

```bash
# Create secrets from environment variables
kubectl create secret generic cad-coder-secrets \
    --namespace=cad-coder \
    --from-literal=MONGO_URI="mongodb+srv://..." \
    --from-literal=HF_TOKEN="hf_..."

# Create GCP credentials secret
kubectl create secret generic gcp-credentials \
    --namespace=cad-coder \
    --from-file=key.json=path/to/service-account.json
```

## Infrastructure Components

### GKE Cluster

The Pulumi program provisions a GKE cluster with:

- **Standard Node Pool**: For backend, frontend, and general workloads
  - Machine type: e2-standard-4 (staging) / e2-standard-8 (production)
  - Auto-scaling: 1-10 nodes

- **GPU Node Pool (T4)**: For Qwen model inference
  - Machine type: n1-standard-8 with NVIDIA T4 GPU
  - Auto-scaling: 0-5 nodes
  - Taint: `nvidia.com/gpu=present:NoSchedule`

- **A100 Node Pool**: For LLaVA model inference
  - Machine type: a2-highgpu-1g with NVIDIA A100 40GB
  - Auto-scaling: 0-3 nodes
  - Taint: `nvidia.com/gpu=a100:NoSchedule`

### Networking

- VPC with custom subnetwork
- Cloud NAT for outbound connectivity
- GCE Ingress with managed SSL certificates
- Network policies for pod-to-pod communication

### Storage

- **Model Artifacts Bucket**: `cad-coder-models-{project}-{env}`
- **Data Versioning Bucket**: `cad-coder-data-{project}-{env}` (DVC remote)
- Persistent Volume Claims for model caches

### Auto-scaling

- **Horizontal Pod Autoscaler (HPA)**: CPU/memory-based scaling for all services
- **GPU-aware HPA**: Scales inference pods based on GPU utilization
- **Cluster Autoscaler**: Automatically provisions/deprovisions nodes
- **Vertical Pod Autoscaler (VPA)**: Right-sizes resource requests

## Load Testing

### Run Load Tests Locally

```bash
cd infrastructure/load-testing

# Install dependencies
pip install -r requirements.txt

# Run Locust with web UI
locust -f locustfile.py --host=http://localhost:8000

# Run headless
locust -f locustfile.py --host=http://localhost:8000 \
    --headless -u 50 -r 5 -t 5m
```

### Run Distributed Load Tests

```bash
cd infrastructure/load-testing

# Start master and 4 workers
LOCUST_HOST=http://your-api-endpoint:8000 \
    docker compose up --scale worker=4
```

### Run Load Tests on Kubernetes

```bash
# Run one-time load test
kubectl apply -f infrastructure/kubernetes/load-testing-job.yaml

# View logs
kubectl logs -f job/cad-coder-load-test -n cad-coder
```

## CI/CD Integration

The infrastructure integrates with GitHub Actions:

1. **CI Pipeline** (`.github/workflows/ci.yml`):
   - Runs tests and linting
   - Builds and validates Docker images
   - Triggers deployment on main branch

2. **Deploy Pipeline** (`.github/workflows/deploy.yml`):
   - Builds and pushes container images to Artifact Registry
   - Optionally deploys infrastructure with Pulumi
   - Deploys application to GKE
   - Runs smoke tests

### Required GitHub Secrets

```
GCP_PROJECT_ID              # GCP project ID
GCP_WORKLOAD_IDENTITY_PROVIDER  # Workload identity provider
GCP_SERVICE_ACCOUNT         # Service account email
GCP_SA_KEY                  # Service account key (base64)
PULUMI_ACCESS_TOKEN         # Pulumi access token
MONGO_URI                   # MongoDB connection string
HF_TOKEN                    # Hugging Face token
API_URL                     # Deployed API URL for smoke tests
```

## Monitoring and Observability

### View Cluster Status

```bash
# Deployments
kubectl get deployments -n cad-coder

# Pods
kubectl get pods -n cad-coder

# Services
kubectl get services -n cad-coder

# HPAs
kubectl get hpa -n cad-coder

# Node pools
gcloud container node-pools list \
    --cluster=cad-coder-staging \
    --zone=us-central1-a
```

### View Logs

```bash
# Backend logs
kubectl logs -f deployment/backend -n cad-coder

# Inference logs
kubectl logs -f deployment/qwen-inference -n cad-coder

# All pods
kubectl logs -l app=cad-coder -n cad-coder --all-containers
```

### Prometheus Metrics

Inference services expose Prometheus metrics at `/metrics`:

- `qwen_inference_requests_total` / `llava_inference_requests_total`
- `qwen_inference_latency_seconds` / `llava_inference_latency_seconds`
- `qwen_model_loaded` / `llava_model_loaded`
- `qwen_gpu_memory_used_bytes` / `llava_gpu_memory_used_bytes`

## Troubleshooting

### GPU Nodes Not Scaling Up

```bash
# Check cluster autoscaler logs
kubectl logs -n kube-system -l k8s-app=cluster-autoscaler

# Check node pool status
gcloud container node-pools describe gpu-pool \
    --cluster=cad-coder-staging \
    --zone=us-central1-a
```

### Model Loading Issues

```bash
# Check inference pod events
kubectl describe pod -l component=qwen-inference -n cad-coder

# Check GPU availability
kubectl describe node -l cloud.google.com/gke-accelerator=nvidia-tesla-t4
```

### Ingress Not Working

```bash
# Check ingress status
kubectl describe ingress cad-coder-ingress -n cad-coder

# Check backend config
kubectl describe backendconfig -n cad-coder

# Check managed certificate status
kubectl describe managedcertificate -n cad-coder
```

## Cost Management

### Estimated Costs (us-central1)

| Resource | Staging | Production |
|----------|---------|------------|
| GKE Management | $72/mo | $72/mo |
| Standard Nodes (2-3x e2-standard-4/8) | ~$100-200/mo | ~$200-400/mo |
| GPU Nodes (T4, on-demand) | ~$300-500/mo | ~$500-1000/mo |
| A100 Nodes (on-demand) | ~$1000-2000/mo | ~$2000-5000/mo |
| Storage (GCS, PVC) | ~$10-50/mo | ~$50-200/mo |
| Networking | ~$20-50/mo | ~$50-200/mo |

### Cost Optimization Tips

1. **Scale GPU nodes to 0** when not in use
2. Use **preemptible/spot VMs** for non-critical workloads
3. Enable **committed use discounts** for predictable workloads
4. Monitor with **Cloud Billing** and set budget alerts
