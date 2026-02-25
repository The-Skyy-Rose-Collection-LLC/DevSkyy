import { NextResponse } from 'next/server';
import { isMeshyConnected, MESHY_CONFIG } from '@/lib/meshy/config';
import { isTripoConnected, TRIPO_CONFIG } from '@/lib/tripo/config';

export async function GET() {
  const providers = [
    {
      id: MESHY_CONFIG.provider_id,
      name: MESHY_CONFIG.provider_name,
      type: MESHY_CONFIG.provider_type,
      capabilities: [...MESHY_CONFIG.capabilities],
      avg_generation_time_s: 90,
      status: isMeshyConnected() ? 'online' : 'offline',
    },
    {
      id: TRIPO_CONFIG.provider_id,
      name: TRIPO_CONFIG.provider_name,
      type: TRIPO_CONFIG.provider_type,
      capabilities: [...TRIPO_CONFIG.capabilities],
      avg_generation_time_s: 120,
      status: isTripoConnected() ? 'online' : 'offline',
    },
  ];

  return NextResponse.json(providers);
}
