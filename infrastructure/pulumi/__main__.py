"""
CAD-Coder Production Infrastructure with Pulumi

This module provisions the complete production infrastructure on GCP:
- GKE Cluster with GPU node pools for model inference
- Cloud SQL (MongoDB equivalent via Atlas or Firestore)
- Cloud Storage for model artifacts and data
- Vertex AI Matching Engine for RAG
- Load balancers and networking
- Auto-scaling configurations
"""

import pulumi
from pulumi import Config, Output, export
import pulumi_gcp as gcp
import pulumi_kubernetes as k8s

# =============================================================================
# Configuration
# =============================================================================

config = Config()
gcp_config = Config("gcp")

project = gcp_config.require("project")
region = gcp_config.get("region") or "us-central1"
zone = gcp_config.get("zone") or "us-central1-a"

# Cluster configuration
cluster_name = config.get("cluster_name") or "cad-coder-cluster"
node_count = config.get_int("node_count") or 1 # from 2
gpu_node_count = config.get_int("gpu_node_count") or 1
machine_type = config.get("machine_type") or "e2-standard-2" # from e2-standard-4
gpu_machine_type = config.get("gpu_machine_type") or "n1-standard-8"
gpu_type = config.get("gpu_type") or "nvidia-tesla-t4"
gpu_count = config.get_int("gpu_count") or 1
enable_gpu_pools = config.get_bool("enable_gpu_pools") or False

# Environment
environment = config.get("environment") or "production"

# region agent log
def _agent_log(message: str, data: dict) -> None:
    """Append a tiny NDJSON line for debug-mode tracing (no secrets)."""
    try:
        import json, time
        with open("/Users/aditya/Documents/apcomp215/cad-coder-nextgen/.cursor/debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "pulumi-run",
                "hypothesisId": "taint-duplication",
                "location": "infrastructure/pulumi/__main__.py",
                "message": message,
                "data": data,
                "timestamp": int(time.time() * 1000),
            }) + "\n")
    except Exception:
        pass
# endregion agent log

# =============================================================================
# Networking
# =============================================================================

# VPC Network
network = gcp.compute.Network(
    "cad-coder-network",
    name=f"cad-coder-{environment}-network",
    auto_create_subnetworks=False,
    project=project,
)

# Subnetwork for GKE
subnetwork = gcp.compute.Subnetwork(
    "cad-coder-subnetwork",
    name=f"cad-coder-{environment}-subnet",
    ip_cidr_range="10.0.0.0/16",
    region=region,
    network=network.id,
    project=project,
    secondary_ip_ranges=[
        gcp.compute.SubnetworkSecondaryIpRangeArgs(
            range_name="pods",
            ip_cidr_range="10.1.0.0/16",
        ),
        gcp.compute.SubnetworkSecondaryIpRangeArgs(
            range_name="services",
            ip_cidr_range="10.2.0.0/20",
        ),
    ],
)

# Cloud NAT for outbound connectivity
router = gcp.compute.Router(
    "cad-coder-router",
    name=f"cad-coder-{environment}-router",
    region=region,
    network=network.id,
    project=project,
)

nat = gcp.compute.RouterNat(
    "cad-coder-nat",
    name=f"cad-coder-{environment}-nat",
    router=router.name,
    region=region,
    nat_ip_allocate_option="AUTO_ONLY",
    source_subnetwork_ip_ranges_to_nat="ALL_SUBNETWORKS_ALL_IP_RANGES",
    project=project,
)

# =============================================================================
# GKE Cluster
# =============================================================================

# Service Account for GKE nodes
gke_sa = gcp.serviceaccount.Account(
    "gke-node-sa",
    account_id=f"cad-coder-gke-{environment}",
    display_name=f"CAD-Coder GKE Node Service Account ({environment})",
    project=project,
)

# Grant necessary permissions to the service account
for role in [
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/storage.objectViewer",
    "roles/artifactregistry.reader",
]:
    gcp.projects.IAMMember(
        f"gke-sa-{role.split('/')[-1]}",
        project=project,
        role=role,
        member=gke_sa.email.apply(lambda email: f"serviceAccount:{email}"),
    )

