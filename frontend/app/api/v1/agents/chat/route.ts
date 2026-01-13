/**
 * Agent Chat API Route
 * =====================
 * Handles streaming chat requests to backend agents.
 */

import { NextRequest } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || process.env.BACKEND_URL || 'http://localhost:8000';

export const runtime = 'edge';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { agent_type, message, stream = true } = body;

    if (!agent_type || !message) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields: agent_type and message' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Forward request to Python backend
    const backendResponse = await fetch(`${BACKEND_URL}/api/v1/agents/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        agent_type,
        task: message,
        stream,
      }),
    });

    if (!backendResponse.ok) {
      const error = await backendResponse.text();
      return new Response(
        JSON.stringify({ error: `Backend error: ${error}` }),
        {
          status: backendResponse.status,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    if (stream) {
      // Stream the response
      return new Response(backendResponse.body, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      });
    } else {
      // Return JSON response
      const data = await backendResponse.json();
      return new Response(JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
      });
    }
  } catch (error) {
    console.error('Chat API error:', error);
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : 'Internal server error',
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}
