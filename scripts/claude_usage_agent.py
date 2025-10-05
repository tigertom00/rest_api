#!/usr/bin/env python3
"""
Claude Usage Agent

This script runs on the desktop PC where Claude stores its data in ~/.claude/
It reads the JSONL files and sends the data to the Django API webhook endpoint.

Usage:
    python claude_usage_agent.py

Setup as cron job (run every 5 minutes):
    */5 * * * * /usr/bin/python3 /path/to/claude_usage_agent.py

Or as systemd timer (recommended)
"""

import os
import json
import glob
import sys
import requests
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timezone


class ClaudeDataExtractor:
    """Extracts Claude usage data from local JSONL files"""

    def __init__(self, claude_path: str = "~/.claude"):
        self.claude_path = os.path.expanduser(claude_path)
        self.projects_path = os.path.join(self.claude_path, "projects")

    def get_all_projects(self) -> List[str]:
        """Get all project directories"""
        if not os.path.exists(self.projects_path):
            return []

        return [
            d
            for d in os.listdir(self.projects_path)
            if os.path.isdir(os.path.join(self.projects_path, d))
        ]

    def get_project_sessions(self, project_name: str) -> List[str]:
        """Get all sessions for a project"""
        project_path = os.path.join(self.projects_path, project_name)
        pattern = os.path.join(project_path, "*.jsonl")
        return glob.glob(pattern)

    def parse_session_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse a single session JSONL file"""
        messages = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if data.get("type") == "assistant":
                                messages.append(data)
                        except json.JSONDecodeError:
                            continue
        except (IOError, OSError) as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return messages

    def extract_usage_data(self, hours_back: int = 6) -> List[Dict[str, Any]]:
        """
        Extract usage data for sending to webhook.
        Only includes messages from the last N hours to reduce payload size.

        Args:
            hours_back: How many hours of data to include (default: 6)
        """
        from datetime import datetime, timedelta, timezone

        # Calculate cutoff time
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        all_projects = []

        for project in self.get_all_projects():
            project_data = {
                "name": project,
                "path": f"{self.claude_path}/projects/{project}",
                "sessions": [],
            }

            for session_file in self.get_project_sessions(project):
                all_messages = self.parse_session_file(session_file)

                if not all_messages:
                    continue

                # Filter messages to only recent ones
                recent_messages = []
                for msg in all_messages:
                    try:
                        msg_time = datetime.fromisoformat(
                            msg["timestamp"].replace("Z", "+00:00")
                        )
                        if msg_time >= cutoff:
                            recent_messages.append(msg)
                    except (ValueError, KeyError):
                        # Include message if we can't parse timestamp
                        recent_messages.append(msg)

                if not recent_messages:
                    continue

                # Extract session ID from first message
                session_id = recent_messages[0].get("sessionId", "unknown")

                session_data = {
                    "session_id": session_id,
                    "messages": recent_messages,
                }

                project_data["sessions"].append(session_data)

            if project_data["sessions"]:
                all_projects.append(project_data)

        return all_projects


class ClaudeUsageAgent:
    """Agent that sends Claude usage data to Django API"""

    def __init__(
        self,
        api_url: str,
        api_token: str,
        claude_path: str = "~/.claude",
    ):
        self.api_url = api_url.rstrip("/")
        self.api_token = api_token
        self.extractor = ClaudeDataExtractor(claude_path)

    def sync_data(self) -> Dict[str, Any]:
        """Extract and send data to API"""
        print(f"[{datetime.now().isoformat()}] Starting Claude usage sync...")

        # Extract data
        projects_data = self.extractor.extract_usage_data()

        if not projects_data:
            print("No Claude usage data found")
            return {"status": "no_data"}

        # Prepare payload
        payload = {"projects": projects_data}

        # Send to webhook
        headers = {
            "Authorization": self.api_token,  # Token is already formatted (e.g., "Token xyz" or "Bearer xyz")
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                f"{self.api_url}/app/claude-usage/agent-sync/",
                json=payload,
                headers=headers,
                timeout=120,  # Increased timeout for large payloads
            )

            response.raise_for_status()
            result = response.json()

            print(f"✓ Sync successful: {result.get('message')}")
            print(f"  Projects: {result.get('projects_updated', 0)}")
            print(f"  Sessions: {result.get('sessions_updated', 0)}")
            print(f"  Snapshots: {result.get('snapshots_created', 0)}")

            return result

        except requests.exceptions.RequestException as e:
            print(f"✗ Sync failed: {e}", file=sys.stderr)
            return {"status": "error", "error": str(e)}


def main():
    """Main entry point"""
    # Configuration from environment variables
    API_URL = os.getenv("CLAUDE_USAGE_API_URL", "http://localhost:8000")
    API_TOKEN = os.getenv("CLAUDE_USAGE_API_TOKEN", "")
    CLAUDE_PATH = os.getenv("CLAUDE_PATH", "~/.claude")

    if not API_TOKEN:
        print(
            "Error: CLAUDE_USAGE_API_TOKEN environment variable not set",
            file=sys.stderr,
        )
        print(
            "Please set it to your Django API JWT token or authentication token",
            file=sys.stderr,
        )
        sys.exit(1)

    agent = ClaudeUsageAgent(
        api_url=API_URL,
        api_token=API_TOKEN,
        claude_path=CLAUDE_PATH,
    )

    result = agent.sync_data()

    if result.get("status") == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
