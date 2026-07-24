/**
 * Tripo 3D Generation Client
 *
 * Wraps the DevSkyy FastAPI backend's Tripo3D-backed 3D generation endpoints:
 *   POST /api/v1/media/3d/generate/text
 *   POST /api/v1/media/3d/generate/image
 *   GET  /api/v1/media/3d/{generation_id}/status
 * (api/v1/media.py). The backend owns the Tripo3D credentials and dispatches
 * agents/tripo_agent.py::TripoAssetAgent as a background task — this client
 * never talks to Tripo3D directly.
 *
 * Falls back to dry-run mode with mock data when no caller-supplied auth
 * token is present (e.g. local dev without a logged-in session). The routes
 * are JWT-gated (Depends(get_current_user)), and the callers of this client
 * are Next.js Route Handlers, which run server-side — there is no
 * `window`/`localStorage` there, so the token can't be read via
 * lib/api/client.ts's getAuthToken(). Callers must extract it from the
 * incoming request (lib/api/client.ts's extractBearerToken()) and thread it
 * in explicitly.
 */

import { fetchWithTimeout, handleResponse } from '@/lib/api/client';
import { API_URL } from '@/lib/api/config';
import { ThreeDGenerationResponseSchema } from '@/lib/api/schemas';
import type { ThreeDGenerationResponse } from '@/lib/api/types';
import { TRIPO_CONFIG } from './config';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ThreeDOutputFormat = 'glb' | 'gltf' | 'fbx' | 'obj' | 'usdz' | 'stl';

export interface TripoTextTo3DRequest {
  product_name: string;
  collection?: string;
  garment_type?: string;
  additional_details?: string;
  output_format?: ThreeDOutputFormat;
}

export interface TripoImageTo3DRequest {
  product_name: string;
  image_url: string;
  output_format?: ThreeDOutputFormat;
}

export type { ThreeDGenerationResponse };

// ---------------------------------------------------------------------------
// product_name derivation helpers
//
// ThreeDGenerationFromTextRequest/ThreeDGenerationFromImageRequest both
// require product_name (1-200 chars, no default). Upstream callers in this
// codebase only carry a free-text prompt or an image URL — these derive a
// real, non-fabricated product_name from that actual input.
// ---------------------------------------------------------------------------

const MAX_PRODUCT_NAME_LENGTH = 200;

/** Derive a Pydantic-valid product_name (1-200 chars) from a free-text prompt. */
export function productNameFromPrompt(prompt: string): string {
  const trimmed = prompt.trim();
  return trimmed.length > MAX_PRODUCT_NAME_LENGTH
    ? `${trimmed.slice(0, MAX_PRODUCT_NAME_LENGTH - 3)}...`
    : trimmed;
}

/**
 * Derive a best-effort product_name from an image URL's filename when the
 * caller doesn't supply one explicitly. Base64/data URIs carry no filename
 * to derive from and fall back to a generic label — callers that can supply
 * a real product_name (e.g. a SKU-bound upload) should always pass one.
 */
export function productNameFromImageUrl(imageUrl: string): string {
  if (imageUrl.startsWith('data:')) {
    return 'Uploaded Image';
  }
  try {
    const { pathname } = new URL(imageUrl);
    const filename = pathname.split('/').filter(Boolean).pop();
    if (!filename) return 'Uploaded Image';
    const base = filename
      .replace(/\.[a-zA-Z0-9]+$/, '')
      .replace(/[-_]+/g, ' ')
      .trim();
    return base ? productNameFromPrompt(base) : 'Uploaded Image';
  } catch {
    return 'Uploaded Image';
  }
}

// ---------------------------------------------------------------------------
// Dry-run mock helpers
// ---------------------------------------------------------------------------