# GKE Cluster
cluster = gcp.container.Cluster(
    "cad-coder-cluster",
    name=cluster_name,
    location=zone,
    project=project,
    
    # Remove default node pool, we'll create custom ones
    remove_default_node_pool=True,
    initial_node_count=1,
    
    # Network configuration
    network=network.id,
    subnetwork=subnetwork.id,
    ip_allocation_policy=gcp.container.ClusterIpAllocationPolicyArgs(
        cluster_secondary_range_name="pods",
        services_secondary_range_name="services",
    ),
    
    # Cluster features
    release_channel=gcp.container.ClusterReleaseChannelArgs(
        channel="REGULAR",
    ),
    
    # Workload identity for secure service account binding
    workload_identity_config=gcp.container.ClusterWorkloadIdentityConfigArgs(
        workload_pool=f"{project}.svc.id.goog",
    ),
    
    # Enable Vertical Pod Autoscaler
    vertical_pod_autoscaling=gcp.container.ClusterVerticalPodAutoscalingArgs(
        enabled=True,
    ),
    
    # Enable cluster autoscaling
    cluster_autoscaling=gcp.container.ClusterClusterAutoscalingArgs(
        enabled=True,
        resource_limits=[
            gcp.container.ClusterClusterAutoscalingResourceLimitArgs(
                resource_type="cpu",
                minimum=4,
                maximum=100,
            ),
            gcp.container.ClusterClusterAutoscalingResourceLimitArgs(
                resource_type="memory",
                minimum=16,
                maximum=400,
            ),
        ],
        auto_provisioning_defaults=gcp.container.ClusterClusterAutoscalingAutoProvisioningDefaultsArgs(
            service_account=gke_sa.email,
            oauth_scopes=[
                "https://www.googleapis.com/auth/cloud-platform",
            ],
        ),
    ),
    
    # Addons
    addons_config=gcp.container.ClusterAddonsConfigArgs(
        http_load_balancing=gcp.container.ClusterAddonsConfigHttpLoadBalancingArgs(
            disabled=False,
        ),
        horizontal_pod_autoscaling=gcp.container.ClusterAddonsConfigHorizontalPodAutoscalingArgs(
            disabled=False,
        ),
        gce_persistent_disk_csi_driver_config=gcp.container.ClusterAddonsConfigGcePersistentDiskCsiDriverConfigArgs(
            enabled=True,
        ),
    ),
    
    # Logging and monitoring
    logging_service="logging.googleapis.com/kubernetes",
    monitoring_service="monitoring.googleapis.com/kubernetes",
)

# =============================================================================
# Node Pools
# =============================================================================

# Standard node pool for backend, frontend, and other services
standard_node_pool = gcp.container.NodePool(
    "standard-node-pool",
    name="standard-pool",
    cluster=cluster.name,
    location=zone,
    project=project,
    
    initial_node_count=node_count,
    
    autoscaling=gcp.container.NodePoolAutoscalingArgs(
        min_node_count=1,
        max_node_count=2, # from 10
    ),
    
    node_config=gcp.container.NodePoolNodeConfigArgs(
        machine_type=machine_type,
        image_type="COS_CONTAINERD",
        disk_type="pd-standard",
        disk_size_gb=100,
        service_account=gke_sa.email,
        oauth_scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
        ],
        labels={
            "workload": "standard",
            "environment": environment,
        },
        tags=["cad-coder", environment],
        
        workload_metadata_config=gcp.container.NodePoolNodeConfigWorkloadMetadataConfigArgs(
            mode="GKE_METADATA",
        ),
    ),
    
    management=gcp.container.NodePoolManagementArgs(
        auto_repair=True,
        auto_upgrade=True,
    ),
)

# region agent log
_agent_log("configured_standard_node_pool", {
    "labels": {
        "workload": "standard",
        "environment": environment,
    },
    "node_count": node_count,
    "machine_type": machine_type,
    "image_type": "COS_CONTAINERD",
    "disk_type": "pd-standard",
    "disk_size_gb": 100,
})
# endregion agent log

