# WebSocket API Documentation

## Overview

The DevSkyy backend provides real-time WebSocket connections for live updates to the dashboard. This eliminates the need for HTTP polling and provides <100ms latency for status updates.

## WebSocket Endpoints

All WebSocket endpoints are available at the following paths:

| Endpoint | Purpose | Message Types |
|----------|---------|---------------|
| `/api/ws/agents` | Agent status updates | `agent_status_update`, `error` |
| `/api/ws/round_table` | LLM Round Table competitions | `competition_update`, `error` |
| `/api/ws/tasks` | Task execution progress | `task_update`, `error` |
| `/api/ws/3d_pipeline` | 3D asset generation pipeline | `pipeline_update`, `error` |
| `/api/ws/metrics` | System performance metrics | `metrics_update`, `error` |

## Connection

### Basic Connection

```typescript
const ws = new WebSocket('ws://localhost:8000/api/ws/agents');

ws.onopen = () => {
  console.log('Connected to agents channel');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Connection closed');
};
```

### Production Connection (Vercel)

For production deployments, replace `ws://` with `wss://` and use your backend domain:

```typescript
const ws = new WebSocket('wss://api.devskyy.com/api/ws/agents');
```

## Message Formats

### Client → Server Messages

#### Ping/Pong (Keepalive)

```json
{
  "type": "ping"
}
```

Response:
```json
{
  "type": "pong",
  "timestamp": "2024-01-06T12:00:00Z"
}
```

#### Subscribe (Future Enhancement)

```json
{
  "type": "subscribe",
  "filters": {
    "agent_type": "commerce"
  }
}
```

### Server → Client Messages

#### Agent Status Update

Channel: `/api/ws/agents`

```json
{
  "type": "agent_status_update",
  "agent_id": "commerce-001",
  "status": "running",
  "data": {
    "agent_type": "commerce",
    "task_id": "task-abc123",
    "prompt_preview": "Create product...",
    "started_at": "2024-01-06T12:00:00Z"
  },
  "timestamp": "2024-01-06T12:00:00Z"
}
```

Status values:
- `running` - Agent is executing a task
- `completed` - Agent finished successfully
- `error` - Agent encountered an error
- `idle` - Agent is ready for new tasks
- `learning` - Agent is performing self-learning

#### Task Update

Channel: `/api/ws/tasks`

```json
{
  "type": "task_update",
  "task_id": "task-abc123",
  "status": "running",
  "progress": 45.0,
  "data": {
    "agent_id": "commerce-001",
    "agent_type": "commerce"
  },
  "timestamp": "2024-01-06T12:00:00Z"
}
```

Progress: 0-100 (percentage)

#### Round Table Competition Update

Channel: `/api/ws/round_table`

```json
{
  "type": "competition_update",
  "competition_id": "comp-xyz789",
  "stage": "scoring",
  "data": {
    "entries_count": 6,
    "scoring_started_at": "2024-01-06T12:00:00Z"
  },
  "timestamp": "2024-01-06T12:00:00Z"
}
```

Stages:
- `generating` - All 6 LLMs generating responses
- `scoring` - Responses being scored
- `ab_testing` - Top 2 finalists in A/B test
- `completed` - Winner determined

#### 3D Pipeline Update

Channel: `/api/ws/3d_pipeline`

```json
{
  "type": "pipeline_update",
  "pipeline_id": "3d-def456",
  "stage": "generating",
  "progress": 60.0,
  "data": {
    "prompt": "Victorian rose ring...",
    "format": "glb",
    "started_at": "2024-01-06T12:00:00Z"
  },
  "timestamp": "2024-01-06T12:00:00Z"
}
```

Stages:
- `generating` - 3D model being generated (Tripo3D)
- `validating` - Checking polycount, textures
- `uploading` - Uploading to WordPress
- `completed` - Asset ready
- `failed` - Generation failed

#### System Metrics Update

Channel: `/api/ws/metrics`

```json
{
  "type": "metrics_update",
  "metrics": {
    "timestamp": "2024-01-06T12:00:00Z",
    "cpu_percent": 45.2,
    "memory_percent": 62.8,
    "active_connections": 12,
    "requests_per_second": 45.5,
    "avg_latency_ms": 125.3
  },
  "timestamp": "2024-01-06T12:00:00Z"
}
```

Metrics are broadcast every 5 seconds.

#### Error Message

Any channel:

```json
{
  "type": "error",
  "error_type": "error",
  "message": "Agent commerce-001 failed: Network timeout",
  "timestamp": "2024-01-06T12:00:00Z"
}
```

Error types:
- `error` - Critical error
- `warning` - Warning message
- `info` - Informational message

#### Keepalive

Any channel (sent periodically if no activity):

```json
{
  "type": "keepalive",
  "timestamp": "2024-01-06T12:00:00Z"
}
```

## REST API Endpoints

### Agents

#### List All Agents

```http
GET /api/v1/agents
```

Response:
```json
[
  {
    "id": "commerce-001",
    "type": "commerce",
    "name": "Commerce Agent",
    "description": "E-commerce operations",
    "status": "idle",
    "capabilities": ["product_management", "pricing_optimization"],
    "tools": [...],
    "mlModels": ["demand_forecast"],
    "stats": {
      "tasksCompleted": 150,
      "successRate": 0.95,
      "avgLatencyMs": 250.0,
      "totalCostUsd": 2.50,
      "learningCycles": 10
    }
  }
]
```

#### Get Single Agent

```http
GET /api/v1/agents/{agent_type}
```

Example:
```http
GET /api/v1/agents/commerce
```

#### Execute Agent Task

```http
POST /api/v1/agents/{agent_type}/execute
Content-Type: application/json

{
  "task": "Create a new product for BLACK ROSE collection",
  "parameters": {},
  "use_round_table": false
}
```

