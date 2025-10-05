# Claude Usage - Frontend API Documentation

Easy-to-use endpoints for building dashboards like claude-monitor.

## Base URL
```
https://api.nxfs.no/app/claude-usage/
```

## Authentication
All endpoints require authentication:
```
Authorization: Token YOUR_API_TOKEN
```

---

## Dashboard Endpoint

### `GET /dashboard/`

Get complete dashboard summary with all metrics needed for a claude-monitor style interface.

**Query Parameters:**
- `hours` (optional): Time range in hours (default: 6)

**Response:**
```json
{
  "summary": {
    "total_tokens": 56869556,
    "total_cost_usd": 1.234,
    "total_messages": 639,
    "time_range_hours": 6
  },
  "burn_rate": {
    "tokens_per_minute": 105.8,
    "cost_per_minute_usd": 0.0348
  },
  "model_distribution": [
    {
      "model": "claude-sonnet-4-20250514",
      "tokens": 50000000,
      "messages": 500,
      "cost_usd": 1.1,
      "percentage": 87.9
    }
  ],
  "rate_limit": {
    "current_window_tokens": 10946569,
    "current_window_start": "2025-10-05T18:26:39.936000+00:00",
    "next_reset_at": "2025-10-05T23:26:39.936000+00:00",
    "time_until_reset_seconds": 14818,
    "time_until_reset_human": "4h 6m",
    "is_within_active_window": true,
    "predictions": {
      "tokens_will_run_out": false,
      "estimated_time_to_limit": "Not reaching limit"
    }
  }
}
```

**Use Cases:**
- Display current usage summary
- Show burn rate (tokens/min, $/min)
- Model distribution pie chart
- Rate limit warnings
- Time until reset countdown
- Predictions for running out of tokens

---

## Time-Series Endpoint

### `GET /timeseries/`

Get time-series data for graphing token usage over time.

**Query Parameters:**
- `hours` (optional): Time range in hours (default: 6)
- `interval` (optional): Data point interval - `5min`, `15min`, or `1hour` (default: `5min`)

**Response:**
```json
{
  "start_time": "2025-10-05T16:00:00+00:00",
  "end_time": "2025-10-05T22:00:00+00:00",
  "interval": "5min",
  "data_points": [
    {
      "timestamp": "2025-10-05T16:00:00+00:00",
      "total_tokens": 1250000,
      "input_tokens": 50000,
      "output_tokens": 25000,
      "cache_creation_tokens": 500000,
      "cache_read_tokens": 675000,
      "message_count": 15
    },
    {
      "timestamp": "2025-10-05T16:05:00+00:00",
      "total_tokens": 890000,
      "input_tokens": 35000,
      "output_tokens": 18000,
      "cache_creation_tokens": 400000,
      "cache_read_tokens": 437000,
      "message_count": 12
    }
  ]
}
```

**Use Cases:**
- Line graphs showing token usage over time
- Area charts for different token types
- Message count bars
- Zoom in/out with different intervals

**Frontend Example (Chart.js):**
```javascript
const response = await fetch('/app/claude-usage/timeseries/?hours=6&interval=5min', {
  headers: { 'Authorization': 'Token YOUR_TOKEN' }
});
const data = await response.json();

const chartData = {
  labels: data.data_points.map(p => new Date(p.timestamp)),
  datasets: [{
    label: 'Total Tokens',
    data: data.data_points.map(p => p.total_tokens),
    borderColor: 'rgb(75, 192, 192)',
    tension: 0.1
  }]
};
```

---

## Usage Stats Endpoint

### `GET /stats/`

Get overall usage statistics with rate limit information.

**Response:**
```json
{
  "total_tokens": 56869556,
  "total_input_tokens": 55689,
  "total_output_tokens": 12116,
  "total_cache_creation_tokens": 3603319,
  "total_cache_read_tokens": 53198432,
  "total_sessions": 4,
  "total_messages": 639,
  "projects": 2,
  "current_window_tokens": 10946569,
  "next_reset_at": "2025-10-05T23:26:39.936000+00:00",
  "time_until_reset_seconds": 14818,
  "time_until_reset_human": "4h 6m remaining",
  "is_within_active_window": true
}
```

---

## Projects Endpoints

### `GET /projects/`

List all projects with usage totals.

**Response:**
```json
{
  "projects": [
    {
      "id": 1,
      "name": "rest-api",
      "path": "~/.claude/projects/rest-api",
      "total_tokens": 45000000,
      "total_sessions": 150,
      "total_cost": 1.234,
      "created_at": "2025-10-05T10:00:00Z",
      "updated_at": "2025-10-05T20:00:00Z"
    }
  ],
  "count": 1
}
```

### `GET /projects/<project_name>/`

Get detailed information for a specific project including all sessions.

### `GET /projects/<project_name>/sessions/`

Get all sessions for a specific project.

---

## Building a Dashboard

### Recommended Polling Intervals

```javascript
// Dashboard summary - update every 30 seconds
setInterval(async () => {
  const data = await fetch('/app/claude-usage/dashboard/', {
    headers: { 'Authorization': `Token ${API_TOKEN}` }
  }).then(r => r.json());

  updateDashboard(data);
}, 30000);

// Time-series graph - update every minute
setInterval(async () => {
  const data = await fetch('/app/claude-usage/timeseries/?interval=5min', {
    headers: { 'Authorization': `Token ${API_TOKEN}` }
  }).then(r => r.json());

  updateGraph(data);
}, 60000);
```