# GPU node pool for model inference (Qwen and LLaVA)
gpu_node_pool = None
if enable_gpu_pools:
    gpu_node_pool = gcp.container.NodePool(
        "gpu-node-pool",
        name="gpu-pool",
        cluster=cluster.name,
        location=zone,
        project=project,
        
        initial_node_count=0,  # Start with 0, scale up as needed
        
        autoscaling=gcp.container.NodePoolAutoscalingArgs(
            min_node_count=0,
            max_node_count=5,
        ),
        
        node_config=gcp.container.NodePoolNodeConfigArgs(
            machine_type=gpu_machine_type,
            service_account=gke_sa.email,
            oauth_scopes=[
                "https://www.googleapis.com/auth/cloud-platform",
            ],
            
            # GPU configuration
            guest_accelerators=[
                gcp.container.NodePoolNodeConfigGuestAcceleratorArgs(
                    type=gpu_type,
                    count=gpu_count,
                    gpu_driver_installation_config=gcp.container.NodePoolNodeConfigGuestAcceleratorGpuDriverInstallationConfigArgs(
                        gpu_driver_version="DEFAULT",
                    ),
                ),
            ],
            
            labels={
                "workload": "gpu-inference",
                "environment": environment,
                "gpu": "true",
            },
            
            taints=[
                gcp.container.NodePoolNodeConfigTaintArgs(
                    key="nvidia.com/gpu",
                    value="present",
                    effect="NO_SCHEDULE",
                ),
            ],
            
            tags=["cad-coder", environment, "gpu"],
            
            workload_metadata_config=gcp.container.NodePoolNodeConfigWorkloadMetadataConfigArgs(
                mode="GKE_METADATA",
            ),
        ),
        
        management=gcp.container.NodePoolManagementArgs(
            auto_repair=True,
            auto_upgrade=True,
        ),
    )

    # region agent log
    _agent_log("configured_gpu_node_pool", {
        "taints": "explicit-nvidia.com/gpu:present",
        "labels": {
            "workload": "gpu-inference",
            "environment": environment,
            "gpu": "true",
        },
    })
    # endregion agent log
else:
    # region agent log
    _agent_log("skipped_gpu_node_pool", {
        "enable_gpu_pools": enable_gpu_pools,
    })
    # endregion agent log

a100_node_pool = None
if enable_gpu_pools:
    # A100 GPU node pool for high-performance inference (LLaVA 13B)
    a100_node_pool = gcp.container.NodePool(
        "a100-node-pool",
        name="a100-pool",
        cluster=cluster.name,
        location=zone,
        project=project,
        
        initial_node_count=0,  # Start with 0, scale up on demand
        
        autoscaling=gcp.container.NodePoolAutoscalingArgs(
            min_node_count=0,
            max_node_count=3,
        ),
        
        node_config=gcp.container.NodePoolNodeConfigArgs(
            machine_type="a2-highgpu-1g",  # A100 40GB
            service_account=gke_sa.email,
            oauth_scopes=[
                "https://www.googleapis.com/auth/cloud-platform",
            ],
            
            guest_accelerators=[
                gcp.container.NodePoolNodeConfigGuestAcceleratorArgs(
                    type="nvidia-tesla-a100",
                    count=1,
                    gpu_driver_installation_config=gcp.container.NodePoolNodeConfigGuestAcceleratorGpuDriverInstallationConfigArgs(
                        gpu_driver_version="DEFAULT",
                    ),
                ),
            ],
            
            labels={
                "workload": "gpu-inference-a100",
                "environment": environment,
                "gpu": "a100",
            },

            tags=["cad-coder", environment, "gpu", "a100"],
            
            workload_metadata_config=gcp.container.NodePoolNodeConfigWorkloadMetadataConfigArgs(
                mode="GKE_METADATA",
            ),
        ),
        
        management=gcp.container.NodePoolManagementArgs(
            auto_repair=True,
            auto_upgrade=True,
        ),
    )

    # region agent log
    _agent_log("configured_a100_node_pool", {
        "taints": "removed-explicit-taint",
        "labels": {
            "workload": "gpu-inference-a100",
            "environment": environment,
            "gpu": "a100",
        },
    })
    # endregion agent log
else:
    # region agent log
    _agent_log("skipped_a100_node_pool", {
        "enable_gpu_pools": enable_gpu_pools,
    })
    # endregion agent log

