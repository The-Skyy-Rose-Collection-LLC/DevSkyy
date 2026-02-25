import { NextResponse } from 'next/server';
import { isMeshyConnected } from '@/lib/meshy/config';
import { isTripoConnected } from '@/lib/tripo/config';

export async function GET() {
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
