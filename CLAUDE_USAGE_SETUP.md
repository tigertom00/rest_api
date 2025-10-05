# Claude Usage Monitoring - Quick Setup Guide

## What Was Built

✅ **Rate limit tracking** - Shows time until next 5-hour reset
✅ **Webhook endpoint** - Desktop agent sends data to Django API
✅ **Enhanced API responses** - Usage stats now include rate limit info
✅ **Desktop agent script** - Reads `~/.claude/` and syncs to API

## New API Response Example

```bash
GET /app/claude-usage/stats/
```

**Returns:**
```json
{
  "total_tokens": 150000,
  "current_window_tokens": 45000,
  "next_reset_at": "2025-10-05T15:30:00Z",
  "time_until_reset_seconds": 7200,
  "time_until_reset_human": "2h 0m remaining",
  "is_within_active_window": true
}
```

## Setup Steps (Desktop PC)

### 1. Get Your JWT Token

```bash
# On Django server
python manage.py shell
>>> from rest_framework_simplejwt.tokens import RefreshToken
>>> from restAPI.models import CustomUser
>>> user = CustomUser.objects.get(email='your@email.com')
>>> refresh = RefreshToken.for_user(user)
>>> print(f"Access Token: {refresh.access_token}")
```

### 2. Configure Environment (Desktop PC)

```bash
export CLAUDE_USAGE_API_URL="https://your-django-server.com"
export CLAUDE_USAGE_API_TOKEN="your-jwt-token-from-step-1"
```

### 3. Install Dependencies (Desktop PC)

```bash
pip install requests
```

### 4. Test the Agent

```bash
python /path/to/rest_api/scripts/claude_usage_agent.py
```

Expected output:
```
[2025-10-05T12:00:00] Starting Claude usage sync...
✓ Sync successful: Synced 2 projects, 5 sessions, 123 snapshots
```

### 5. Setup Automatic Sync (Cron)

```bash
crontab -e
```

Add (replace paths and credentials):
```cron
*/5 * * * * export CLAUDE_USAGE_API_URL="https://your-server.com" && export CLAUDE_USAGE_API_TOKEN="your-token" && /usr/bin/python3 /path/to/rest_api/scripts/claude_usage_agent.py >> /var/log/claude_usage_agent.log 2>&1
```

## How It Works

```
┌─────────────┐     Every 5 min     ┌──────────────┐
│  Desktop PC │ ──────────────────> │  Django API  │
│             │                      │              │
│ ~/.claude/  │  POST /agent-sync/  │  Database    │
│   *.jsonl   │                      │              │
└─────────────┘                      └──────────────┘
                                              │
                                              │
                                              ▼
                                     ┌──────────────────┐
                                     │   GET /stats/    │
                                     │                  │
                                     │ • Token usage    │
                                     │ • Reset timer    │
                                     │ • Window status  │
                                     └──────────────────┘
```

## Webhook Architecture

Same pattern as `docker_monitor`:

1. **Desktop agent** reads local `~/.claude/` files
2. **Agent sends** JSON payload to webhook endpoint
3. **Django receives** and stores in database
4. **Frontend queries** API for usage stats

## Files Changed/Created

### Modified:
- ✏️ `app/claude_usage/services.py` - Added rate limit calculation methods
- ✏️ `app/claude_usage/views.py` - Added webhook endpoint and enhanced stats view
- ✏️ `app/claude_usage/serializers.py` - Added rate limit fields
- ✏️ `app/claude_usage/urls.py` - Added webhook route

### Created:
- ✨ `scripts/claude_usage_agent.py` - Desktop agent script
- ✨ `app/claude_usage/README.md` - Full documentation
- ✨ `CLAUDE_USAGE_SETUP.md` - This quick setup guide

## Testing Locally

If Django server runs on same PC as `~/.claude/`:

```bash
# Use the existing refresh endpoint instead
curl -X POST http://localhost:8000/app/claude-usage/refresh/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Check stats
curl http://localhost:8000/app/claude-usage/stats/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Rate Limit Window Calculation

- **5-hour windows** starting from first message timestamp
- **Current usage** = tokens in active window
- **Next reset** = window start + 5 hours
- **Time remaining** = next reset - current time

Example:
- First message at: `10:00:00`
- Window ends at: `15:00:00` (5 hours later)
- Current time: `13:30:00`
- Time remaining: `1h 30m`

## Troubleshooting

**Agent can't connect:**
- Verify `CLAUDE_USAGE_API_URL` is correct
- Check JWT token hasn't expired
- Test with: `curl $CLAUDE_USAGE_API_URL/app/claude-usage/stats/`

**No data showing:**
- Check `~/.claude/projects/` has JSONL files
- Verify agent has read permissions
- Check logs: `tail -f /var/log/claude_usage_agent.log`

**Wrong reset time:**
- Ensure system time is synced (NTP)
- Check Django `TIME_ZONE` setting
- Verify JSONL timestamps are correct

## Next Steps

1. **Get JWT token** from Django
2. **Configure desktop PC** with environment variables
3. **Test agent** manually
4. **Setup cron job** for automatic sync
5. **Verify data** in API responses

See `app/claude_usage/README.md` for detailed documentation.
