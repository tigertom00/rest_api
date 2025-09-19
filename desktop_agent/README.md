# Docker Desktop Agent

A lightweight Python agent that monitors Docker containers on your desktop and syncs data to your Django REST API.

## Features

- 🐳 Monitors all Docker containers (running and stopped)
- 📊 Syncs container metadata, ports, networks, and mount information
- 🔄 Automatic periodic synchronization (configurable interval)
- 🛡️ Secure authentication via JWT tokens
- 📝 Comprehensive logging
- 🔧 Systemd service with auto-restart
- 🐍 Isolated Python virtual environment

## Installation

1. **Clone or copy the agent files to your desktop:**
   ```bash
   # Files needed:
   # - docker_agent.py
   # - requirements.txt
   # - docker-agent.service
   # - .env.example
   # - install.sh
   ```

2. **Run the installation script:**
   ```bash
   sudo ./install.sh
   ```

3. **Configure the agent:**
   ```bash
   sudo nano /opt/docker-agent/.env
   ```

   Update these values:
   ```
   DOCKER_AGENT_API_URL=https://your-api-domain.com/api/docker/agent/sync/
   DOCKER_AGENT_TOKEN=your_jwt_token_here
   DOCKER_AGENT_HOST_NAME=desktop-pc
   ```

4. **Enable and start the service:**
   ```bash
   sudo systemctl enable docker-agent
   sudo systemctl start docker-agent
   ```

## Management

### Check status:
```bash
sudo systemctl status docker-agent
```

### View logs:
```bash
sudo journalctl -u docker-agent -f
```

### Restart service:
```bash
sudo systemctl restart docker-agent
```

### Stop service:
```bash
sudo systemctl stop docker-agent
```

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCKER_AGENT_API_URL` | - | Your Django API webhook URL |
| `DOCKER_AGENT_TOKEN` | - | JWT token for authentication |
| `DOCKER_AGENT_HOST_NAME` | hostname | Display name for this host |
| `DOCKER_AGENT_INTERVAL` | 120 | Sync interval in seconds |
| `DOCKER_AGENT_LOG_LEVEL` | INFO | Log level (DEBUG, INFO, WARNING, ERROR) |

## Getting Your JWT Token

1. Login to your Django admin or API
2. Create a token for API access
3. Use the token in the `.env` file

## Troubleshooting

### Permission Denied for Docker Socket
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again
```

### Check Docker Connection
```bash
# Test Docker access
docker ps
```

### View Detailed Logs
```bash
# Enable debug logging
sudo nano /opt/docker-agent/.env
# Set: DOCKER_AGENT_LOG_LEVEL=DEBUG
sudo systemctl restart docker-agent
```

## Security

- Agent runs as unprivileged user
- Secure systemd service configuration
- JWT token authentication
- Read-only Docker socket access
- Private temporary directories

## Uninstallation

```bash
sudo systemctl stop docker-agent
sudo systemctl disable docker-agent
sudo rm /etc/systemd/system/docker-agent.service
sudo rm -rf /opt/docker-agent
sudo systemctl daemon-reload
```