#!/bin/bash
# Script to configure MongoDB Atlas credentials in Pulumi

set -e

echo "🔐 Configuring MongoDB Atlas credentials for Pulumi"
echo ""

# Check if Pulumi is logged in
if ! pulumi whoami &> /dev/null; then
    echo "⚠️  Pulumi login required. Please run:"
    echo "   pulumi login"
    echo "   (Choose 'Use local file backend' for local development)"
    echo ""
    exit 1
fi

# Initialize or select stack
if ! pulumi stack ls 2>/dev/null | grep -q "dev"; then
    echo "📦 Initializing Pulumi stack 'dev'..."
    pulumi stack init dev
else
    echo "📦 Selecting existing stack 'dev'..."
    pulumi stack select dev
fi

echo ""
echo "🔑 Setting MongoDB Atlas API credentials..."

# Set public key
pulumi config set mongodbatlas:publicKey kszwtxnb

# Set private key as secret
pulumi config set --secret mongodbatlas:privateKey da0676c6-72b5-4e3b-8c83-1d2a13fc204f

echo ""
echo "✅ Credentials configured!"
echo ""
echo "⚠️  You still need to set the database password:"
echo "   pulumi config set --secret dbPassword <your-password>"
echo ""
echo "Then you can deploy with:"
echo "   pulumi up"
echo ""

