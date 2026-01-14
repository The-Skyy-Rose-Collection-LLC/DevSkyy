import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'https://devskyy.fly.dev';

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/health`, {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      // Note: Caching handled via Cache-Control response headers
    });

    if (!response.ok) {
      return NextResponse.json(
        {
          error: 'Backend health check failed',
          status: response.status,
          statusText: response.statusText,
        },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json(data, {
      headers: {
        'Cache-Control': 'public, s-maxage=30, stale-while-revalidate=60',
      },
    });
  } catch (error) {
    console.error('Health check error:', error);

    return NextResponse.json(
      {
        error: 'Failed to connect to backend',
        details: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      },
      { status: 502 }
    );
  }
}

// Support CORS preflight
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
