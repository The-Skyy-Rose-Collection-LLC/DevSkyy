/**
 * Meshy API Route Handler
 *
 * Proxies 3D generation requests to the Meshy API with proper
 * authentication and returns standardized Job3D format.
 *
 * POST /api/pipeline/meshy — Submit a text-to-3d or image-to-3d job
 * GET  /api/pipeline/meshy?task_id=xxx&type=text|image — Check job status
 */

import { NextRequest, NextResponse } from 'next/server';
import { meshyClient, toJob3D } from '@/lib/meshy/client';
import { getMeshyConnectionStatus } from '@/lib/meshy/config';

// ---------------------------------------------------------------------------
// POST — Submit a generation job
// ---------------------------------------------------------------------------

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { input_type, prompt, image_url, art_style, mode } = body as {
      input_type?: string;
      prompt?: string;
      image_url?: string;
      art_style?: string;
      mode?: string;
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

      const task = await meshyClient.textTo3D({
        mode: (mode as 'preview' | 'refine') || 'preview',
        prompt: prompt.trim(),
        art_style: art_style as MeshyArtStyle | undefined,
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

    const task = await meshyClient.imageTo3D({
      image_url: image_url.trim(),
    });

    const job = toJob3D(task, 'image', image_url.trim());
    return NextResponse.json(job, { status: 201 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Internal server error';
    console.error('Meshy POST error:', error);
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
    const inputType = searchParams.get('type') as 'text' | 'image' | null;

    // If no task_id, return connection status
    if (!taskId) {
      const status = getMeshyConnectionStatus();
      return NextResponse.json({
        provider: 'meshy',
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

    const type = inputType || 'text';

    const task =
      type === 'image'
        ? await meshyClient.getImageTo3DTask(taskId)
        : await meshyClient.getTextTo3DTask(taskId);

    const job = toJob3D(task, type, task.prompt || '');
    return NextResponse.json(job);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Internal server error';
    console.error('Meshy GET error:', error);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

// ---------------------------------------------------------------------------
// Helper type (keeps the import out of the function body)
// ---------------------------------------------------------------------------

type MeshyArtStyle =
  | 'realistic'
  | 'sculpture'
  | 'pbr'
  | 'cartoon'
  | 'low-poly'
  | 'anime'
  | 'voxel';
