"""
MongoDB Atlas infrastructure provisioned with Pulumi.

This module provisions:
- MongoDB Atlas cluster (M0 free tier by default)
- Database user with authentication
- Network access (IP allowlist)
- Outputs connection string for application use
"""
import urllib.parse
import pulumi
import pulumi_mongodbatlas as mongodbatlas

# Get configuration values
config = pulumi.Config()

# MongoDB Atlas configuration
org_id = config.require("orgId")
project_name = config.get("projectName", "cad-coder-nextgen")
cluster_name = config.get("clusterName", "cad-coder-cluster")
region = config.get("region", "US_EAST_1")  # Default to US East
instance_size = config.get("instanceSize", "M0")  # M0 is free tier

# Database user configuration
db_username = config.get("dbUsername", "cad-coder-user")
db_password = config.require_secret("dbPassword")

# Network access configuration
# Allow all IPs by default (0.0.0.0/0) - you can restrict this in production
allowed_ips = config.get_object("allowedIps", ["0.0.0.0/0"])

# Create MongoDB Atlas project
atlas_project = mongodbatlas.Project(
    "cad-coder-project",
    name=project_name,
    org_id=org_id,
)

# Create MongoDB Atlas cluster
cluster = mongodbatlas.Cluster(
    "cad-coder-cluster",
    project_id=atlas_project.id,
    name=cluster_name,
    provider_name="TENANT",
    backing_provider_name="AWS",
    provider_region_name=region,
    provider_instance_size_name=instance_size,
    mongo_db_major_version="6.0",
    # Enable backup for production (disabled for M0 free tier)
    provider_backup_enabled=False,
    # Auto-scaling (not available for M0)
    auto_scaling_disk_gb_enabled=False,
    opts=pulumi.ResourceOptions(depends_on=[atlas_project]),
)

# Create database user
db_user = mongodbatlas.DatabaseUser(
    "cad-coder-db-user",
    project_id=atlas_project.id,
    username=db_username,
    password=db_password,
    auth_database_name="admin",
    roles=[
        mongodbatlas.DatabaseUserRoleArgs(
            role_name="readWrite",
            database_name="cad_coder",  # Default database name
        ),
        mongodbatlas.DatabaseUserRoleArgs(
            role_name="dbAdmin",
            database_name="cad_coder",
        ),
    ],
    opts=pulumi.ResourceOptions(depends_on=[atlas_project]),
)

# Configure network access (IP allowlist)
# Add IP addresses to allowlist
for i, ip in enumerate(allowed_ips):
    mongodbatlas.ProjectIpAccessList(
        f"ip-access-{i}",
        project_id=atlas_project.id,
        ip_address=ip,
        comment=f"CAD-Coder access from {ip}",
        opts=pulumi.ResourceOptions(depends_on=[atlas_project]),
    )

# Output important information
pulumi.export("project_id", atlas_project.id)
pulumi.export("cluster_id", cluster.id)
pulumi.export("cluster_name", cluster.name)
pulumi.export("database_name", "cad_coder")
pulumi.export("database_username", db_username)

# Connection strings (available after cluster is provisioned)
cluster_connection_strings = cluster.connection_strings

# Standard connection string (without credentials)
pulumi.export("cluster_connection_string", cluster_connection_strings.apply(
    lambda cs: cs.standard_srv if cs and hasattr(cs, "standard_srv") else "Not available yet"
))

# Full MongoDB URI with credentials (URL-encode password)
def build_mongo_uri(connection_strings, username, password):
    """Build MongoDB URI with credentials."""
    if not connection_strings or not hasattr(connection_strings, "standard_srv") or not connection_strings.standard_srv:
        return "Connection string will be available after cluster is created"
    
    # Extract host from connection string (format: mongodb+srv://cluster-name.mongodb.net/...)
    conn_str = connection_strings.standard_srv
    # Remove mongodb+srv:// prefix and extract host
    if "mongodb+srv://" in conn_str:
        host_part = conn_str.replace("mongodb+srv://", "").split("/")[0]
    else:
        host_part = conn_str.split("//")[1].split("/")[0] if "//" in conn_str else conn_str
    
    # URL-encode password to handle special characters
    encoded_password = urllib.parse.quote_plus(password)
    
    return f"mongodb+srv://{username}:{encoded_password}@{host_part}/cad_coder?retryWrites=true&w=majority"

pulumi.export("mongo_uri", pulumi.Output.all(
    cluster_connection_strings,
    db_username,
    db_password,
).apply(lambda args: build_mongo_uri(args[0], args[1], args[2])))

