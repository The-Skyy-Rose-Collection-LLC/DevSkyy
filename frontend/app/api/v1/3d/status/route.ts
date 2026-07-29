import { NextResponse } from 'next/server';
import { withAuth } from '@/lib/api-auth';
import { isMeshyConnected } from '@/lib/meshy/config';
import { isTripoConnected } from '@/lib/tripo/config';

async function getHandler() {
  const meshyOnline = isMeshyConnected();
  const tripoOnline = isTripoConnected();
  const providersOnline = [meshyOnline, tripoOnline].filter(Boolean).length;

  return NextResponse.json({
    status: providersOnline > 0 ? 'healthy' : 'degraded',
    active_jobs: 0,
    queued_jobs: 0,
    providers_online: providersOnline,
    providers_total: 2,
  });
}

export const GET = withAuth(getHandler);
