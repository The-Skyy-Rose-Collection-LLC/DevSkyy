# Backend Quick Start Guide

## For Frontend Developers

This guide provides everything you need to connect the Next.js dashboard to the backend.

---

## Backend URL

**Development**: `http://localhost:8000`

**Production**: Set via environment variables

---

## WebSocket Endpoints

Connect to these endpoints for real-time updates:

```typescript
const WEBSOCKET_ENDPOINTS = {
  agents: '/api/ws/agents',           // Agent status updates
  roundTable: '/api/ws/round_table',  // Round Table competitions
  tasks: '/api/ws/tasks',             // Task execution progress
  pipeline3D: '/api/ws/3d_pipeline',  // 3D generation pipeline
  metrics: '/api/ws/metrics',         // System metrics (every 5s)
};
```

### Usage Example

```typescript
const ws = new WebSocket(`${WS_URL}/api/ws/agents`);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Agent update:', message);
};
```

---

## REST API Endpoints

### List All Agents

```http
GET /api/v1/agents
```

Returns array of 6 SuperAgents with status, stats, tools, and ML models.

### Execute Agent Task

```http
POST /api/v1/agents/{agent_type}/execute
Content-Type: application/json

{
  "task": "Your task here",
  "parameters": {},
  "use_round_table": false
}
```

Agent types: `commerce`, `creative`, `marketing`, `support`, `operations`, `analytics`

### List Tasks

```http
GET /api/v1/tasks?limit=20&agent_type=commerce&status=completed
```

### Submit Task (Async)

```http
POST /api/v1/tasks
Content-Type: application/json

{
  "agentType": "commerce",
  "prompt": "Your task",
  "useRoundTable": false
}
```

Returns immediately with `taskId`. Track progress via WebSocket `/api/ws/tasks`.

### Round Table Competition

```http
POST /api/v1/round-table/compete
Content-Type: application/json

{
  "prompt": "Your prompt for all 6 LLMs",
  "task_id": "optional-task-id"
}
```

Track progress via WebSocket `/api/ws/round_table`.

---

## Environment Variables

### Frontend (.env.local)

```env
# REST API
NEXT_PUBLIC_API_URL=http://localhost:8000

# WebSocket
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Production

```env
NEXT_PUBLIC_API_URL=https://api.devskyy.com
NEXT_PUBLIC_WS_URL=wss://api.devskyy.com
```

---

## Message Types

### Agent Status Update

```json
{
  "type": "agent_status_update",
  "agent_id": "commerce-001",
  "status": "running",
  "data": {
    "task_id": "task-abc123",
    "agent_type": "commerce"
  },
  "timestamp": "2024-01-06T12:00:00Z"
}
```

Status: `running`, `completed`, `error`, `idle`, `learning`

### Task Update

```json
{
  "type": "task_update",
  "task_id": "task-abc123",
  "status": "running",
  "progress": 45.0,
  "data": {
    "agent_id": "commerce-001"
  },
  "timestamp": "2024-01-06T12:00:00Z"
}
```

Progress: 0-100 (percentage)

### Round Table Update

```json
{
  "type": "competition_update",
  "competition_id": "comp-xyz789",
  "stage": "scoring",
  "data": {
    "entries_count": 6
  },
  "timestamp": "2024-01-06T12:00:00Z"
}
```

Stages: `generating`, `scoring`, `ab_testing`, `completed`

### 3D Pipeline Update

```json
{
  "type": "pipeline_update",
  "pipeline_id": "3d-def456",
  "stage": "generating",
  "progress": 60.0,
  "data": {
    "prompt": "3D model description"
  },
  "timestamp": "2024-01-06T12:00:00Z"
}
```

Stages: `generating`, `validating`, `uploading`, `completed`, `failed`

### Metrics Update

```json
{
  "type": "metrics_update",
  "metrics": {
    "cpu_percent": 45.2,
    "memory_percent": 62.8,
    "active_connections": 12,
    "requests_per_second": 45.5,
    "avg_latency_ms": 125.3
  },
  "timestamp": "2024-01-06T12:00:00Z"
}
```

Broadcast every 5 seconds.

---

## Testing Backend Locally

### 1. Start Backend

```bash
cd /Users/coreyfoster/DevSkyy
uvicorn main_enterprise:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Verify Health

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "services": {
    "api": "operational",
    "agents": "operational"
  }
}
```

### 3. Test Agents Endpoint

```bash
curl http://localhost:8000/api/v1/agents
```

Should return array of 6 agents.

### 4. Test WebSocket

```bash
# Install wscat
npm install -g wscat

# Connect
wscat -c ws://localhost:8000/api/ws/agents

# Send ping
> {"type": "ping"}

# Should receive pong
< {"type":"pong","timestamp":"..."}
```

### 5. Run Full Test Suite

```bash
# Install dependencies
pip install httpx websockets

# Run tests
python test_api_endpoints.py
```

---

## Common Issues

### CORS Error

**Symptom**: `Access-Control-Allow-Origin` error in browser

**Solution**: Backend already configured for `localhost:3000` and Vercel. Check `NEXT_PUBLIC_API_URL` is correct.

### WebSocket Connection Refused

**Symptom**: `WebSocket connection failed`

**Solution**:
1. Ensure backend is running
2. Check URL is `ws://` (not `http://`)
3. Verify port is correct (default: 8000)

### No Real-Time Updates

**Symptom**: WebSocket connected but no messages

**Solution**:
1. Ensure you're connected to correct channel
2. Trigger an action (submit task, start Round Table)
3. Check browser console for errors

---

## Production Deployment

### Backend Requirements

1. **WebSocket Support**: Ensure hosting platform supports WebSocket (most do)
2. **HTTPS/WSS**: Use secure connections in production
3. **CORS**: Already configured for Vercel production domain
4. **Environment Variables**: Set all required API keys

### Frontend Requirements

1. Set `NEXT_PUBLIC_API_URL` to backend domain
2. Set `NEXT_PUBLIC_WS_URL` to backend domain (wss://)
3. Deploy to Vercel: `vercel --prod`

---

## API Documentation

Full documentation: http://localhost:8000/docs (when backend running)

Or see: `/Users/coreyfoster/DevSkyy/docs/WEBSOCKET_API.md`

---

## Support

**Questions?** Check documentation in `/Users/coreyfoster/DevSkyy/docs/`

**Issues?** Run test suite: `python test_api_endpoints.py`

**Need Help?** Email: support@skyyrose.com

---

**Version**: 1.0.0

**Last Updated**: 2024-01-06
