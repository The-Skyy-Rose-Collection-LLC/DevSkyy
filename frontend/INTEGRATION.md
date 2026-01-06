# Frontend-Backend Integration Guide

## Overview

The DevSkyy frontend dashboard is fully integrated with the production backend at `https://devskyy-backend.onrender.com`. This document explains the architecture, configuration, and usage patterns.

---

## Architecture

### Components

1. **REST API Client** (`/lib/api-client.ts`)
   - Type-safe API calls
   - Automatic error handling
   - Request/response interceptors
   - Timeout and retry logic

2. **WebSocket Client** (`/lib/websocket.ts`)
   - Real-time updates for agents, metrics, round table
   - Auto-reconnection with exponential backoff
   - Connection state management
   - Type-safe message handlers

3. **React Hooks** (`/lib/hooks.ts`, `/lib/hooks/useRealtime.ts`)
   - SWR for REST API data fetching
   - Custom hooks for WebSocket subscriptions
   - Automatic cache management

4. **Connection Status** (`/components/ConnectionStatus.tsx`)
   - Visual health indicators
   - API and WebSocket status monitoring
   - Automatic health checks every 30s

---

## Configuration

### Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=https://devskyy-backend.onrender.com
NEXT_PUBLIC_WS_URL=wss://devskyy-backend.onrender.com
```

### Backend Endpoints

All API endpoints follow the pattern: `${NEXT_PUBLIC_API_URL}/api/v1/{resource}`

**Available Resources:**
- `/api/v1/agents` - SuperAgent management
- `/api/v1/tasks` - Task execution
- `/api/v1/round-table` - LLM competitions
- `/api/v1/metrics` - System metrics
- `/api/v1/tools` - Tool registry
- `/api/v1/3d` - 3D pipeline
- `/api/v1/visual` - Visual generation
- `/health` - Health check endpoint

**WebSocket Channels:**
- `/ws/agents` - Agent status updates
- `/ws/round_table` - Competition progress
- `/ws/tasks` - Task execution status
- `/ws/3d_pipeline` - 3D generation progress
- `/ws/metrics` - System metrics stream

---

## Usage Patterns

### REST API Calls

```typescript
import { apiClient } from '@/lib/api-client';

// Health check
const health = await apiClient.healthCheck();

// List agents
const agents = await apiClient.agents.list();

// Execute agent task
const result = await apiClient.agents.execute('commerce', 'Create product');

// Start round table competition
const competition = await apiClient.roundTable.compete('Write a poem');
```

### React Hooks (SWR)

```typescript
import { useAgents, useRoundTableHistory } from '@/lib/hooks';

function MyComponent() {
  // Automatically fetches and caches
  const { data: agents, error, mutate } = useAgents();

  // Refetch manually
  const refresh = () => mutate();

  // With parameters
  const { data: history } = useRoundTableHistory({ limit: 10, status: 'completed' });
}
```

### Real-time WebSocket Updates

```typescript
import { useRealtimeAgents, useRealtimeMetrics } from '@/lib/hooks/useRealtime';

function Dashboard() {
  // Real-time agent updates (<100ms latency)
  const { agents, isConnected, error } = useRealtimeAgents();

  // Real-time metrics stream
  const { metrics, history } = useRealtimeMetrics(100);

  return (
    <div>
      <Badge variant={isConnected ? 'success' : 'destructive'}>
        {isConnected ? 'Online' : 'Offline'}
      </Badge>

      {agents.map(agent => (
        <AgentCard key={agent.id} agent={agent} />
      ))}
    </div>
  );
}
```

### Direct WebSocket Access

```typescript
import { apiClient } from '@/lib/api-client';

const ws = apiClient.websocket('agents');

// Listen for events
ws.on('agent_status_update', (data) => {
  console.log('Agent updated:', data);
});

// Send message
ws.send({ type: 'get_agents' });

// Monitor connection
ws.onStatus((status) => {
  console.log('Status:', status); // 'connecting' | 'connected' | 'disconnected' | 'error'
});

// Cleanup
ws.disconnect();
```

---

## Error Handling

### APIError Class

```typescript
import { APIError } from '@/lib/api-client';

try {
  await apiClient.agents.execute('commerce', 'task');
} catch (error) {
  if (error instanceof APIError) {
    if (error.isNetworkError) {
      // Handle network issues
      showToast('Connection failed. Please check your internet.');
    } else if (error.isServerError) {
      // Handle 5xx errors
      showToast('Server error. Please try again later.');
    } else if (error.isClientError) {
      // Handle 4xx errors
      showToast(`Error: ${error.message}`);
    }
  }
}
```

### WebSocket Reconnection

The WebSocket client automatically handles reconnection with exponential backoff:
- Initial delay: 1 second
- Max delay: 30 seconds
- Max attempts: 10

```typescript
const ws = apiClient.websocket('agents', {
  reconnect: true,
  reconnectDelay: 1000,
  maxReconnectAttempts: 10,
  heartbeatInterval: 30000
});
```

---

## Connection Monitoring

### System Health Checks

The `ConnectionStatus` component performs automatic health checks:

```typescript
import { ConnectionStatus } from '@/components';

