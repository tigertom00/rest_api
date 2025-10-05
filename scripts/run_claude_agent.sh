#!/bin/bash
# Wrapper script for Claude Usage Agent cron job

export CLAUDE_USAGE_API_URL="https://api.nxfs.no"
export CLAUDE_USAGE_API_TOKEN="Token 6b06fbf0ad21caa9298985caf9de4d9332cbebbf"
export CLAUDE_PATH="~/.claude"

/usr/bin/python3 /home/tiger/Dev/rest_api/scripts/claude_usage_agent.py
