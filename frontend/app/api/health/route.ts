/**
 * Health Check API Route Handler
 */

import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '3.0.0',
    environment: process.env.NODE_ENV || 'development',
    services: {
      api: 'operational',
      agents: 'operational',
      tools: 'operational'
    }
  });
}
