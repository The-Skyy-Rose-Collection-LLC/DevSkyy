import { NextRequest, NextResponse } from 'next/server';
import { extractBearerToken } from '@/lib/api/client';
import { ApiError } from '@/lib/api/errors';
import { meshyClient, toJob3D as meshyToJob3D } from '@/lib/meshy/client';
import {
  tripoClient,
  toJob3D as tripoToJob3D,
  productNameFromPrompt,
} from '@/lib/tripo/client';
import { jobStore } from '../../jobs/route';

export async function POST(request: NextRequest) {
  let body: { prompt?: string; provider?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const prompt = body.prompt?.trim();
  if (!prompt) {
    return NextResponse.json({ error: 'Prompt is required' }, { status: 400 });
  }
  if (prompt.length > 5000) {
    return NextResponse.json({ error: 'Prompt too long (max 5000 chars)' }, { status: 400 });
  }

  const provider = body.provider || 'meshy';

  try {
    let job;

    if (provider === 'tripo') {
      const authToken = extractBearerToken(request.headers);
      const generation = await tripoClient.textTo3D(
        {
          product_name: productNameFromPrompt(prompt),
          additional_details: prompt.slice(0, 1000),
        },
        authToken
      );
      job = tripoToJob3D(generation, 'text', prompt);
    } else {
      const task = await meshyClient.textTo3D({ mode: 'preview', prompt });
      job = meshyToJob3D(task, 'text', prompt);
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
