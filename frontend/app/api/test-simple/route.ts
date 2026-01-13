import { NextResponse } from 'next/server';

/**
 * Minimal test endpoint - no backend calls, just returns static JSON
 * Used to verify API routes are working at all in production
 */
export async function GET() {
  return NextResponse.json({
    status: 'ok',
    message: 'Simple test endpoint responding',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV,
  });
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}
