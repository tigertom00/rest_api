#!/usr/bin/env python3
"""
Docker Desktop Agent
Monitors Docker containers and syncs data to remote Django API
"""

import docker
import requests
import time
import logging
import socket
import json
from datetime import datetime
import os
from pathlib import Path

# Configuration
API_URL = os.getenv('DOCKER_AGENT_API_URL', 'https://api.nxfs.no/api/docker/agent/sync/')
API_TOKEN = os.getenv('DOCKER_AGENT_TOKEN', '')
HOST_NAME = os.getenv('DOCKER_AGENT_HOST_NAME', socket.gethostname())
SYNC_INTERVAL = int(os.getenv('DOCKER_AGENT_INTERVAL', '120'))  # seconds
LOG_LEVEL = os.getenv('DOCKER_AGENT_LOG_LEVEL', 'INFO')

# Setup logging
log_dir = Path('/opt/docker-agent/logs')
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'docker_agent.log'

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class DockerAgent:
    def __init__(self):
        self.docker_client = None
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Token {API_TOKEN}',
            'Content-Type': 'application/json',
            'User-Agent': f'DockerAgent/1.0 ({HOST_NAME})'
        })
        self._connect_docker()

    def _connect_docker(self):
        """Connect to Docker daemon"""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            logger.info("Connected to Docker daemon")
        except Exception as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            self.docker_client = None

    def extract_container_data(self, container):
        """Extract container data in the format expected by Django API"""
        try:
            attrs = container.attrs

            # Parse port mappings
            ports = []
            port_bindings = attrs.get('NetworkSettings', {}).get('Ports', {})
            for container_port, host_bindings in port_bindings.items():
                if host_bindings:
                    for binding in host_bindings:
                        ports.append({
                            'container_port': container_port,
                            'host_ip': binding.get('HostIp', '0.0.0.0'),
                            'host_port': binding.get('HostPort')
                        })

            return {
                'container_id': container.id,
                'name': container.name,
                'image': attrs.get('Config', {}).get('Image', ''),
                'status': container.status,
                'state': attrs.get('State', {}),
                'ports': ports,
                'labels': attrs.get('Config', {}).get('Labels', {}) or {},
                'networks': attrs.get('NetworkSettings', {}).get('Networks', {}),
                'mounts': attrs.get('Mounts', []),
                'created_at': attrs.get('Created'),
                'started_at': attrs.get('State', {}).get('StartedAt'),
                'finished_at': attrs.get('State', {}).get('FinishedAt'),
            }

        except Exception as e:
            logger.error(f"Error extracting data for container {container.id}: {e}")
            return None

    def sync_containers(self):
        """Sync all containers to the API"""
        if not self.docker_client:
            logger.error("Docker client not available")
            return False

        if not API_TOKEN:
            logger.error("API_TOKEN not configured")
            return False

        try:
            # Get all containers
            containers = self.docker_client.containers.list(all=True)
            logger.info(f"Found {len(containers)} containers")

            # Extract container data
            containers_data = []
            for container in containers:
                container_data = self.extract_container_data(container)
                if container_data:
                    containers_data.append(container_data)

            # Prepare payload
            payload = {
                'host': {
                    'name': HOST_NAME,
                    'hostname': socket.getfqdn()
                },
                'containers': containers_data
            }

            # Send to API
            response = self.session.post(API_URL, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully synced {len(containers_data)} containers: {result.get('message', '')}")
                return True
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error syncing containers: {e}")
            return False
        except Exception as e:
            logger.error(f"Error syncing containers: {e}")
            return False

    def run(self):
        """Main run loop"""
        logger.info(f"Starting Docker Agent for host: {HOST_NAME}")
        logger.info(f"API URL: {API_URL}")
        logger.info(f"Sync interval: {SYNC_INTERVAL} seconds")

        while True:
            try:
                if not self.docker_client:
                    logger.info("Attempting to reconnect to Docker...")
                    self._connect_docker()

                if self.docker_client:
                    self.sync_containers()
                else:
                    logger.warning("Docker client not available, retrying in next cycle")

                logger.debug(f"Sleeping for {SYNC_INTERVAL} seconds...")
                time.sleep(SYNC_INTERVAL)

            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(30)  # Wait before retrying


if __name__ == '__main__':
    agent = DockerAgent()
    agent.run()