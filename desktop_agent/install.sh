#!/bin/bash
set -e

# Docker Agent Installation Script
echo "🐳 Installing Docker Desktop Agent..."

# Configuration
INSTALL_DIR="/opt/docker-agent"
SERVICE_NAME="docker-agent"
CURRENT_USER=$(whoami)

# Check if running as root for installation
if [[ $EUID -eq 0 ]]; then
    echo "✅ Running as root for installation"
else
    echo "❌ This script needs to be run as root (use sudo)"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if user is in docker group
if ! groups $SUDO_USER | grep -q docker; then
    echo "⚠️  User $SUDO_USER is not in docker group. Adding..."
    usermod -aG docker $SUDO_USER
    echo "✅ Added $SUDO_USER to docker group (logout/login required)"
fi

# Create installation directory
echo "📁 Creating installation directory..."
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Copy files (including hidden files)
echo "📋 Copying agent files..."
cp -r /home/$SUDO_USER/Dev/rest_api/desktop_agent/. $INSTALL_DIR/
# Remove the install script from destination to avoid confusion
rm -f $INSTALL_DIR/install.sh

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file from example
if [[ ! -f .env ]]; then
    echo "⚙️  Creating .env configuration file..."
    cp .env.example .env
    echo "⚠️  Please edit /opt/docker-agent/.env with your configuration"
fi

# Create logs directory
mkdir -p $INSTALL_DIR/logs

# Set correct permissions
echo "🔐 Setting permissions..."
chown -R $SUDO_USER:$SUDO_USER $INSTALL_DIR
chmod +x $INSTALL_DIR/docker_agent.py

# Update systemd service file with correct username (if needed)
echo "🔧 Configuring systemd service..."
if grep -q "your-username" docker-agent.service; then
    sed -i "s/your-username/$SUDO_USER/g" docker-agent.service
fi

# Install systemd service
cp docker-agent.service /etc/systemd/system/
systemctl daemon-reload

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit configuration: sudo nano $INSTALL_DIR/.env"
echo "2. Add your API token and URL"
echo "3. Enable service: sudo systemctl enable $SERVICE_NAME"
echo "4. Start service: sudo systemctl start $SERVICE_NAME"
echo "5. Check status: sudo systemctl status $SERVICE_NAME"
echo "6. View logs: sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "⚠️  Remember to logout/login if user was added to docker group"