# =============================================================================
# Artifact Registry for Container Images
# =============================================================================

artifact_registry = gcp.artifactregistry.Repository(
    "cad-coder-registry",
    repository_id=f"cad-coder-{environment}",
    location=region,
    project=project,
    format="DOCKER",
    description="Container images for CAD-Coder application",
)

# =============================================================================
# Cloud Storage Buckets
# =============================================================================

# Model artifacts bucket
model_bucket = gcp.storage.Bucket(
    "model-artifacts-bucket",
    name=f"cad-coder-models-{project}-{environment}",
    location=region,
    project=project,
    uniform_bucket_level_access=True,
    versioning=gcp.storage.BucketVersioningArgs(
        enabled=True,
    ),
)

# Data versioning bucket (DVC remote)
data_bucket = gcp.storage.Bucket(
    "data-versioning-bucket",
    name=f"cad-coder-data-{project}-{environment}",
    location=region,
    project=project,
    uniform_bucket_level_access=True,
    versioning=gcp.storage.BucketVersioningArgs(
        enabled=True,
    ),
    lifecycle_rules=[
        gcp.storage.BucketLifecycleRuleArgs(
            action=gcp.storage.BucketLifecycleRuleActionArgs(
                type="Delete",
            ),
            condition=gcp.storage.BucketLifecycleRuleConditionArgs(
                num_newer_versions=5,
            ),
        ),
    ],
)

# =============================================================================
# Secret Manager for Sensitive Configuration
# =============================================================================

def create_secret(name: str, secret_data: str = "") -> gcp.secretmanager.Secret:
    """Create a Secret Manager secret with an initial version."""
    secret = gcp.secretmanager.Secret(
        f"secret-{name}",
        secret_id=f"cad-coder-{name}-{environment}",
        project=project,
        replication=gcp.secretmanager.SecretReplicationArgs(
            auto=gcp.secretmanager.SecretReplicationAutoArgs(),
        ),
    )
    return secret

# Create secrets for sensitive configuration
mongo_uri_secret = create_secret("mongo-uri")
gcp_credentials_secret = create_secret("gcp-credentials")
hf_token_secret = create_secret("hf-token")

# =============================================================================
# Kubernetes Provider (for deploying to GKE)
# =============================================================================

# Generate kubeconfig
kubeconfig = Output.all(
    cluster.name,
    cluster.endpoint,
    cluster.master_auth,
).apply(lambda args: f"""
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: {args[2]["cluster_ca_certificate"]}
    server: https://{args[1]}
  name: {args[0]}
contexts:
- context:
    cluster: {args[0]}
    user: {args[0]}
  name: {args[0]}
current-context: {args[0]}
users:
- name: {args[0]}
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: gke-gcloud-auth-plugin
      installHint: Install gke-gcloud-auth-plugin for use with kubectl by following
        https://cloud.google.com/blog/products/containers-kubernetes/kubectl-auth-changes-in-gke
      provideClusterInfo: true
""")

k8s_provider = k8s.Provider(
    "gke-k8s",
    kubeconfig=kubeconfig,
)

# =============================================================================
# Kubernetes Namespace
# =============================================================================

namespace = k8s.core.v1.Namespace(
    "cad-coder-namespace",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="cad-coder",
        labels={
            "app": "cad-coder",
            "environment": environment,
        },
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider),
)

# =============================================================================
# Exports
# =============================================================================

export("project", project)
export("region", region)
export("zone", zone)
export("cluster_name", cluster.name)
export("cluster_endpoint", cluster.endpoint)
export("kubeconfig", kubeconfig)
export("namespace", namespace.metadata.name)
export("artifact_registry_url", artifact_registry.id.apply(
    lambda id: f"{region}-docker.pkg.dev/{project}/{id.split('/')[-1]}"
))
export("model_bucket", model_bucket.name)
export("data_bucket", data_bucket.name)
if enable_gpu_pools and gpu_node_pool is not None:
    export("gpu_node_pool", gpu_node_pool.name)
if enable_gpu_pools and a100_node_pool is not None:
    export("a100_node_pool", a100_node_pool.name)
