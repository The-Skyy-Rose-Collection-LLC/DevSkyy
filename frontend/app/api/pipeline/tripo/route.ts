/**
 * Tripo 3D API Route Handler
 *
 * Proxies 3D generation requests to the Tripo API with proper
 * authentication and returns standardized Job3D format.
 *
 * POST /api/pipeline/tripo — Submit a text-to-3d or image-to-3d job
 * GET  /api/pipeline/tripo?task_id=xxx — Check job status or return connection info
 */

import { NextRequest, NextResponse } from 'next/server';
import { extractBearerToken } from '@/lib/api/client';
import { ApiError } from '@/lib/api/errors';
import {
  tripoClient,
  toJob3D,
  productNameFromPrompt,
  productNameFromImageUrl,
} from '@/lib/tripo/client';
import { getTripoConnectionStatus } from '@/lib/tripo/config';

// ---------------------------------------------------------------------------
// POST — Submit a generation job
// ---------------------------------------------------------------------------

async function handleTextTo3D(prompt: string | undefined, authToken: string | null) {
  if (!prompt?.trim()) {
    return NextResponse.json({ error: 'prompt is required for text-to-3d' }, { status: 400 });
  }
  if (prompt.length > 5000) {
    return NextResponse.json({ error: 'prompt too long (max 5000 chars)' }, { status: 400 });
  }

  const trimmedPrompt = prompt.trim();
  const generation = await tripoClient.textTo3D(
    {
      product_name: productNameFromPrompt(trimmedPrompt),
      additional_details: trimmedPrompt.slice(0, 1000),
    },
    authToken
  );

  const job = toJob3D(generation, 'text', trimmedPrompt);
  return NextResponse.json(job, { status: 201 });
}

async function handleImageTo3D(
  imageUrl: string | undefined,
  productName: string | undefined,
  authToken: string | null
) {
  if (!imageUrl?.trim()) {
    return NextResponse.json({ error: 'image_url is required for image-to-3d' }, { status: 400 });
  }

  try {
    new URL(imageUrl);
  } catch {
    return NextResponse.json({ error: 'Invalid image_url' }, { status: 400 });
  }

  if (imageUrl.length > 2000) {
    return NextResponse.json({ error: 'image_url too long (max 2000 chars)' }, { status: 400 });
  }

  const trimmedImageUrl = imageUrl.trim();
  const generation = await tripoClient.imageTo3D(
    {
      product_name: productName?.trim() || productNameFromImageUrl(trimmedImageUrl),
      image_url: trimmedImageUrl,
    },
    authToken
  );

  const job = toJob3D(generation, 'image', trimmedImageUrl);
  return NextResponse.json(job, { status: 201 });
}

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  try {
    // NOTE: model_version is no longer accepted here — the real backend
    // (api/v1/media.py::ThreeDGenerationFromTextRequest/FromImageRequest)
    // has no such field; Tripo model selection is owned by the backend.
    const { input_type, prompt, image_url, product_name } = body as {
      input_type?: string;
      prompt?: string;
      image_url?: string;
      product_name?: string;
    };

    if (!input_type || !['text', 'image'].includes(input_type)) {
      return NextResponse.json(
        { error: 'input_type must be "text" or "image"' },
        { status: 400 }
      );
    }

    const authToken = extractBearerToken(request.headers);

    return input_type === 'text'
      ? await handleTextTo3D(prompt, authToken)
      : await handleImageTo3D(image_url, product_name, authToken);
  } catch (error) {
    console.error('Tripo POST error:', error);
    if (ApiError.isApiError(error)) {
      return NextResponse.json({ error: error.message }, { status: error.status });
    }
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// ---------------------------------------------------------------------------
// GET — Check job status or get connection info
// ---------------------------------------------------------------------------

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const taskId = searchParams.get('task_id');

    // If no task_id, return connection status
    if (!taskId) {
      const status = getTripoConnectionStatus();
      return NextResponse.json({
        provider: 'tripo',
        ...status,
      });
    }

    // Validate task_id format
    if (!/^[a-zA-Z0-9_-]+$/.test(taskId)) {
      return NextResponse.json(
        { error: 'Invalid task_id format' },
        { status: 400 }
      );
    }

    const authToken = extractBearerToken(request.headers);
    const generation = await tripoClient.getGenerationStatus(taskId, authToken);

    // ThreeDGenerationResponse doesn't echo the original request's
    // input_type/prompt/image_url back on status polls — only product_name
    // and output_format survive. Default input_type to 'text' and use the
    // real product_name as the closest available "input" label; a caller
    // that needs the original input_type must track it itself (e.g. via the
    // in-memory jobStore populated at creation time).
    const job = toJob3D(generation, 'text', generation.product_name);
    return NextResponse.json(job);
  } catch (error) {
    console.error('Tripo GET error:', error);
    if (ApiError.isApiError(error)) {
      return NextResponse.json({ error: error.message }, { status: error.status });
    }
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
