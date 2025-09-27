#!/bin/bash

set -e

echo "🚀 Starting server update process..."

echo "📁 Downloading latest files from server via SFTP..."
if sftp 10.20.30.202 << 'EOF'
get -r /home/tiger/Dev/rest_api/srv
get -r /home/tiger/Dev/rest_api/restAPI
get -r /home/tiger/Dev/rest_api/app
bye
EOF
then
    echo "✅ Files downloaded successfully"
else
    echo "❌ Failed to download files from server"
    exit 1
fi

echo "🐍 Installing Python packages..."
if docker exec -u tiger restapi_django pip install -r requirements.txt; then
    echo "✅ Python packages installed successfully"
else
    echo "❌ Failed to install Python packages"
    exit 1
fi

echo "🔄 Restarting Django container..."
if docker restart restapi_django; then
    echo "✅ Django container restarted successfully"
else
    echo "❌ Failed to restart Django container"
    exit 1
fi

echo "🎉 Server update completed successfully!"
