/**
 * Meshy API Client
 *
 * Wraps the Meshy v2 API for text-to-3d and image-to-3d generation.
 * Falls back to dry-run mode with mock data when MESHY_API_KEY is not set.
 *
 * API Docs: https://docs.meshy.ai
 * Base URL: https://api.meshy.ai
 * Auth: Authorization: Bearer ${MESHY_API_KEY}
 */

import { getMeshyApiKey, MESHY_CONFIG } from './config';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface MeshyTextTo3DRequest {
  mode: 'preview' | 'refine';
  prompt: string;
  art_style?:
    | 'realistic'
    | 'sculpture'
    | 'pbr'
    | 'cartoon'
    | 'low-poly'
    | 'anime'
    | 'voxel';
  negative_prompt?: string;
  ai_model?: string;
  topology?: 'triangle' | 'quad';
  target_polycount?: number;
}

export interface MeshyImageTo3DRequest {
  image_url: string;
  ai_model?: string;
  topology?: 'triangle' | 'quad';
  target_polycount?: number;
}

export type MeshyTaskStatus =
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'SUCCEEDED'
  | 'FAILED'
  | 'EXPIRED';

export interface MeshyModelUrls {
  glb?: string;
  fbx?: string;
  usdz?: string;
  obj?: string;
}

export interface MeshyTaskResponse {
  id: string;
  mode: string;
  prompt?: string;
  art_style?: string;
  negative_prompt?: string;
  status: MeshyTaskStatus;
  progress: number;
  model_urls: MeshyModelUrls;
  thumbnail_url?: string;
  texture_urls?: Array<{ base_color?: string }>;
  created_at: number;
  started_at?: number;
  finished_at?: number;
  expires_at?: number;
  task_error?: { message: string };
}

// ---------------------------------------------------------------------------
// Dry-run mock helpers
// ---------------------------------------------------------------------------

function mockTaskId(): string {
  return `mock_meshy_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function createMockTask(
  input: string,
  inputType: 'text' | 'image'
): MeshyTaskResponse {
  return {
    id: mockTaskId(),
    mode: 'preview',
    prompt: inputType === 'text' ? input : undefined,
    status: 'PENDING',
    progress: 0,
    model_urls: {},
    created_at: Date.now(),
  };
}

function createMockCompletedTask(
  id: string,
  input: string,
  inputType: 'text' | 'image'
): MeshyTaskResponse {
  return {
    id,
    mode: 'preview',
    prompt: inputType === 'text' ? input : undefined,
    status: 'SUCCEEDED',
    progress: 100,
    model_urls: {
      glb: `https://mock.meshy.ai/models/${id}/model.glb`,
      fbx: `https://mock.meshy.ai/models/${id}/model.fbx`,
    },
    thumbnail_url: `https://mock.meshy.ai/models/${id}/thumbnail.png`,
    created_at: Date.now() - 120_000,
    started_at: Date.now() - 110_000,
    finished_at: Date.now(),
  };
}

// ---------------------------------------------------------------------------
// HTTP helpers
// ---------------------------------------------------------------------------

async function meshyFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const apiKey = getMeshyApiKey();
  if (!apiKey) {
    throw new Error('Meshy API key not configured — use dry-run mode');
  }

  const url = `${MESHY_CONFIG.base_url}${path}`;
  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    MESHY_CONFIG.default_timeout_ms
  );

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const body = await response.text().catch(() => '');
      throw new Error(
        `Meshy API error ${response.status}: ${body || response.statusText}`
      );
    }

    return (await response.json()) as T;
  } finally {
    clearTimeout(timeout);
  }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

export const meshyClient = {
  /**
   * Check if client will make real API calls or return mock data.
   */
  isDryRun(): boolean {
    return !getMeshyApiKey();
  },

  /**
   * Submit a text-to-3D generation task.
   * POST /v2/text-to-3d
   */
  async textTo3D(request: MeshyTextTo3DRequest): Promise<MeshyTaskResponse> {
    if (this.isDryRun()) {
      return createMockTask(request.prompt, 'text');
    }

    const body = {
      mode: request.mode,
      prompt: request.prompt,
      ...(request.art_style && { art_style: request.art_style }),
      ...(request.negative_prompt && {
        negative_prompt: request.negative_prompt,
      }),
      ...(request.ai_model && { ai_model: request.ai_model }),
      ...(request.topology && { topology: request.topology }),
      ...(request.target_polycount && {
        target_polycount: request.target_polycount,
      }),
    };

    return meshyFetch<MeshyTaskResponse>('/v2/text-to-3d', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  /**
   * Submit an image-to-3D generation task.
   * POST /v2/image-to-3d
   */
  async imageTo3D(request: MeshyImageTo3DRequest): Promise<MeshyTaskResponse> {
    if (this.isDryRun()) {
      return createMockTask(request.image_url, 'image');
    }

    const body = {
      image_url: request.image_url,
      ...(request.ai_model && { ai_model: request.ai_model }),
      ...(request.topology && { topology: request.topology }),
      ...(request.target_polycount && {
        target_polycount: request.target_polycount,
      }),
    };

    return meshyFetch<MeshyTaskResponse>('/v2/image-to-3d', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  /**
   * Get the status of a text-to-3D task.
   * GET /v2/text-to-3d/{id}
   */
  async getTextTo3DTask(taskId: string): Promise<MeshyTaskResponse> {
    if (this.isDryRun()) {
      return createMockCompletedTask(taskId, 'mock prompt', 'text');
    }

    return meshyFetch<MeshyTaskResponse>(`/v2/text-to-3d/${taskId}`);
  },

  /**
   * Get the status of an image-to-3D task.
   * GET /v2/image-to-3d/{id}
   */
  async getImageTo3DTask(taskId: string): Promise<MeshyTaskResponse> {
    if (this.isDryRun()) {
      return createMockCompletedTask(taskId, 'mock image', 'image');
    }

    return meshyFetch<MeshyTaskResponse>(`/v2/image-to-3d/${taskId}`);
  },
};

// ---------------------------------------------------------------------------
// Helpers to map Meshy responses to the standard Job3D format
// ---------------------------------------------------------------------------

const STATUS_MAP: Record<MeshyTaskStatus, 'queued' | 'processing' | 'completed' | 'failed'> = {
  PENDING: 'queued',
  IN_PROGRESS: 'processing',
  SUCCEEDED: 'completed',
  FAILED: 'failed',
  EXPIRED: 'failed',
};

/**
 * Convert a Meshy task response to the standard Job3D shape
 * used by the frontend pipeline.
 */
export function toJob3D(
  task: MeshyTaskResponse,
  inputType: 'text' | 'image',
  input: string
): {
  id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  provider: string;
  input_type: 'text' | 'image';
  input: string;
  output_url?: string;
  error?: string;
  created_at: string;
  completed_at?: string;
} {
  return {
    id: task.id,
    status: STATUS_MAP[task.status] ?? 'queued',
    provider: 'meshy',
    input_type: inputType,
    input,
    output_url: task.model_urls.glb || task.model_urls.fbx || undefined,
    error: task.task_error?.message,
    created_at: new Date(task.created_at).toISOString(),
    completed_at: task.finished_at
      ? new Date(task.finished_at).toISOString()
      : undefined,
  };
}
