#!/bin/bash
set -e

# LOOP Frontend Deployment Script
# Builds the Next.js frontend and deploys it to the backend

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${SCRIPT_DIR}/frontend/loop-frontend"
BACKEND_SPA_DIR="${SCRIPT_DIR}/backend/web/spa"
BUILD_OUTPUT_DIR="${FRONTEND_DIR}/out"

echo "🚀 LOOP Frontend Deployment"
echo "================================"

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Frontend directory not found at $FRONTEND_DIR"
    exit 1
fi

# Check if package.json exists
if [ ! -f "$FRONTEND_DIR/package.json" ]; then
    echo "❌ package.json not found in $FRONTEND_DIR"
    exit 1
fi

echo "📁 Frontend dir: $FRONTEND_DIR"
echo "📁 Backend SPA dir: $BACKEND_SPA_DIR"
echo ""

# Navigate to frontend directory
cd "$FRONTEND_DIR"

# Build the frontend
echo "🔨 Building frontend..."
npm run build

# Check if build output exists
if [ ! -d "$BUILD_OUTPUT_DIR" ]; then
    echo "❌ Build output directory not found at $BUILD_OUTPUT_DIR"
    echo "   Make sure your build script produces an 'out' directory"
    exit 1
fi

echo "✅ Build complete!"
echo ""

# Clear existing SPA directory
echo "🧹 Clearing existing SPA directory..."
if [ -d "$BACKEND_SPA_DIR" ]; then
    rm -rf "$BACKEND_SPA_DIR"
    echo "✅ Removed existing SPA directory"
else
    echo "ℹ️  SPA directory didn't exist"
fi

# Create backend SPA directory
mkdir -p "$BACKEND_SPA_DIR"

# Copy build output to backend SPA directory
echo "📦 Copying build output to backend..."
cp -r "$BUILD_OUTPUT_DIR"/* "$BACKEND_SPA_DIR"/

echo "✅ Frontend deployed to backend SPA directory!"
echo ""

# Show some stats
SPA_SIZE=$(du -sh "$BACKEND_SPA_DIR" | cut -f1)
FILE_COUNT=$(find "$BACKEND_SPA_DIR" -type f | wc -l)

echo "📊 Deployment Stats:"
echo "   Size: $SPA_SIZE"
echo "   Files: $FILE_COUNT"
echo ""

echo "🎉 Frontend built and copied to backend/web/spa!" 