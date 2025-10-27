#!/bin/bash

# Build and distribute script for ducku

set -e

echo "🔧 Building ducku package..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Build the package
echo "📦 Building wheel and source distribution..."
python -m build

# Check the built package
echo "🔍 Checking built package..."
python -m twine check dist/*

echo "✅ Build complete!"
echo ""
echo "📋 Next steps:"
echo "1. Test the package locally:"
echo "   pip install dist/ducku-*.whl"
echo ""
echo "2. Upload to PyPI (test):"
echo "   python -m twine upload --repository testpypi dist/*"
echo ""
echo "3. Upload to PyPI (production):"
echo "   python -m twine upload dist/*"
echo ""
echo "📁 Built files are in ./dist/"
ls -la dist/
