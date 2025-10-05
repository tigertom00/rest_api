# Claude Usage Monitoring

This Django app tracks Claude AI usage and provides rate limit information including time until the next 5-hour reset.

## Features

- 📊 Track token usage across all projects and sessions
- ⏰ Calculate time until next 5-hour rate limit reset
- 📈 Historical usage data and cost calculations
- 🔄 Webhook endpoint for remote data collection
- 💰 Cost tracking per message and session

## Architecture

The app uses a **webhook-based architecture** similar to the `docker_monitor` app:

1. **Desktop PC**: Runs agent script that reads `~/.claude/` files
2. **Agent Script**: Sends data to Django API webhook
3. **Django API**: Stores and processes usage data
4. **Frontend**: Queries API for usage stats and rate limit info

## API Endpoints

### GET `/app/claude-usage/stats/`
Get overall usage statistics with rate limit information.

**Response:**
```json
{
  "total_tokens": 150000,
  "total_input_tokens": 100000,
  "total_output_tokens": 50000,
  "total_cache_creation_tokens": 20000,
  "total_cache_read_tokens": 10000,
  "total_sessions": 15,
  "total_messages": 234,
  "projects": 3,
  "current_window_tokens": 45000,
  "current_window_start": "2025-10-05T10:30:00Z",
  "next_reset_at": "2025-10-05T15:30:00Z",
  "time_until_reset_seconds": 7200,
  "time_until_reset_human": "2h 0m remaining",
  "is_within_active_window": true,
  "window_details": {
    "input_tokens": 30000,
    "output_tokens": 15000,
    "cache_creation_tokens": 5000,
    "cache_read_tokens": 2000
  }
}
```

### GET `/app/claude-usage/projects/`
List all projects with usage totals.

### GET `/app/claude-usage/projects/<project_name>/`
Get detailed information for a specific project.

### GET `/app/claude-usage/projects/<project_name>/sessions/`
Get all sessions for a specific project.

### GET `/app/claude-usage/sessions/<session_id>/`
Get detailed information for a specific session.

### POST `/app/claude-usage/refresh/`
Manually trigger data refresh (reads from local `~/.claude/` directory).

### POST `/app/claude-usage/agent-sync/`
Webhook endpoint for desktop agent to send Claude usage data.

**Request payload:**
```json
{
  "projects": [
    {
      "name": "project-name",
      "path": "~/.claude/projects/project-name",
      "sessions": [
        {
          "session_id": "uuid",
          "messages": [
            {
              "timestamp": "2025-09-14T11:57:01.497Z",
              "message": {
                "id": "msg_...",
                "model": "claude-sonnet-4-20250514",
                "usage": {
                  "input_tokens": 2000,
                  "output_tokens": 500,
                  "cache_creation_input_tokens": 1000,
                  "cache_read_input_tokens": 200
                }
              },
              "requestId": "req_..."
            }
          ]
        }
      ]
    }
  ]
}
```

## Desktop Agent Setup

### 1. Configure Environment Variables

On your **desktop PC** (where `~/.claude/` exists), create a `.env` file or export variables:

```bash
export CLAUDE_USAGE_API_URL="https://your-django-server.com"
export CLAUDE_USAGE_API_TOKEN="your-jwt-token-here"
export CLAUDE_PATH="~/.claude"  # Optional, defaults to ~/.claude
```

### 2. Get Your API Token

You need a JWT token or API authentication token from your Django app:

```bash
# Method 1: Using Django shell to get JWT token
python manage.py shell
>>> from rest_framework_simplejwt.tokens import RefreshToken
>>> from restAPI.models import CustomUser
>>> user = CustomUser.objects.get(email='your@email.com')
>>> refresh = RefreshToken.for_user(user)
>>> print(f"Access Token: {refresh.access_token}")
```

Or use the login endpoint to get a token.

### 3. Install Dependencies

```bash
pip install requests
```

### 4. Test the Agent

```bash
python /path/to/rest_api/scripts/claude_usage_agent.py
```

You should see output like:
```
[2025-10-05T12:00:00] Starting Claude usage sync...
✓ Sync successful: Synced 2 projects, 5 sessions, 123 snapshots
  Projects: 2
  Sessions: 5
  Snapshots: 123
```

