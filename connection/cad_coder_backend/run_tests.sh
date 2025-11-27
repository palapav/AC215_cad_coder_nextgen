#!/bin/bash
# Test runner script for local development

set -e

echo "🧪 Running CAD-Coder Backend Tests"
echo "===================================="

# Check if MongoDB is running (optional, tests use mocks by default)
if command -v mongosh &> /dev/null; then
    if mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
        echo "✅ MongoDB is running"
        export MONGO_URI=${MONGO_URI:-"mongodb://localhost:27017"}
        export MONGO_DB=${MONGO_DB:-"cad_coder_test"}
    else
        echo "⚠️  MongoDB not running, tests will use mocks"
    fi
else
    echo "⚠️  MongoDB client not found, tests will use mocks"
fi

# Install dependencies if needed
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    pip install pytest pytest-cov pytest-asyncio black ruff
fi

# Run linting
echo ""
echo "🔍 Running linters..."
ruff check app/ --output-format=github || echo "⚠️  Ruff found issues (non-blocking)"
black --check app/ || echo "⚠️  Black found formatting issues (non-blocking)"

# Run tests with coverage
echo ""
echo "🧪 Running tests with coverage..."
pytest app/tests/ -v \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=xml

# Check coverage threshold
echo ""
echo "📊 Checking coverage threshold..."
coverage report --fail-under=50

echo ""
echo "✅ All tests completed!"
echo "📁 HTML coverage report: htmlcov/index.html"

