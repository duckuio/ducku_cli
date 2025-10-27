#!/bin/bash

# Build and distribute script for ducku

set -e

echo "🔧 Building ducku package..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Build the package - try UV first, fall back to regular python
echo "📦 Building wheel and source distribution..."
if command -v uv >/dev/null 2>&1 && uv tool list | grep -q build; then
    echo "Using UV build tool..."
    uv tool run --from build pyproject-build
elif python -c "import build" >/dev/null 2>&1; then
    echo "Using system build module..."
    python -m build
else
    echo "❌ Neither UV build tool nor python build module found!"
    echo "Please install with: pip install build  OR  uv tool install build"
    exit 1
fi

# Check the built package - try UV first, fall back to regular python
echo "🔍 Checking built package..."
if command -v uv >/dev/null 2>&1 && uv tool list | grep -q twine; then
    echo "Using UV twine tool..."
    uv tool run twine check dist/*
elif python -c "import twine" >/dev/null 2>&1; then
    echo "Using system twine module..."
    python -m twine check dist/*
else
    echo "⚠️ Neither UV twine tool nor python twine module found!"
    echo "Skipping package check. Install with: pip install twine  OR  uv tool install twine"
fi

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
