#!/bin/bash

set -e

echo "🚀 Starting deployment process..."

echo "📥 Pulling latest changes from git..."
if git pull; then
    echo "✅ Git pull successful"
else
    echo "❌ Git pull failed"
    exit 1
fi

echo "🔄 Restarting Django container..."
if docker compose restart django; then
    echo "✅ Django container restarted successfully"
else
    echo "❌ Failed to restart Django container"
    exit 1
fi

echo "📦 Installing/updating Python packages..."
if docker compose exec -u tiger django pip install -r requirements.txt; then
    echo "✅ Python packages installed successfully"
else
    echo "❌ Failed to install Python packages"
    exit 1
fi

echo "🔄 Restarting Django container to load new packages..."
if docker compose restart django; then
    echo "✅ Django container restarted successfully"
else
    echo "❌ Failed to restart Django container"
    exit 1
fi

echo "🎉 Deployment completed successfully!"
