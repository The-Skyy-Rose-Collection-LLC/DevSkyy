import { NextRequest } from 'next/server';

import { proxyToBackend } from '@/lib/api/server-proxy';

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.text();
  return proxyToBackend(`/api/v1/qa/reviews/${encodeURIComponent(id)}/regenerate`, {
    method: 'POST',
    body: body || '{}',
  });
}
