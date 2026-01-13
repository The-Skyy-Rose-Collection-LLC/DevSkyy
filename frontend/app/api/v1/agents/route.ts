import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'https://devskyy-backend.onrender.com';

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/agents`, {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      // Cache for 5 minutes (agents list doesn't change frequently)
      next: { revalidate: 300 },
    });

    if (!response.ok) {
      return NextResponse.json(
        {
          error: 'Failed to fetch agents',
          status: response.status,
          statusText: response.statusText,
        },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json(data, {
      headers: {
        'Cache-Control': 'public, s-maxage=300, stale-while-revalidate=600',
      },
    });
  } catch (error) {
    console.error('Agents fetch error:', error);

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
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
