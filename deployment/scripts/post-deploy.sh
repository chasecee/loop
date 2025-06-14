#!/bin/bash
set -e

# LOOP Post-Deployment Script
# This script runs after deployment to handle any necessary cleanup or updates

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
SERVICE_NAME="vidbox"

echo "🔧 LOOP Post-Deployment Script"
echo "================================"

cd "$PROJECT_DIR"

# Update Python dependencies if requirements changed
if [ -f requirements.txt ]; then
    echo "📚 Updating Python dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Run database migrations or config updates if needed
echo "⚙️  Checking configuration..."
if [ -f deployment/scripts/migrate-config.py ]; then
    echo "Running configuration migration..."
    source venv/bin/activate
    python deployment/scripts/migrate-config.py
fi

# Set proper permissions
echo "🔒 Setting file permissions..."
find . -name "*.py" -exec chmod 644 {} \;
find . -name "*.sh" -exec chmod +x {} \;
chmod +x main.py 2>/dev/null || true

# Clear Python cache
echo "🧹 Clearing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Restart systemd service
echo "🔄 Reloading systemd configuration..."
sudo systemctl daemon-reload

# Test the application
echo "🧪 Testing application..."
source venv/bin/activate
if python -c "from config.schema import Config; print('✅ Configuration test passed')" 2>/dev/null; then
    echo "✅ Application test passed"
else
    echo "❌ Application test failed"
    exit 1
fi

# Log deployment completion
echo "$(date): Post-deployment completed successfully" >> ~/.vidbox/logs/deployment.log

echo "✅ Post-deployment completed successfully!" 