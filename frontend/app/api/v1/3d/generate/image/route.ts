import { NextRequest, NextResponse } from 'next/server';
import { extractBearerToken } from '@/lib/api/client';
import { ApiError } from '@/lib/api/errors';
import { meshyClient, toJob3D as meshyToJob3D } from '@/lib/meshy/client';
import {
  tripoClient,
  toJob3D as tripoToJob3D,
  productNameFromImageUrl,
} from '@/lib/tripo/client';
import { jobStore } from '../../jobs/route';

export async function POST(request: NextRequest) {
  let body: { image_url?: string; provider?: string; product_name?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const imageUrl = body.image_url;
  if (!imageUrl) {
    return NextResponse.json({ error: 'image_url is required' }, { status: 400 });
  }

  try {
    new URL(imageUrl);
  } catch {
    return NextResponse.json({ error: 'Invalid image URL' }, { status: 400 });
  }

  if (imageUrl.length > 2000) {
    return NextResponse.json({ error: 'Image URL too long' }, { status: 400 });
  }

  const provider = body.provider || 'meshy';

  try {
    let job;

    if (provider === 'tripo') {
      const authToken = extractBearerToken(request.headers);
      const generation = await tripoClient.imageTo3D(
        {
          product_name: body.product_name?.trim() || productNameFromImageUrl(imageUrl),
          image_url: imageUrl,
        },
        authToken
      );
      job = tripoToJob3D(generation, 'image', imageUrl);
    } else {
      const task = await meshyClient.imageTo3D({ image_url: imageUrl });
      job = meshyToJob3D(task, 'image', imageUrl);
    }

    jobStore.unshift(job);

    return NextResponse.json(job);
  } catch (err) {
    if (ApiError.isApiError(err)) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    return NextResponse.json({ error: 'Generation failed' }, { status: 500 });
  }
}
