/**
 * Tasks API Route Handler
 * Returns task history with metrics for the Task History Panel
 */

import { NextResponse } from 'next/server';

// Generate realistic mock tasks with proper TaskResponse format
function generateMockTasks() {
  const agents = ['commerce', 'creative', 'marketing', 'support', 'operations', 'analytics'] as const;
  const providers = ['anthropic', 'openai', 'google', 'mistral', 'cohere', 'groq'] as const;
  const techniques = ['chain_of_thought', 'few_shot', 'react', 'rag', 'tree_of_thoughts'] as const;
  const statuses = ['completed', 'completed', 'completed', 'failed', 'running', 'pending'] as const;

  const prompts = [
    'Create a new product listing for Black Rose Collection',
    'Generate 3D model for luxury watch',
    'Create email campaign for holiday sale',
    'Analyze customer support tickets from last week',
    'Deploy WordPress theme update',
    'Generate sales forecast for Q1 2025',
    'Create virtual try-on for new jacket',
    'Optimize product descriptions for SEO',
    'Process bulk order #12345',
    'Generate social media content calendar',
    'Update inventory levels across warehouses',
    'Create customer segmentation report',
    'Design homepage banner for Love Hurts collection',
    'Respond to support ticket #5678',
    'Monitor system health metrics',
  ];

  return Array.from({ length: 15 }, (_, i) => {
    const status = statuses[i % statuses.length];
    const startTime = new Date(Date.now() - (i + 1) * 1800000);
    const durationMs = Math.floor(Math.random() * 5000) + 500;
    const endTime = status === 'completed' || status === 'failed'
      ? new Date(startTime.getTime() + durationMs)
      : undefined;

    return {
      taskId: `task-${String(i + 1).padStart(3, '0')}`,
      agentType: agents[i % agents.length],
      prompt: prompts[i % prompts.length],
      status: status as 'pending' | 'running' | 'completed' | 'failed',
      result: status === 'completed' ? { success: true } : status === 'failed' ? { success: false } : undefined,
      error: status === 'failed' ? 'Task execution timeout' : undefined,
      createdAt: startTime.toISOString(),
      metrics: {
        startTime: startTime.toISOString(),
        endTime: endTime?.toISOString(),
        durationMs: status === 'completed' || status === 'failed' ? durationMs : undefined,
        tokensUsed: status === 'completed' ? Math.floor(Math.random() * 2000) + 500 : undefined,
        costUsd: status === 'completed' ? Math.random() * 0.05 + 0.001 : undefined,
        provider: providers[i % providers.length],
        promptTechnique: techniques[i % techniques.length],
      },
    };
  });
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const agentType = searchParams.get('agent_type');
  const status = searchParams.get('status');
  const limit = parseInt(searchParams.get('limit') || '20', 10);

  let tasks = generateMockTasks();

  // Filter by agent type if provided
  if (agentType) {
    tasks = tasks.filter((t) => t.agentType === agentType);
  }

  // Filter by status if provided
  if (status) {
    tasks = tasks.filter((t) => t.status === status);
  }

  // Apply limit
  tasks = tasks.slice(0, limit);

  return NextResponse.json(tasks);
}

export async function POST(request: Request) {
  const body = await request.json();
  const newTask = {
    taskId: `task-${Date.now()}`,
    agentType: body.agent_type || body.agentType,
    prompt: body.prompt,
    status: 'pending' as const,
    createdAt: new Date().toISOString(),
    metrics: {
      startTime: new Date().toISOString(),
    },
  };
  return NextResponse.json(newTask);
}
