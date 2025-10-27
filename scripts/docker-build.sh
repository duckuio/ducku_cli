#!/bin/bash

# Docker build script for ducku

set -e

IMAGE_NAME="ducku"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo "🐳 Building Docker image for ducku..."

# Build the Docker image
echo "📦 Building image: ${FULL_IMAGE_NAME}"
docker build -t "${FULL_IMAGE_NAME}" .

# Tag with version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/' | tr -d '"')
if [ -n "$VERSION" ]; then
    echo "🏷️  Tagging with version: ${IMAGE_NAME}:${VERSION}"
    docker tag "${FULL_IMAGE_NAME}" "${IMAGE_NAME}:${VERSION}"
fi

echo "✅ Docker image built successfully!"
echo ""
echo "📋 Available images:"
docker images | grep "${IMAGE_NAME}"
echo ""
echo "🚀 Usage examples:"
echo "1. Analyze current directory:"
echo "   docker run --rm -v \$(pwd):/workspace ${FULL_IMAGE_NAME}"
echo ""
echo "2. Analyze specific project:"
echo "   docker run --rm -v /path/to/project:/workspace ${FULL_IMAGE_NAME}"
echo ""
echo "3. Interactive shell:"
echo "   docker run --rm -it -v \$(pwd):/workspace --entrypoint bash ${FULL_IMAGE_NAME}"
echo ""
echo "4. Using docker-compose:"
echo "   PROJECT_PATH=/path/to/project docker-compose run analyze"
