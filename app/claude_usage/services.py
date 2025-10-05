import os
import json
import glob
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from django.utils import timezone


class ClaudeDataExtractor:
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
                            if (
                                data.get("type") == "assistant"
                            ):  # Only assistant messages have usage
                                messages.append(data)
                        except json.JSONDecodeError:
                            continue
        except (IOError, OSError):
            # Handle file access errors gracefully
            pass
        return messages

    def get_project_data(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed data for a specific project"""
        if project_name not in self.get_all_projects():
            return None

        project_data = {"project_name": project_name, "sessions": []}

        for session_file in self.get_project_sessions(project_name):
            messages = self.parse_session_file(session_file)

            if not messages:
                continue

            # Calculate session totals
            total_input = sum(
                m["message"]["usage"].get("input_tokens", 0) for m in messages
            )
            total_output = sum(
                m["message"]["usage"].get("output_tokens", 0) for m in messages
            )
            total_cache_creation = sum(
                m["message"]["usage"].get("cache_creation_input_tokens", 0)
                for m in messages
            )
            total_cache_read = sum(
                m["message"]["usage"].get("cache_read_input_tokens", 0)
                for m in messages
            )

            session_data = {
                "session_id": messages[0].get("sessionId", "unknown"),
                "file_path": session_file,
                "message_count": len(messages),
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_cache_creation_tokens": total_cache_creation,
                "total_cache_read_tokens": total_cache_read,
                "total_tokens": total_input
                + total_output
                + total_cache_creation
                + total_cache_read,
                "messages": messages,
            }

            project_data["sessions"].append(session_data)

        return project_data

    def extract_usage_data(self) -> List[Dict[str, Any]]:
        """Extract all usage data"""
        all_data = []

        for project in self.get_all_projects():
            project_data = self.get_project_data(project)
            if project_data:
                all_data.append(project_data)

        return all_data

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get overall usage statistics"""
        data = self.extract_usage_data()

        # Calculate totals
        total_tokens = sum(
            session["total_tokens"]
            for project in data
            for session in project["sessions"]
        )

        total_input_tokens = sum(
            session["total_input_tokens"]
            for project in data
            for session in project["sessions"]
        )

        total_output_tokens = sum(
            session["total_output_tokens"]
            for project in data
            for session in project["sessions"]
        )

        total_cache_creation_tokens = sum(
            session["total_cache_creation_tokens"]
            for project in data
            for session in project["sessions"]
        )

        total_cache_read_tokens = sum(
            session["total_cache_read_tokens"]
            for project in data
            for session in project["sessions"]
        )

        total_sessions = sum(len(project["sessions"]) for project in data)

        total_messages = sum(
            session["message_count"]
            for project in data
            for session in project["sessions"]
        )

        return {
            "total_tokens": total_tokens,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_cache_creation_tokens": total_cache_creation_tokens,
            "total_cache_read_tokens": total_cache_read_tokens,
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "projects": len(data),
            "projects_data": data,
        }

    def calculate_cost(self, message: Dict[str, Any]) -> float:
        """Calculate cost for a message based on token usage and model"""
        # Claude pricing (approximate, may need updating)
        pricing = {
            "claude-sonnet-4-20250514": {
                "input": 0.015,  # per 1K tokens
                "output": 0.075,  # per 1K tokens
                "cache_creation": 0.0375,  # per 1K tokens
                "cache_read": 0.00375,  # per 1K tokens
            },
            "claude-3-5-sonnet-20241022": {
                "input": 0.003,
                "output": 0.015,
                "cache_creation": 0.0075,
                "cache_read": 0.00075,
            },
        }

        model = message["message"].get("model", "claude-sonnet-4-20250514")
        usage = message["message"]["usage"]

        if model not in pricing:
            model = "claude-sonnet-4-20250514"

        rates = pricing[model]

        input_cost = (usage.get("input_tokens", 0) / 1000) * rates["input"]
        output_cost = (usage.get("output_tokens", 0) / 1000) * rates["output"]
        cache_creation_cost = (
            usage.get("cache_creation_input_tokens", 0) / 1000
        ) * rates["cache_creation"]
        cache_read_cost = (usage.get("cache_read_input_tokens", 0) / 1000) * rates[
            "cache_read"
        ]

        return input_cost + output_cost + cache_creation_cost + cache_read_cost

    def calculate_rate_limit_windows(
        self, messages: List[Dict[str, Any]], window_hours: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Group messages into rate limit windows (default 5 hours).
        Each window starts from the first message timestamp.
        """
        if not messages:
            return []

        # Sort messages by timestamp
        sorted_messages = sorted(
            messages,
            key=lambda m: datetime.fromisoformat(m["timestamp"].replace("Z", "+00:00")),
        )

        windows = []
        current_window = None
        window_duration = timedelta(hours=window_hours)

        for msg in sorted_messages:
            msg_time = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))

            # Start new window if needed
            if current_window is None or msg_time >= current_window["end_time"]:
                if current_window:
                    windows.append(current_window)

                current_window = {
                    "start_time": msg_time,
                    "end_time": msg_time + window_duration,
                    "messages": [],
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cache_creation_tokens": 0,
                    "cache_read_tokens": 0,
                }

            # Add message to current window
            current_window["messages"].append(msg)
            usage = msg["message"]["usage"]
            current_window["input_tokens"] += usage.get("input_tokens", 0)
            current_window["output_tokens"] += usage.get("output_tokens", 0)
            current_window["cache_creation_tokens"] += usage.get(
                "cache_creation_input_tokens", 0
            )
            current_window["cache_read_tokens"] += usage.get(
                "cache_read_input_tokens", 0
            )
            current_window["total_tokens"] = (
                current_window["input_tokens"]
                + current_window["output_tokens"]
                + current_window["cache_creation_tokens"]
                + current_window["cache_read_tokens"]
            )

        # Add last window
        if current_window:
            windows.append(current_window)

        return windows

    def get_current_rate_limit_status(self, window_hours: int = 5) -> Dict[str, Any]:
        """
        Calculate current rate limit status including time until reset.
        """
        # Get all messages from all projects
        all_messages = []
        for project in self.get_all_projects():
            project_data = self.get_project_data(project)
            if project_data:
                for session in project_data["sessions"]:
                    all_messages.extend(session["messages"])

        if not all_messages:
            return {
                "current_window_tokens": 0,
                "current_window_start": None,
                "next_reset_at": None,
                "time_until_reset_seconds": None,
                "time_until_reset_human": None,
                "is_within_active_window": False,
            }

        # Calculate windows
        windows = self.calculate_rate_limit_windows(all_messages, window_hours)

        if not windows:
            return {
                "current_window_tokens": 0,
                "current_window_start": None,
                "next_reset_at": None,
                "time_until_reset_seconds": None,
                "time_until_reset_human": None,
                "is_within_active_window": False,
            }

        # Get the most recent window
        latest_window = windows[-1]
        now = timezone.now()

        # Check if we're still within the latest window
        is_within_active_window = now < latest_window["end_time"]

        if is_within_active_window:
            time_until_reset = latest_window["end_time"] - now
            time_until_reset_seconds = int(time_until_reset.total_seconds())

            # Format human-readable time
            hours = time_until_reset_seconds // 3600
            minutes = (time_until_reset_seconds % 3600) // 60
            time_until_reset_human = f"{hours}h {minutes}m remaining"

            return {
                "current_window_tokens": latest_window["total_tokens"],
                "current_window_start": latest_window["start_time"].isoformat(),
                "next_reset_at": latest_window["end_time"].isoformat(),
                "time_until_reset_seconds": time_until_reset_seconds,
                "time_until_reset_human": time_until_reset_human,
                "is_within_active_window": True,
                "window_details": {
                    "input_tokens": latest_window["input_tokens"],
                    "output_tokens": latest_window["output_tokens"],
                    "cache_creation_tokens": latest_window["cache_creation_tokens"],
                    "cache_read_tokens": latest_window["cache_read_tokens"],
                },
            }
        else:
            # Window has expired, limits have reset
            return {
                "current_window_tokens": 0,
                "current_window_start": None,
                "next_reset_at": None,
                "time_until_reset_seconds": None,
                "time_until_reset_human": "Limits have reset",
                "is_within_active_window": False,
            }