### 5. Setup Automatic Sync

#### Option A: Cron Job (runs every 5 minutes)

```bash
crontab -e
```

Add:
```cron
*/5 * * * * export CLAUDE_USAGE_API_URL="https://your-server.com" && export CLAUDE_USAGE_API_TOKEN="your-token" && /usr/bin/python3 /path/to/rest_api/scripts/claude_usage_agent.py >> /var/log/claude_usage_agent.log 2>&1
```

#### Option B: Systemd Timer (recommended)

Create `/etc/systemd/system/claude-usage-sync.service`:
```ini
[Unit]
Description=Claude Usage Data Sync
After=network.target

[Service]
Type=oneshot
User=your-username
Environment="CLAUDE_USAGE_API_URL=https://your-server.com"
Environment="CLAUDE_USAGE_API_TOKEN=your-token"
ExecStart=/usr/bin/python3 /path/to/rest_api/scripts/claude_usage_agent.py
StandardOutput=journal
StandardError=journal
```

Create `/etc/systemd/system/claude-usage-sync.timer`:
```ini
[Unit]
Description=Sync Claude Usage Data Every 5 Minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
Unit=claude-usage-sync.service

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable claude-usage-sync.timer
sudo systemctl start claude-usage-sync.timer
sudo systemctl status claude-usage-sync.timer
```

View logs:
```bash
journalctl -u claude-usage-sync.service -f
```

## Rate Limit Calculation

The app calculates 5-hour rate limit windows based on Claude's policy:

- **Window Duration**: 5 hours from first message
- **Window Start**: Timestamp of first message in window
- **Next Reset**: Window start + 5 hours
- **Current Usage**: Total tokens in active window
- **Time Until Reset**: Countdown in seconds and human-readable format

### How It Works

1. All messages are sorted by timestamp
2. Messages are grouped into 5-hour windows
3. The most recent window is checked against current time
4. If within active window, usage and reset time are calculated
5. If past window end time, limits have reset (usage = 0)

## Models

### Project
- Stores project metadata and path
- Aggregates total tokens, sessions, and cost

### Session
- Represents a Claude conversation session
- Tracks message count and token totals

### UsageSnapshot
- Individual message usage data
- Timestamp, tokens, cost, model info

## Cost Calculation

Costs are calculated based on Anthropic's pricing:

**Claude Sonnet 4 (claude-sonnet-4-20250514)**
- Input: $0.015 per 1K tokens
- Output: $0.075 per 1K tokens
- Cache Creation: $0.0375 per 1K tokens
- Cache Read: $0.00375 per 1K tokens

**Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)**
- Input: $0.003 per 1K tokens
- Output: $0.015 per 1K tokens
- Cache Creation: $0.0075 per 1K tokens
- Cache Read: $0.00075 per 1K tokens

## Development

### Running Locally

If your Django server and desktop PC are the same machine:

1. The agent can read `~/.claude/` directly
2. Use `http://localhost:8000` as API URL
3. Or use the `/refresh/` endpoint instead of agent

### Manual Data Refresh

```bash
# From Django project directory
python manage.py update_claude_data --verbose
```

## Troubleshooting

### Agent can't connect to API
- Check `CLAUDE_USAGE_API_URL` is correct
- Verify API token is valid (not expired)
- Check network connectivity: `curl https://your-server.com/app/claude-usage/stats/`

### No data showing up
- Verify `~/.claude/projects/` contains JSONL files
- Check agent logs for errors
- Try manual refresh: `POST /app/claude-usage/refresh/`

### Rate limit shows "Limits have reset" incorrectly
- Ensure system time is synchronized (NTP)
- Check timezone settings in Django (`TIME_ZONE`)
- Verify timestamps in JSONL files are correct

### Authentication errors
- JWT tokens expire - regenerate token
- Ensure `IsAuthenticated` permission is working
- Check Authorization header format: `Bearer <token>`

## Security Notes

- Store API tokens securely (use environment variables, not code)
- Use HTTPS for production API endpoints
- Consider IP whitelisting for webhook endpoint
- Rotate API tokens regularly
- Don't commit tokens to git repositories
