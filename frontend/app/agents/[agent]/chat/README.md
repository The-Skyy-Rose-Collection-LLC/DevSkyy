# Agent Chat Interface

Production-ready real-time chat interface with streaming support and tool execution visibility.

## Features

- **Real-time Streaming**: Server-sent events (SSE) for instant response updates
- **Tool Execution Visibility**: See exactly what tools the agent is using and their results
- **6 SuperAgents**: Chat with Commerce, Creative, Marketing, Support, Operations, or Analytics agents
- **Responsive Design**: Works on desktop and mobile
- **Type-Safe**: Full TypeScript coverage with strict types
- **Error Handling**: Graceful error display and recovery

## Usage

Navigate to `/agents/{agent-type}/chat` where `agent-type` is one of:
- `commerce` - E-commerce operations
- `creative` - 3D and visual generation
- `marketing` - Content and campaigns
- `support` - Customer service
- `operations` - DevOps and deployment
- `analytics` - Data analysis and reports

## Architecture

### Components

- **AgentChat**: Main container component
- **AgentHeader**: Agent info and status display
- **MessageList**: Scrollable message history with bubbles
- **ChatInput**: Auto-resizing textarea with send button
- **ToolCallDisplay**: Shows tool execution details inline

### State Management

- **useAgentChat**: Custom hook managing chat state, streaming, and API calls
- **Server-Sent Events**: Streaming protocol for real-time updates
- **Abort Controller**: Allows cancelling in-flight requests

### Data Flow

1. User types message → ChatInput
2. useAgentChat sends to `/api/v1/agents/chat`
3. Next.js API route forwards to Python backend
4. Backend streams responses as SSE
5. Hook parses SSE chunks and updates message state
6. MessageList renders updated messages

## API Contract

### Request

```typescript
POST /api/v1/agents/chat
{
  "agent_type": "commerce",
  "message": "Create a product for luxury candles",
  "stream": true
}
```

### Response (SSE Stream)

```
data: {"type": "content", "content": "I'll create that product for you"}
data: {"type": "tool_call", "toolCall": {"id": "1", "name": "create_product", "status": "running", ...}}
data: {"type": "tool_result", "toolCall": {"id": "1", "status": "completed", "result": {...}}}
data: [DONE]
```

## Error Handling

- Network errors: Displayed inline in chat
- API errors: Shown as assistant message
- Streaming errors: Gracefully handled with partial content
- Cancellation: Clean abort via abort controller

## Performance

- **Lazy Loading**: Messages render on-demand
- **Auto-scroll**: Smooth scroll to latest message
- **Textarea Auto-resize**: Grows with content up to max height
- **Debouncing**: Not needed - streaming handles backpressure

## Testing

```bash
# Type check
npm run type-check

# Lint
npm run lint

# E2E tests (if configured)
npm run test:e2e
```

## Future Enhancements

- [ ] Message persistence (localStorage/DB)
- [ ] Session history
- [ ] File attachments
- [ ] Voice input
- [ ] Markdown rendering
- [ ] Code syntax highlighting
- [ ] Export chat transcript
