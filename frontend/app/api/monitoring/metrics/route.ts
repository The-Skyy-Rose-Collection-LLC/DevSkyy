/**
 * Prometheus Metrics Endpoint - Next.js Route Handler
 */

import { NextResponse } from 'next/server';

const metrics = [
  {
    name: 'mcp_tool_calls_total',
    type: 'counter',
    help: 'Total number of MCP tool calls',
    value: 0,
  },
  {
    name: 'mcp_request_duration_seconds',
    type: 'histogram',
    help: 'MCP tool request duration in seconds',
    value: 0,
  },
  {
    name: 'mcp_errors_total',
    type: 'counter',
    help: 'Total number of MCP errors',
    value: 0,
  },
  {
    name: 'mcp_active_connections',
    type: 'gauge',
    help: 'Number of active MCP connections',
    value: 0,
  },
  {
    name: 'mcp_server_uptime_seconds',
    type: 'gauge',
    help: 'MCP Server uptime in seconds',
    value: Date.now() / 1000,
  },
];

function formatPrometheusMetrics() {
  let output = '';

  for (const metric of metrics) {
    output += `# HELP ${metric.name} ${metric.help}\n`;
    output += `# TYPE ${metric.name} ${metric.type}\n`;
    output += `${metric.name} ${metric.value}\n`;
  }

  return output;
}

export async function GET() {
  try {
    const prometheusOutput = formatPrometheusMetrics();

    return new NextResponse(prometheusOutput, {
      status: 200,
      headers: {
        'Content-Type': 'text/plain; version=0.0.4; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
      },
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: 'Failed to generate metrics',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