Response:
```json
{
  "task_id": "task-abc123",
  "agent_type": "commerce",
  "status": "started",
  "result": null,
  "latency_ms": 125.5,
  "technique_used": "chain_of_thought"
}
```

#### Start/Stop Agent

```http
POST /api/v1/agents/{agent_type}/start
POST /api/v1/agents/{agent_type}/stop
```

#### Trigger Learning

```http
POST /api/v1/agents/{agent_type}/learn
```

### Tasks

#### List Tasks

```http
GET /api/v1/tasks?limit=20&agent_type=commerce&status=completed
```

Query parameters:
- `limit` - Number of tasks (1-100, default 20)
- `agent_type` - Filter by agent type
- `status` - Filter by status (pending, running, completed, failed)

#### Get Task

```http
GET /api/v1/tasks/{task_id}
```

#### Submit Task

```http
POST /api/v1/tasks
Content-Type: application/json

{
  "agentType": "commerce",
  "prompt": "Analyze pricing trends",
  "parameters": {},
  "useRoundTable": false
}
```

Response:
```json
{
  "taskId": "task-abc123",
  "agentType": "commerce",
  "prompt": "Analyze pricing trends",
  "status": "pending",
  "result": null,
  "error": null,
  "createdAt": "2024-01-06T12:00:00Z",
  "metrics": {
    "startTime": "2024-01-06T12:00:00Z"
  }
}
```

#### Cancel Task

```http
POST /api/v1/tasks/{task_id}/cancel
```

### Round Table

#### List Competitions

```http
GET /api/v1/round-table?limit=20&offset=0
```

#### Get Competition

```http
GET /api/v1/round-table/{competition_id}
```

#### Start Competition

```http
POST /api/v1/round-table/compete
Content-Type: application/json

{
  "prompt": "Generate a marketing campaign for BLACK ROSE collection",
  "task_id": "task-abc123",
  "providers": null
}
```

Response includes:
- Winner entry with full scores
- All entries ranked
- A/B test reasoning
- Total cost and duration

#### Get Provider Stats

```http
GET /api/v1/round-table/stats
```

Returns aggregated statistics for all LLM providers (win rates, costs, latencies).

### Metrics

#### Get System Metrics

```http
GET /api/v1/monitoring/metrics?metrics=health,performance&time_range=1h
```

Query parameters:
- `metrics` - Comma-separated list (health, performance, ml, business)
- `time_range` - Time window (1h, 24h, 7d, 30d)

## Frontend Integration

### React/Next.js Example

```typescript
// hooks/useWebSocket.ts
import { useEffect, useState } from 'react';

export function useWebSocket<T>(channel: string) {
  const [data, setData] = useState<T | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/api/ws/${channel}`);

    ws.onopen = () => {
      setConnected(true);
      console.log(`Connected to ${channel}`);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setData(message);
    };

    ws.onerror = (error) => {
      console.error(`WebSocket error on ${channel}:`, error);
    };

    ws.onclose = () => {
      setConnected(false);
      console.log(`Disconnected from ${channel}`);
    };

    // Cleanup on unmount
    return () => {
      ws.close();
    };
  }, [channel]);

  return { data, connected };
}

// Usage in component
function AgentDashboard() {
  const { data: agentUpdate, connected } = useWebSocket<AgentStatusUpdate>('agents');

  useEffect(() => {
    if (agentUpdate?.type === 'agent_status_update') {
      console.log('Agent status:', agentUpdate);
    }
  }, [agentUpdate]);

  return (
    <div>
      <StatusIndicator connected={connected} />
      {agentUpdate && <AgentStatus update={agentUpdate} />}
    </div>
  );
}
```

## Error Handling

### Connection Errors

- **4004**: Invalid channel name
- Connection refused: Backend not running
- WebSocket upgrade failed: CORS or proxy issue

### Reconnection Strategy

```typescript
function createWebSocketWithReconnect(url: string, maxRetries = 5) {
  let retries = 0;
  let ws: WebSocket | null = null;

  const connect = () => {
    ws = new WebSocket(url);

    ws.onopen = () => {
      retries = 0;
      console.log('Connected');
    };

    ws.onclose = () => {
      if (retries < maxRetries) {
        retries++;
        const delay = Math.min(1000 * Math.pow(2, retries), 30000);
        console.log(`Reconnecting in ${delay}ms...`);
        setTimeout(connect, delay);
      }
    };
  };

  connect();
  return ws;
}
```

## CORS Configuration

The backend is configured to accept connections from:
- `http://localhost:3000` (development)
- `https://devskyy-dashboard.vercel.app` (production)
- `https://*.vercel.app` (Vercel preview deployments)

## Security

- WebSocket connections use same origin policy
- No authentication required for WebSocket (read-only updates)
- REST API endpoints require JWT authentication (except health checks)
- Rate limiting applies to REST API (not WebSockets)

## Performance

- **WebSocket latency**: <100ms typical
- **Metrics broadcast interval**: 5 seconds
- **Max concurrent connections**: Limited by server (typically 1000+)
- **Message size**: Keep under 64KB for best performance

## Testing

Run the test suite:

```bash
# Install dependencies
pip install httpx websockets

# Run tests
python test_api_endpoints.py

# Custom host/port
python test_api_endpoints.py --host api.devskyy.com --port 443
```

## Monitoring

WebSocket connection statistics are available via:

```http
GET /api/v1/monitoring/metrics
```

Includes:
- Active connection count per channel
- Message throughput
- Error rates
- Connection duration

---

**Version**: 1.0.0
**Last Updated**: 2024-01-06
**Author**: DevSkyy Platform Team