### Dashboard Components

Based on the claude-monitor screenshot:

1. **Cost Usage Bar**
   - Use: `dashboard.summary.total_cost_usd` / budget limit
   - Color: Yellow if > 50%, Red if > 80%

2. **Token Usage Bar**
   - Use: `dashboard.rate_limit.current_window_tokens` / 65459 (Pro limit)
   - Color: Green if < 50%, Yellow if > 50%, Red if > 80%

3. **Messages Usage Bar**
   - Use: `dashboard.summary.total_messages` / message limit

4. **Time to Reset**
   - Use: `dashboard.rate_limit.time_until_reset_human`
   - Color: Red if < 30 minutes

5. **Model Distribution**
   - Use: `dashboard.model_distribution`
   - Pie chart or bar chart
   - Show percentage for each model

6. **Burn Rate Display**
   - Use: `dashboard.burn_rate.tokens_per_minute`
   - Show as "X tokens/min"

7. **Cost Rate Display**
   - Use: `dashboard.burn_rate.cost_per_minute_usd`
   - Show as "$X/min"

8. **Predictions**
   - Use: `dashboard.rate_limit.predictions.tokens_will_run_out`
   - Show warning if true
   - Display: `dashboard.rate_limit.predictions.estimated_time_to_limit`

### React Example Component

```tsx
import { useEffect, useState } from 'react';

interface DashboardData {
  summary: {
    total_tokens: number;
    total_cost_usd: number;
    total_messages: number;
  };
  burn_rate: {
    tokens_per_minute: number;
    cost_per_minute_usd: number;
  };
  rate_limit: {
    time_until_reset_human: string;
    current_window_tokens: number;
    predictions: {
      tokens_will_run_out: boolean;
      estimated_time_to_limit: string;
    };
  };
  model_distribution: Array<{
    model: string;
    percentage: number;
    tokens: number;
  }>;
}

export function ClaudeUsageDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      const response = await fetch('https://api.nxfs.no/app/claude-usage/dashboard/', {
        headers: {
          'Authorization': `Token ${process.env.REACT_APP_API_TOKEN}`
        }
      });
      setData(await response.json());
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30s

    return () => clearInterval(interval);
  }, []);

  if (!data) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      <div className="summary">
        <h2>Claude Usage Monitor</h2>
        <div className="metrics">
          <div className="metric">
            <label>💰 Cost Usage</label>
            <div className="progress-bar">
              <div style={{ width: `${(data.summary.total_cost_usd / 16.66) * 100}%` }} />
            </div>
            <span>${data.summary.total_cost_usd.toFixed(2)} / $16.66</span>
          </div>

          <div className="metric">
            <label>🔢 Token Usage</label>
            <div className="progress-bar">
              <div style={{ width: `${(data.rate_limit.current_window_tokens / 65459) * 100}%` }} />
            </div>
            <span>{data.rate_limit.current_window_tokens.toLocaleString()} / 65,459</span>
          </div>

          <div className="metric">
            <label>⏱️ Time to Reset</label>
            <span>{data.rate_limit.time_until_reset_human}</span>
          </div>

          <div className="metric">
            <label>📈 Burn Rate</label>
            <span>{data.burn_rate.tokens_per_minute.toFixed(1)} tokens/min</span>
            <span>${data.burn_rate.cost_per_minute_usd.toFixed(4)}/min</span>
          </div>
        </div>
      </div>

      {data.rate_limit.predictions.tokens_will_run_out && (
        <div className="warning">
          ⚠️ Tokens will run out in {data.rate_limit.predictions.estimated_time_to_limit}
        </div>
      )}

      <div className="model-distribution">
        <h3>Model Distribution</h3>
        {data.model_distribution.map(model => (
          <div key={model.model}>
            <span>{model.model}</span>
            <span>{model.percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Rate Limit Calculations

The API uses Claude's 5-hour rate limit window:

- **Window starts**: First message timestamp
- **Window ends**: Start + 5 hours
- **Current usage**: Tokens used in active window
- **Reset time**: When window ends
- **Predictions**: Based on current burn rate

### Token Limits by Plan

- **Pro**: ~65,459 tokens per 5h window
- **Max5**: ~88,000 tokens
- **Max20**: ~220,000 tokens

Pass `token_limit` parameter to customize predictions (coming soon).

---

## Error Handling

All endpoints return standard error responses:

```json
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Authentication required"
  }
}
```

Common status codes:
- `200`: Success
- `401`: Unauthorized (invalid token)
- `404`: Resource not found
- `500`: Server error

---

## Data Retention

- **Auto-cleanup**: Data older than 6 hours is automatically deleted
- **Sync frequency**: Desktop agent syncs every 5 minutes
- **Always available**: Last 6 hours of usage data

---

## WebSocket Support (Coming Soon)

Real-time updates via WebSockets:

```javascript
const ws = new WebSocket('wss://api.nxfs.no/ws/claude-usage/');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updateDashboard(data);
};
```

---

## Questions?

- API Issues: Check `/app/claude-usage/stats/` first
- Frontend Examples: See React example above
- More endpoints: See main README in `/app/claude_usage/README.md`
