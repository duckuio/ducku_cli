#!/bin/bash

# Docker run script for ducku - convenient wrapper

set -e

IMAGE_NAME="ducku:latest"
PROJECT_PATH="${PROJECT_PATH:-$(pwd)}"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if image exists
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    echo "❌ Docker image '$IMAGE_NAME' not found."
    echo "🔧 Building the image first..."
    ./scripts/docker-build.sh
fi

echo "🐳 Running ducku in Docker container..."
echo "📁 Analyzing project: $PROJECT_PATH"
echo ""

# Run ducku with the specified project path
docker run --rm \
    -v "$PROJECT_PATH:/workspace:ro" \
    -e PROJECT_PATH=/workspace \
    "$IMAGE_NAME" "$@"
