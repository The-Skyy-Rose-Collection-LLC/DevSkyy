import { getServerSession } from 'next-auth';
import { NextResponse } from 'next/server';

import { authOptions } from '@/lib/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Bearer-forwarding helper for Route Handlers that proxy to the FastAPI
 * backend. Reads the backend JWT NextAuth minted at login and stored on
 * `session.accessToken` (see lib/auth.ts's jwt/session callbacks) rather
 * than decoding NextAuth's own session token — decoding NextAuth's internal
 * token in a third-party backend is explicitly discouraged by the NextAuth
 * maintainers (nextauthjs/next-auth#5904); minting a separate backend token
 * and carrying it through the session is the recommended pattern.
 */
export async function proxyToBackend(path: string, init: RequestInit = {}): Promise<NextResponse> {
  const session = await getServerSession(authOptions);
  const accessToken = (session as { accessToken?: string } | null)?.accessToken;
  if (!accessToken) {
    // `detail` (not `error`) so the client's ApiError.fromResponse — which
    // reads detail || message — surfaces the real reason instead of a generic
    // "Request failed"; this matches FastAPI's own HTTPException body shape.
    return NextResponse.json({ detail: 'Unauthorized' }, { status: 401 });
  }

  let backendResponse: Response;
  try {
    backendResponse = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...init.headers,
        Authorization: `Bearer ${accessToken}`,
      },
    });
  } catch {
    return NextResponse.json({ detail: 'Failed to reach backend' }, { status: 502 });
  }

  const contentType = backendResponse.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    const data = await backendResponse.json();
    return NextResponse.json(data, { status: backendResponse.status });
  }

  const text = await backendResponse.text();
  return new NextResponse(text, {
    status: backendResponse.status,
    headers: { 'Content-Type': contentType || 'text/plain' },
  });
}
