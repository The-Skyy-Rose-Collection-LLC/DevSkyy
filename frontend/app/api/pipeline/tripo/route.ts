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
import { tripoClient, toJob3D } from '@/lib/tripo/client';
import { getTripoConnectionStatus } from '@/lib/tripo/config';

// ---------------------------------------------------------------------------
// POST — Submit a generation job
// ---------------------------------------------------------------------------

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { input_type, prompt, image_url, model_version } = body as {
      input_type?: string;
      prompt?: string;
      image_url?: string;
      model_version?: string;
    };

    if (!input_type || !['text', 'image'].includes(input_type)) {
      return NextResponse.json(
        { error: 'input_type must be "text" or "image"' },
        { status: 400 }
      );
    }

    if (input_type === 'text') {
      if (!prompt?.trim()) {
        return NextResponse.json(
          { error: 'prompt is required for text-to-3d' },
          { status: 400 }
        );
      }
      if (prompt.length > 5000) {
        return NextResponse.json(
          { error: 'prompt too long (max 5000 chars)' },
          { status: 400 }
        );
      }

      const task = await tripoClient.textTo3D({
        prompt: prompt.trim(),
        model_version: model_version || undefined,
      });

      const job = toJob3D(task, 'text', prompt.trim());
      return NextResponse.json(job, { status: 201 });
    }

    // image-to-3d
    if (!image_url?.trim()) {
      return NextResponse.json(
        { error: 'image_url is required for image-to-3d' },
        { status: 400 }
      );
    }

    try {
      new URL(image_url);
    } catch {
      return NextResponse.json(
        { error: 'Invalid image_url' },
        { status: 400 }
      );
    }

    if (image_url.length > 2000) {
      return NextResponse.json(
        { error: 'image_url too long (max 2000 chars)' },
        { status: 400 }
      );
    }

    // Upload the image first to get a file_token, then submit the task
    const fileToken = await tripoClient.uploadImage(image_url.trim());

    const task = await tripoClient.imageTo3D({
      file_token: fileToken,
      model_version: model_version || undefined,
    });

    const job = toJob3D(task, 'image', image_url.trim());
    return NextResponse.json(job, { status: 201 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Internal server error';
    console.error('Tripo POST error:', error);
    return NextResponse.json({ error: message }, { status: 500 });
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

    const task = await tripoClient.getTask(taskId);

    const input =
      typeof task.input?.prompt === 'string'
        ? task.input.prompt
        : '';
    const inputType = task.type === 'image_to_model' ? 'image' : 'text';

    const job = toJob3D(task, inputType as 'text' | 'image', input);
    return NextResponse.json(job);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Internal server error';
    console.error('Tripo GET error:', error);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
