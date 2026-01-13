import { NextRequest, NextResponse } from 'next/server';
import { proxyToBackend, getCacheControlHeader, createErrorResponse } from '@/lib/api-proxy';

/**
 * Universal API proxy handler
 * Catches all /api/* requests not handled by specific route handlers
 * and forwards them to the backend.
 */

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params;
  return handleRequest(request, resolvedParams, 'GET');
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params;
  return handleRequest(request, resolvedParams, 'POST');
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params;
  return handleRequest(request, resolvedParams, 'PUT');
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params;
  return handleRequest(request, resolvedParams, 'DELETE');
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params;
  return handleRequest(request, resolvedParams, 'PATCH');
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
      'Access-Control-Max-Age': '86400',
    },
  });
}

async function handleRequest(
  request: NextRequest,
  params: { path: string[] },
  method: string
) {
  const path = `/api/${params.path.join('/')}`;

  // Get query parameters
  const searchParams = request.nextUrl.searchParams;
  const queryString = searchParams.toString();
  const fullPath = queryString ? `${path}?${queryString}` : path;

  console.log(`[API Proxy] ${method} ${fullPath}`);

  try {
    // Get request body for POST/PUT/PATCH
    let body: BodyInit | undefined;
    if (['POST', 'PUT', 'PATCH'].includes(method)) {
      try {
        body = JSON.stringify(await request.json());
      } catch {
        // Body might not be JSON
        body = await request.text();
      }
    }

    // Forward auth header if present
    const authHeader = request.headers.get('authorization');
    const customHeaders: Record<string, string> = {};
    if (authHeader) {
      customHeaders['Authorization'] = authHeader;
    }

    // Determine cache strategy based on path
    let revalidate = 0; // No cache by default

    // Cache safe GET requests
    if (method === 'GET') {
      if (path.includes('/health')) {
        revalidate = 30; // 30 seconds
      } else if (path.includes('/agents')) {
        revalidate = 300; // 5 minutes
      } else if (path.includes('/monitoring') || path.includes('/metrics')) {
        revalidate = 60; // 1 minute
      }
    }

    const response = await proxyToBackend(fullPath, method, {
      revalidate,
      timeout: 30000, // 30 second timeout
      headers: customHeaders,
    }, body);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[API Proxy] Backend error ${response.status}:`, errorText);

      return NextResponse.json(
        createErrorResponse(
          'Backend request failed',
          response.status,
          errorText
        ),
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json(data, {
      headers: {
        'Cache-Control': getCacheControlHeader(revalidate),
      },
    });
  } catch (error) {
    console.error(`[API Proxy] Error for ${fullPath}:`, error);

    return NextResponse.json(
      createErrorResponse(
        'Failed to connect to backend',
        502,
        error
      ),
      { status: 502 }
    );
  }
}
