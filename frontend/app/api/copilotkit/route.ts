/**
 * CopilotKit Runtime API Endpoint
 * ================================
 * Handles AI requests from CopilotKit frontend components.
 * Supports multiple LLM providers (OpenAI, Anthropic).
 */

import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from '@copilotkit/runtime';
import { NextRequest } from 'next/server';

const runtime = new CopilotRuntime({
  // Use OpenAI as the LLM provider
  // Can switch to Anthropic, Groq, etc. based on your preference
  actions: [],
});

const serviceAdapter = new OpenAIAdapter({
  model: process.env.OPENAI_MODEL || 'gpt-4-turbo-preview',
});

/**
 * POST /api/copilotkit
 * Handle CopilotKit runtime requests
 */
export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: '/api/copilotkit',
  });

  return handleRequest(req);
};

/**
 * GET /api/copilotkit/health
 * Health check endpoint
 */
export const GET = async () => {
  return new Response(
    JSON.stringify({
      status: 'ok',
      provider: 'openai',
      model: process.env.OPENAI_MODEL || 'gpt-4-turbo-preview',
    }),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );
};
