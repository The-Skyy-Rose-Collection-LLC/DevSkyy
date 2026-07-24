import { NextRequest } from 'next/server';

import { proxyToBackend } from '@/lib/api/server-proxy';

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyToBackend(`/api/v1/qa/reviews/${encodeURIComponent(id)}`);
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.text();
  return proxyToBackend(`/api/v1/qa/reviews/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    body,
  });
}