function mockGenerationId(): string {
  return `mock_gen_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function createMockGenerationResponse(
  productName: string,
  outputFormat: ThreeDOutputFormat,
  estimatedCompletionTime: string
): ThreeDGenerationResponse {
  return {
    generation_id: mockGenerationId(),
    status: 'processing',
    timestamp: new Date().toISOString(),
    product_name: productName,
    output_format: outputFormat,
    model_url: null,
    preview_url: null,
    download_url: null,
    metadata: null,
    estimated_completion_time: estimatedCompletionTime,
  };
}

function createMockCompletedGenerationResponse(
  generationId: string
): ThreeDGenerationResponse {
  const modelUrl = `https://mock.devskyy.app/3d/${generationId}/model.glb`;
  return {
    generation_id: generationId,
    status: 'completed',
    timestamp: new Date().toISOString(),
    product_name: 'Mock Product',
    output_format: 'glb',
    model_url: modelUrl,
    preview_url: `https://mock.devskyy.app/3d/${generationId}/preview.png`,
    download_url: modelUrl,
    metadata: null,
    estimated_completion_time: null,
  };
}

// ---------------------------------------------------------------------------
// HTTP helpers
// ---------------------------------------------------------------------------

async function backendFetch3D(
  path: string,
  options: RequestInit,
  authToken: string
): Promise<ThreeDGenerationResponse> {
  const response = await fetchWithTimeout(
    `${API_URL}${path}`,
    {
      ...options,
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    },
    TRIPO_CONFIG.default_timeout_ms
  );

  return handleResponse(response, ThreeDGenerationResponseSchema);
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

export const tripoClient = {
  /**
   * Check whether a call will hit the real DevSkyy backend or return mock
   * data. Gated on auth-token presence — the backend owns the Tripo3D
   * credentials, so the frontend's only decision point is whether it has a
   * caller identity to send.
   */
  isDryRun(authToken?: string | null): boolean {
    return !authToken;
  },

  /**
   * Submit a text-to-3D generation job.
   * POST /api/v1/media/3d/generate/text
   */
  async textTo3D(
    request: TripoTextTo3DRequest,
    authToken?: string | null
  ): Promise<ThreeDGenerationResponse> {
    if (!authToken) {
      return createMockGenerationResponse(
        request.product_name,
        request.output_format ?? 'glb',
        '2-5 minutes'
      );
    }

    return backendFetch3D(
      '/api/v1/media/3d/generate/text',
      { method: 'POST', body: JSON.stringify(request) },
      authToken
    );
  },

  /**
   * Submit an image-to-3D generation job.
   * POST /api/v1/media/3d/generate/image
   */
  async imageTo3D(
    request: TripoImageTo3DRequest,
    authToken?: string | null
  ): Promise<ThreeDGenerationResponse> {
    if (!authToken) {
      return createMockGenerationResponse(
        request.product_name,
        request.output_format ?? 'glb',
        '3-7 minutes'
      );
    }

    return backendFetch3D(
      '/api/v1/media/3d/generate/image',
      { method: 'POST', body: JSON.stringify(request) },
      authToken
    );
  },

  /**
   * Poll the status of a generation job.
   * GET /api/v1/media/3d/{generation_id}/status
   */
  async getGenerationStatus(
    generationId: string,
    authToken?: string | null
  ): Promise<ThreeDGenerationResponse> {
    if (!authToken) {
      return createMockCompletedGenerationResponse(generationId);
    }

    return backendFetch3D(
      `/api/v1/media/3d/${generationId}/status`,
      { method: 'GET' },
      authToken
    );
  },
};

// ---------------------------------------------------------------------------
// Helpers to map ThreeDGenerationResponse to the standard Job3D format
// ---------------------------------------------------------------------------

const STATUS_MAP: Record<string, 'queued' | 'processing' | 'completed' | 'failed'> = {
  processing: 'processing',
  completed: 'completed',
  failed: 'failed',
};

/**
 * Convert a DevSkyy 3D generation response to the standard Job3D shape
 * used by the frontend pipeline.
 */
export function toJob3D(
  response: ThreeDGenerationResponse,
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
  const status = STATUS_MAP[response.status] ?? 'queued';
  const finished = status === 'completed' || status === 'failed';

  return {
    id: response.generation_id,
    status,
    provider: 'tripo',
    input_type: inputType,
    input,
    output_url: response.model_url ?? undefined,
    error: status === 'failed' ? 'Generation failed' : undefined,
    created_at: response.timestamp,
    completed_at: finished ? response.timestamp : undefined,
  };
}
