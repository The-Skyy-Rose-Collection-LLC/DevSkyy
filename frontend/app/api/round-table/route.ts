/**
 * Round Table API Route Handler
 */

import { NextResponse } from 'next/server';

const MOCK_ENTRIES = [
  {
    id: 'rt-001',
    prompt: 'Generate a product description for a luxury watch',
    taskType: 'content_creation',
    status: 'completed',
    startedAt: new Date(Date.now() - 3600000).toISOString(),
    completedAt: new Date(Date.now() - 3500000).toISOString(),
    responses: [
      { provider: 'openai', model: 'gpt-4o', response: 'Exquisite timepiece...', score: 0.92, latencyMs: 1200 },
      { provider: 'anthropic', model: 'claude-3-5-sonnet', response: 'Masterfully crafted...', score: 0.95, latencyMs: 980 },
      { provider: 'google', model: 'gemini-2.0-flash', response: 'Precision engineering...', score: 0.88, latencyMs: 850 }
    ],
    winner: { provider: 'anthropic', model: 'claude-3-5-sonnet', score: 0.95 },
    abTestResult: { significance: 0.95, winner: 'anthropic' }
  },
  {
    id: 'rt-002',
    prompt: 'Analyze sales trends for Q4 2024',
    taskType: 'analytics',
    status: 'completed',
    startedAt: new Date(Date.now() - 7200000).toISOString(),
    completedAt: new Date(Date.now() - 7000000).toISOString(),
    responses: [
      { provider: 'openai', model: 'gpt-4o', response: 'Sales analysis shows...', score: 0.94, latencyMs: 1400 },
      { provider: 'anthropic', model: 'claude-3-5-sonnet', response: 'Q4 trends indicate...', score: 0.91, latencyMs: 1100 }
    ],
    winner: { provider: 'openai', model: 'gpt-4o', score: 0.94 },
    abTestResult: { significance: 0.87, winner: 'openai' }
  }
];

export async function GET() {
  return NextResponse.json(MOCK_ENTRIES);
}

export async function POST(request: Request) {
  const body = await request.json();
  const newEntry = {
    id: `rt-${Date.now()}`,
    prompt: body.prompt,
    taskType: body.task_type || 'general',
    status: 'completed',
    startedAt: new Date().toISOString(),
    completedAt: new Date().toISOString(),
    responses: [
      { provider: 'openai', model: 'gpt-4o', response: 'Generated response...', score: 0.90, latencyMs: 1000 },
      { provider: 'anthropic', model: 'claude-3-5-sonnet', response: 'Generated response...', score: 0.92, latencyMs: 950 }
    ],
    winner: { provider: 'anthropic', model: 'claude-3-5-sonnet', score: 0.92 },
    abTestResult: { significance: 0.85, winner: 'anthropic' }
  };
  return NextResponse.json(newEntry);
}
