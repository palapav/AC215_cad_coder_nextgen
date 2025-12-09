#!/bin/bash
# Quick setup script for MongoDB Atlas Pulumi infrastructure

set -e

echo "🚀 Setting up MongoDB Atlas infrastructure with Pulumi"
echo ""

# Check if Pulumi is installed
if ! command -v pulumi &> /dev/null; then
    echo "❌ Pulumi CLI is not installed."
    echo "   Install it from: https://www.pulumi.com/docs/get-started/install/"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing Pulumi dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if Pulumi is logged in
if ! pulumi whoami &> /dev/null; then
    echo "🔐 Pulumi login required..."
    pulumi login
fi

# Initialize stack if it doesn't exist
if [ ! -f "Pulumi.dev.yaml" ]; then
    echo "📝 Initializing Pulumi stack..."
    pulumi stack init dev || true
    
    # Copy example config if it exists
    if [ -f "Pulumi.dev.yaml.example" ]; then
        echo "📋 Creating Pulumi.dev.yaml from example..."
        cp Pulumi.dev.yaml.example Pulumi.dev.yaml
    fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Get your MongoDB Atlas Organization ID from: https://cloud.mongodb.com/"
echo "2. Create API keys at: https://cloud.mongodb.com/account/apiKeys"
echo "3. Configure Pulumi:"
echo "   pulumi config set orgId <your-org-id>"
echo "   pulumi config set mongodbatlas:publicKey <your-public-key>"
echo "   pulumi config set --secret mongodbatlas:privateKey <your-private-key>"
echo "   pulumi config set --secret dbPassword <your-password>"
echo ""
echo "4. Deploy:"
echo "   pulumi up"
echo ""

