#!/bin/bash

# =====================================================
# Docker Helper Script for CAD-Coder UI
# =====================================================

set -e

IMAGE_NAME="cad-coder-ui"
CONTAINER_NAME="cad-coder-ui-container"
HOST_PORT=8080
CONTAINER_PORT=80

echo "🐳 CAD-Coder UI - Docker Helper Script"
echo "========================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Parse command line arguments
case "${1:-}" in
    build)
        echo "🔨 Building Docker image: $IMAGE_NAME"
        docker build -t $IMAGE_NAME .
        echo "✅ Build complete!"
        ;;
    run)
        echo "🚀 Running Docker container: $CONTAINER_NAME"
        
        # Stop and remove existing container if it exists
        if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
            echo "🛑 Stopping existing container..."
            docker stop $CONTAINER_NAME > /dev/null 2>&1 || true
            echo "🗑️  Removing existing container..."
            docker rm $CONTAINER_NAME > /dev/null 2>&1 || true
        fi
        
        # Run new container
        docker run -d -p $HOST_PORT:$CONTAINER_PORT --name $CONTAINER_NAME $IMAGE_NAME
        echo "✅ Container started successfully!"
        echo "🌐 Access the UI at: http://localhost:$HOST_PORT"
        ;;
    stop)
        echo "🛑 Stopping container: $CONTAINER_NAME"
        docker stop $CONTAINER_NAME
        echo "✅ Container stopped!"
        ;;
    logs)
        echo "📋 Showing logs for: $CONTAINER_NAME"
        docker logs -f $CONTAINER_NAME
        ;;
    clean)
        echo "🧹 Cleaning up Docker resources..."
        docker stop $CONTAINER_NAME > /dev/null 2>&1 || true
        docker rm $CONTAINER_NAME > /dev/null 2>&1 || true
        docker rmi $IMAGE_NAME > /dev/null 2>&1 || true
        echo "✅ Cleanup complete!"
        ;;
    rebuild)
        echo "🔄 Rebuilding and restarting..."
        $0 clean
        $0 build
        $0 run
        ;;
    *)
        echo "Usage: $0 {build|run|stop|logs|clean|rebuild}"
        echo ""
        echo "Commands:"
        echo "  build    - Build the Docker image"
        echo "  run      - Run the Docker container (stops existing if running)"
        echo "  stop     - Stop the running container"
        echo "  logs     - View container logs (live)"
        echo "  clean    - Remove container and image"
        echo "  rebuild  - Clean, build, and run in one command"
        echo ""
        echo "Quick start:"
        echo "  ./docker-run.sh rebuild"
        exit 1
        ;;
esac

