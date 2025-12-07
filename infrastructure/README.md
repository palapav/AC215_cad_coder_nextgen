# MongoDB Atlas Infrastructure with Pulumi

This directory contains Pulumi infrastructure-as-code for provisioning and managing MongoDB Atlas resources for the CAD-Coder project.

## What This Provisions

- **MongoDB Atlas Cluster**: Managed MongoDB cluster (M0 free tier by default)
- **Database User**: Authenticated user with read/write and admin roles
- **Network Access**: IP allowlist for secure access
- **Connection String**: Automatically generated MongoDB connection URI

## Prerequisites

1. **MongoDB Atlas Account**: Sign up at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. **MongoDB Atlas API Keys**: 
   - Go to MongoDB Atlas → Access Manager → API Keys
   - Create an API key with "Organization Owner" or "Project Owner" permissions
   - Save the Public Key and Private Key
3. **Pulumi CLI**: Install from [pulumi.com](https://www.pulumi.com/docs/get-started/install/)
4. **Python 3.8+**: Required for Pulumi Python runtime

## Setup Instructions

### 1. Install Dependencies

```bash
cd infrastructure
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Pulumi

#### Login to Pulumi (if not already logged in)

```bash
pulumi login
# Choose: Use local file backend (or cloud if you prefer)
```

#### Configure MongoDB Atlas API Credentials

```bash
# Set MongoDB Atlas public key
pulumi config set mongodbatlas:publicKey <your-public-key>

# Set MongoDB Atlas private key (stored as secret)
pulumi config set --secret mongodbatlas:privateKey <your-private-key>
```

#### Get Your Organization ID

1. Go to MongoDB Atlas → Settings → Organizations
2. Copy your Organization ID
3. Set it in Pulumi config:

```bash
pulumi config set orgId <your-organization-id>
```

#### Set Database Password

```bash
pulumi config set --secret dbPassword <your-secure-password>
```

### 3. Review Configuration

Edit `Pulumi.dev.yaml` to customize:
- `projectName`: MongoDB Atlas project name
- `clusterName`: Cluster name
- `region`: AWS region (e.g., `US_EAST_1`, `US_WEST_2`)
- `instanceSize`: Cluster tier (`M0` = free, `M10` = paid, etc.)
- `dbUsername`: Database username
- `allowedIps`: List of IP addresses allowed to connect

### 4. Deploy Infrastructure

```bash
# Preview changes
pulumi preview

# Deploy
pulumi up
```

### 5. Get Connection String

After deployment, get the connection string:

```bash
pulumi stack output mongo_uri
```

Or view all outputs:

```bash
pulumi stack output
```

### 6. Update Your Application

Add the connection string to your `.env` file:

```bash
# In src/.env
MONGO_URI=$(pulumi stack output mongo_uri)
MONGO_DB=cad_coder
```

## Configuration Options

### Instance Sizes

- `M0`: Free tier (shared, 512MB storage)
- `M2`: $9/month (shared, 2GB storage)
- `M5`: $25/month (shared, 5GB storage)
- `M10+`: Dedicated instances (higher performance)

### Regions

Common AWS regions:
- `US_EAST_1` (N. Virginia)
- `US_WEST_2` (Oregon)
- `EU_WEST_1` (Ireland)
- `AP_SOUTHEAST_1` (Singapore)

### Network Security

For production, restrict IP access:

```yaml
allowedIps:
  - "1.2.3.4/32"  # Specific IP
  - "10.0.0.0/8"  # Private network range
```

Remove `0.0.0.0/0` (allows all IPs) for production environments.

## Stack Management

### Create Additional Stacks

```bash
# Create production stack
pulumi stack init prod
pulumi config set orgId <your-org-id> --stack prod
pulumi config set --secret dbPassword <prod-password> --stack prod
pulumi config set instanceSize M10 --stack prod  # Use paid tier for prod
```

### Switch Between Stacks

```bash
pulumi stack select dev    # Switch to dev
pulumi stack select prod   # Switch to prod
```

### Destroy Infrastructure

```bash
# Remove all resources
pulumi destroy
```

## Troubleshooting

### Error: "Organization not found"
- Verify your `orgId` is correct
- Ensure your API key has organization-level permissions

### Error: "Invalid API credentials"
- Check that public/private keys are set correctly
- Verify keys haven't expired in MongoDB Atlas

### Cluster takes time to provision
- M0 clusters typically take 3-5 minutes
- Paid tiers may take longer (10-15 minutes)
- Check status in MongoDB Atlas console

### Connection string not available
- Wait for cluster to finish provisioning
- Run `pulumi refresh` to sync state
- Check cluster status: `pulumi stack output cluster_id`

## Integration with Docker Compose

This Pulumi setup is for **production/cloud MongoDB**. For local development, continue using Docker Compose:

```bash
# Local development (uses Docker Compose MongoDB)
cd src/cad_coder_backend
docker compose up -d mongo

# Production (uses MongoDB Atlas from Pulumi)
# Set MONGO_URI from Pulumi output in your .env
```

## Cost Considerations

- **M0 (Free Tier)**: Free forever, suitable for development
- **M2+ (Paid)**: Starts at $9/month, required for production workloads
- **Data Transfer**: Free up to certain limits, then charged per GB

Monitor usage in MongoDB Atlas console.

