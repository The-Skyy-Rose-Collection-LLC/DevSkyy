/**
 * Tripo 3D API Client
 *
 * Wraps the Tripo v2 OpenAPI for text-to-3d and image-to-3d generation.
 * Falls back to dry-run mode with mock data when TRIPO_API_KEY is not set.
 *
 * API Docs: https://platform.tripo3d.ai/docs/api
 * Base URL: https://api.tripo3d.ai/v2/openapi
 * Auth: Authorization: Bearer ${TRIPO_API_KEY}
 */

import { getTripoApiKey, TRIPO_CONFIG } from './config';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface TripoTextTo3DRequest {
  prompt: string;
  model_version?: string;
}

export interface TripoImageTo3DRequest {
  file_token: string;
  model_version?: string;
}

export type TripoTaskStatus =
  | 'queued'
  | 'running'
  | 'success'
  | 'failed'
  | 'cancelled'
  | 'unknown';

export interface TripoTaskOutput {
  model?: string;
  rendered_image?: string;
}

export interface TripoTaskData {
  task_id: string;
  type: string;
  status: TripoTaskStatus;
  input: Record<string, unknown>;
  output: TripoTaskOutput;
  progress: number;
}

export interface TripoApiResponse<T = TripoTaskData> {
  code: number;
  data: T;
}

export interface TripoUploadData {
  image_token: string;
}

// ---------------------------------------------------------------------------
// Dry-run mock helpers
// ---------------------------------------------------------------------------

function mockTaskId(): string {
  return `mock_tripo_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function createMockTaskData(
  input: string,
  inputType: 'text' | 'image'
): TripoTaskData {
  return {
    task_id: mockTaskId(),
    type: inputType === 'text' ? 'text_to_model' : 'image_to_model',
    status: 'queued',
    input: inputType === 'text' ? { prompt: input } : { file_token: input },
    output: {},
    progress: 0,
  };
}

function createMockCompletedTaskData(
  taskId: string,
  input: string,
  inputType: 'text' | 'image'
): TripoTaskData {
  return {
    task_id: taskId,
    type: inputType === 'text' ? 'text_to_model' : 'image_to_model',
    status: 'success',
    input: inputType === 'text' ? { prompt: input } : { file_token: input },
    output: {
      model: `https://mock.tripo3d.ai/models/${taskId}/model.glb`,
      rendered_image: `https://mock.tripo3d.ai/models/${taskId}/rendered.png`,
    },
    progress: 100,
  };
}

// ---------------------------------------------------------------------------
// HTTP helpers
// ---------------------------------------------------------------------------

async function tripoFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const apiKey = getTripoApiKey();
  if (!apiKey) {
    throw new Error('Tripo API key not configured — use dry-run mode');
  }

  const url = `${TRIPO_CONFIG.base_url}${path}`;
  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    TRIPO_CONFIG.default_timeout_ms
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
        `Tripo API error ${response.status}: ${body || response.statusText}`
      );
    }

    return (await response.json()) as T;
  } finally {
    clearTimeout(timeout);
  }
}

/**
 * Upload an image to Tripo and receive a file_token.
 * Uses multipart/form-data — the Content-Type header is set by the browser.
 */
async function tripoUpload(imageUrl: string): Promise<string> {
  const apiKey = getTripoApiKey();
  if (!apiKey) {
    throw new Error('Tripo API key not configured — use dry-run mode');
  }

  // Fetch the image from the provided URL
  const imageResponse = await fetch(imageUrl);
  if (!imageResponse.ok) {
    throw new Error(`Failed to fetch image from ${imageUrl}`);
  }
  const imageBlob = await imageResponse.blob();

  const formData = new FormData();
  formData.append('file', imageBlob, 'image.png');

  const url = `${TRIPO_CONFIG.base_url}/upload`;
  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    TRIPO_CONFIG.default_timeout_ms
  );

  try {
    const response = await fetch(url, {
      method: 'POST',
      signal: controller.signal,
      headers: {
        Authorization: `Bearer ${apiKey}`,
        // Do NOT set Content-Type — fetch sets it with the boundary for FormData
      },
      body: formData,
    });

    if (!response.ok) {
      const body = await response.text().catch(() => '');
      throw new Error(
        `Tripo upload error ${response.status}: ${body || response.statusText}`
      );
    }

    const result = (await response.json()) as TripoApiResponse<TripoUploadData>;
    return result.data.image_token;
  } finally {
    clearTimeout(timeout);
  }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

export const tripoClient = {
  /**
   * Check if client will make real API calls or return mock data.
   */
  isDryRun(): boolean {
    return !getTripoApiKey();
  },

  /**
   * Submit a text-to-3D generation task.
   * POST /task — { type: "text_to_model", prompt, model_version? }
   */
  async textTo3D(request: TripoTextTo3DRequest): Promise<TripoTaskData> {
    if (this.isDryRun()) {
      return createMockTaskData(request.prompt, 'text');
    }

    const body = {
      type: 'text_to_model',
      prompt: request.prompt,
      ...(request.model_version && { model_version: request.model_version }),
    };

    const result = await tripoFetch<TripoApiResponse>('/task', {
      method: 'POST',
      body: JSON.stringify(body),
    });

    return result.data;
  },

  /**
   * Submit an image-to-3D generation task.
   * First uploads the image via POST /upload, then submits the task.
   * POST /task — { type: "image_to_model", file: { type: "image", file_token } }
   */
  async imageTo3D(request: TripoImageTo3DRequest): Promise<TripoTaskData> {
    if (this.isDryRun()) {
      return createMockTaskData(request.file_token, 'image');
    }

    const body = {
      type: 'image_to_model',
      file: {
        type: 'image',
        file_token: request.file_token,
      },
      ...(request.model_version && { model_version: request.model_version }),
    };

    const result = await tripoFetch<TripoApiResponse>('/task', {
      method: 'POST',
      body: JSON.stringify(body),
    });

    return result.data;
  },

  /**
   * Upload an image and receive a file_token for use with imageTo3D.
   * POST /upload — multipart/form-data with file field
   */
  async uploadImage(imageUrl: string): Promise<string> {
    if (this.isDryRun()) {
      return `mock_token_${Date.now()}`;
    }

    return tripoUpload(imageUrl);
  },

  /**
   * Get the status of a task.
   * GET /task/{task_id}
   */
  async getTask(taskId: string): Promise<TripoTaskData> {
    if (this.isDryRun()) {
      return createMockCompletedTaskData(taskId, 'mock prompt', 'text');
    }

    const result = await tripoFetch<TripoApiResponse>(`/task/${taskId}`);
    return result.data;
  },
};

// ---------------------------------------------------------------------------
// Helpers to map Tripo responses to the standard Job3D format
// ---------------------------------------------------------------------------

const STATUS_MAP: Record<TripoTaskStatus, 'queued' | 'processing' | 'completed' | 'failed'> = {
  queued: 'queued',
  running: 'processing',
  success: 'completed',
  failed: 'failed',
  cancelled: 'failed',
  unknown: 'queued',
};

/**
 * Convert a Tripo task response to the standard Job3D shape
 * used by the frontend pipeline.
 */
export function toJob3D(
  task: TripoTaskData,
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
    id: task.task_id,
    status: STATUS_MAP[task.status] ?? 'queued',
    provider: 'tripo',
    input_type: inputType,
    input,
    output_url: task.output.model || undefined,
    error: task.status === 'failed' ? 'Task failed' : undefined,
    created_at: new Date().toISOString(),
    completed_at: task.status === 'success' ? new Date().toISOString() : undefined,
  };
}
