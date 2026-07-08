import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

// Route handlers run on the Node runtime by default (the MCP SDK needs Node APIs).
// Do NOT add `export const runtime` — it's incompatible with Cache Components mode.

// Server-side only. MCP_SERVICE_TOKEN never reaches the browser.
const MCP_URL = process.env.MCP_URL ?? 'http://localhost:8000/mcp/';
const MCP_TOKEN = process.env.MCP_SERVICE_TOKEN ?? '';
// Matches the WordPress bridge's 20s timeout (inc/mcp-bridge.php:113).
const MCP_TIMEOUT_MS = 20_000;

interface McpRequestBody {
  action?: 'list' | 'call';
  name?: string;
  args?: Record<string, unknown>;
}

// Sentinel error thrown when the deadline below wins the race, so the catch
// block in POST() can return 504 instead of the generic 502.
class McpTimeoutError extends Error {
  constructor() {
    super('MCP_TIMEOUT');
    this.name = 'McpTimeoutError';
  }
}

async function withClient<T>(run: (client: Client) => Promise<T>): Promise<T> {
  const client = new Client({ name: 'devskyy-dashboard', version: '1.0.0' });
  // StreamableHTTPClientTransportOptions has no `signal` field — the
  // transport owns its own internal AbortController and always overwrites
  // any `signal` smuggled in via `requestInit` on every request (see
  // node_modules/@modelcontextprotocol/sdk streamableHttp.js). So the
  // deadline is enforced by racing the call itself, not by an AbortSignal.
  const transport = new StreamableHTTPClientTransport(new URL(MCP_URL), {
    requestInit: MCP_TOKEN ? { headers: { Authorization: `Bearer ${MCP_TOKEN}` } } : undefined,
  });
  await client.connect(transport);
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => reject(new McpTimeoutError()), MCP_TIMEOUT_MS);
  });
  try {
    return await Promise.race([run(client), timeout]);
  } finally {
    // Clear the timer so it can't reject after a successful race (would
    // otherwise be an unhandled rejection on every successful request).
    clearTimeout(timer);
    // client.close() -> transport.close() aborts the transport's internal
    // AbortController, cancelling any in-flight fetch on timeout.
    await client.close().catch(() => {});
  }
}

export async function POST(req: NextRequest): Promise<NextResponse> {
  // Gate: only authenticated dashboard users may reach the relay. The proxy holds
  // MCP_SERVICE_TOKEN server-side, so an open route would expose the full tool set
  // (count is computed at runtime — see /health's tool_count, mcp_tools/http_mount.py).
  const session = await getServerSession(authOptions);
  if (!session) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  let body: McpRequestBody;
  try {
    body = (await req.json()) as McpRequestBody;
  } catch {
    return NextResponse.json({ error: 'invalid JSON body' }, { status: 400 });
  }

  try {
    if (body.action === 'list') {
      const { tools } = await withClient((client) => client.listTools());
      return NextResponse.json({ tools });
    }
    if (body.action === 'call') {
      if (!body.name) {
        return NextResponse.json({ error: 'tool name required' }, { status: 400 });
      }
      const name = body.name;
      const args = body.args ?? {};
      const result = await withClient((client) => client.callTool({ name, arguments: args }));
      return NextResponse.json({ result });
    }
    return NextResponse.json({ error: `unknown action: ${String(body.action)}` }, { status: 400 });
  } catch (error: unknown) {
    if (error instanceof McpTimeoutError) {
      return NextResponse.json({ error: 'MCP request timed out' }, { status: 504 });
    }
    const message = error instanceof Error ? error.message : 'Unexpected error';
    return NextResponse.json({ error: `MCP request failed: ${message}` }, { status: 502 });
  }
}
