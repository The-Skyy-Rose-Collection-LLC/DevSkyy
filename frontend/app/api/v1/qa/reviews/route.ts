import { NextRequest } from 'next/server';

import { proxyToBackend } from '@/lib/api/server-proxy';

export async function GET(request: NextRequest) {
  const status = request.nextUrl.searchParams.get('status');
  const qs = status ? `?status=${encodeURIComponent(status)}` : '';
  return proxyToBackend(`/api/v1/qa/reviews${qs}`);
}