function Header() {
  return (
    <div className="flex items-center gap-4">
      <h1>Dashboard</h1>
      {/* Compact badge */}
      <ConnectionStatus compact />

      {/* Or detailed status */}
      <ConnectionStatus showDetails />
    </div>
  );
}
```

**Health Check Schedule:**
- Initial check on mount
- Periodic checks every 30 seconds
- Real-time WebSocket status monitoring

---

## Page-Specific Integrations

### 1. Dashboard (`/app/page.tsx`)
- Real-time agent status
- Live metrics charts
- WebSocket connection indicator
- Latest round table results

### 2. Agents Page (`/app/agents/page.tsx`)
- Agent list with live status
- SWR-cached data
- Manual refresh capability

### 3. Agent Chat (`/app/agents/[agent]/chat/page.tsx`)
- Streaming chat responses
- Server-Sent Events (SSE)
- Tool execution visibility
- Auto-scrolling messages

### 4. Round Table (`/app/round-table/page.tsx`)
- Competition history
- Real-time competition progress
- Provider status monitoring
- Win statistics charts

### 5. 3D Pipeline (`/app/3d-pipeline/page.tsx`)
- File upload to backend
- Job status polling
- Progress tracking
- Result display with model viewer

### 6. HuggingFace Spaces (`/app/hf-spaces/page.tsx`)
- Embedded iframe integrations
- Loading states
- Error handling with fallback links

---

## Best Practices

### 1. Use Appropriate Data Fetching Method

**SWR (REST):** For data that changes infrequently
```typescript
const { data } = useAgents(); // Cached, revalidated
```

**WebSocket:** For real-time updates
```typescript
const { agents } = useRealtimeAgents(); // Live updates
```

### 2. Handle Loading States

```typescript
const { data, error, isLoading } = useAgents();

if (isLoading) return <Skeleton />;
if (error) return <Error error={error} />;
return <AgentList agents={data} />;
```

### 3. Implement Error Boundaries

```typescript
import { ErrorBoundary } from '@/components';

<ErrorBoundary fallback={<ErrorPage />}>
  <AgentDashboard />
</ErrorBoundary>
```

### 4. Clean Up Subscriptions

```typescript
useEffect(() => {
  const ws = apiClient.websocket('agents');

  const handler = (data) => {
    // Handle update
  };

  ws.on('update', handler);

  return () => {
    ws.off('update', handler);
  };
}, []);
```

### 5. Optimize WebSocket Connections

- Reuse existing connections via `apiClient.websocket()`
- Don't create multiple connections to same channel
- Disconnect when component unmounts
- Use connection status to show UI state

---

## Troubleshooting

### Issue: "Failed to connect to backend"

**Solutions:**
1. Verify `NEXT_PUBLIC_API_URL` is set correctly
2. Check backend is running: `curl https://devskyy-backend.onrender.com/health`
3. Check browser console for CORS errors
4. Verify network connectivity

### Issue: "WebSocket connection failed"

**Solutions:**
1. Verify `NEXT_PUBLIC_WS_URL` uses `wss://` (not `ws://`)
2. Check firewall/proxy settings
3. Monitor connection status in dev tools Network tab
4. Try manual reconnection: `ws.reconnectNow()`

### Issue: "Stale data displayed"

**Solutions:**
1. Manually revalidate: `mutate()`
2. Check `revalidateOnFocus` setting
3. Verify WebSocket is connected for real-time updates
4. Clear SWR cache: `mutate(key, undefined, { revalidate: true })`

### Issue: "Too many requests"

**Solutions:**
1. Increase SWR `dedupingInterval`
2. Reduce WebSocket heartbeat frequency
3. Use `revalidateOnFocus: false` for static data
4. Implement request throttling

---

## Testing

### Manual Testing

```bash
# Start frontend
npm run dev

# Check health
curl http://localhost:3000/api/v1/agents

# Monitor WebSocket
# Open browser DevTools > Network > WS
# Filter for "ws/agents"
```

### Integration Tests

```typescript
import { apiClient } from '@/lib/api-client';

describe('API Integration', () => {
  it('should fetch agents', async () => {
    const agents = await apiClient.agents.list();
    expect(agents).toBeDefined();
    expect(Array.isArray(agents)).toBe(true);
  });

  it('should handle errors', async () => {
    await expect(
      apiClient.agents.get('invalid' as any)
    ).rejects.toThrow(APIError);
  });
});
```

---

## Production Checklist

- [x] Environment variables configured
- [x] HTTPS/WSS URLs for production
- [x] Error boundaries implemented
- [x] Loading states on all pages
- [x] Connection status indicators
- [x] WebSocket auto-reconnection
- [x] Request timeout handling
- [x] Graceful degradation
- [x] CORS headers configured on backend
- [x] Rate limiting respected

---

## Support

For backend API issues:
- Backend logs: Check Render dashboard
- API documentation: See `docs/api/` in backend repo
- Contact: support@skyyrose.com

For frontend issues:
- Check browser console
- Review Network tab (XHR/WS)
- Verify environment variables
- Test backend health endpoint directly
