import { z } from 'zod';

// Environment validation
const API_URL = (() => {
  const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  try {
    new URL(url);
    return url;
  } catch {
    console.error('Invalid API_URL, falling back to localhost');
    return 'http://localhost:8000';
  }
})();

// =============================================================================
// ERROR HANDLING
// =============================================================================

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
    public readonly details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
    Object.setPrototypeOf(this, ApiError.prototype);
  }

  static isApiError(error: unknown): error is ApiError {
    return error instanceof ApiError;
  }

  static fromResponse(status: number, body: unknown): ApiError {
    if (typeof body === 'object' && body !== null) {
      const { detail, message, code } = body as Record<string, unknown>;
      return new ApiError(
        String(detail || message || 'Request failed'),
        status,
        typeof code === 'string' ? code : undefined,
        body
      );
    }
    return new ApiError('Request failed', status);
  }
}

// =============================================================================
// ZOD SCHEMAS - Runtime validation
// =============================================================================

// Schema matching backend ProviderInfo model
const ProviderInfoSchema = z.object({
  name: z.string(),
  display_name: z.string(),
  enabled: z.boolean(),
  avg_latency_ms: z.number(),
  win_rate: z.number(),
  total_competitions: z.number(),
});

// Schema matching backend ProviderStats model
const ProviderStatsSchema = z.object({
  provider: z.string(),
  total_competitions: z.number(),
  wins: z.number(),
  win_rate: z.number(),
  avg_score: z.number(),
  avg_latency_ms: z.number(),
  total_cost_usd: z.number(),
});

// Score breakdown schema
const EntryScoreSchema = z.object({
  relevance: z.number().default(0),
  quality: z.number().default(0),
  completeness: z.number().default(0),
  efficiency: z.number().default(0),
  brand_alignment: z.number().default(0),
  total: z.number().default(0),
});

// Competition entry schema matching backend
const CompetitionEntrySchema = z.object({
  provider: z.string(),
  rank: z.number(),
  scores: EntryScoreSchema,
  latency_ms: z.number(),
  cost_usd: z.number(),
  response_preview: z.string().default(''),
});

// Competition response matching backend
const CompetitionResponseSchema = z.object({
  id: z.string(),
  task_id: z.string(),
  prompt_preview: z.string(),
  status: z.string(),
  winner: CompetitionEntrySchema.nullable(),
  entries: z.array(CompetitionEntrySchema),
  ab_test_reasoning: z.string().nullable().optional(),
  ab_test_confidence: z.number().nullable().optional(),
  total_duration_ms: z.number(),
  total_cost_usd: z.number(),
  created_at: z.string(),
});

// History entry schema matching backend
const HistoryEntrySchema = z.object({
  id: z.string(),
  prompt_preview: z.string(),
  winner_provider: z.string(),
  winner_score: z.number(),
  total_cost_usd: z.number(),
  created_at: z.string(),
});

const PipelineStatusSchema = z.object({
  status: z.enum(['healthy', 'degraded', 'down']),
  active_jobs: z.number(),
  queued_jobs: z.number(),
  providers_online: z.number(),
  providers_total: z.number(),
});

const Provider3DSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.enum(['commercial', 'huggingface', 'local']),
  capabilities: z.array(z.string()),
  avg_generation_time_s: z.number(),
  status: z.enum(['online', 'offline', 'busy']),
});

const Job3DSchema = z.object({
  id: z.string(),
  status: z.enum(['queued', 'processing', 'completed', 'failed']),
  provider: z.string(),
  input_type: z.enum(['text', 'image']),
  input: z.string(),
  output_url: z.string().optional(),
  error: z.string().optional(),
  created_at: z.string(),
  completed_at: z.string().optional(),
});

const HealthResponseSchema = z.object({
  status: z.string(),
  version: z.string(),
  uptime: z.number(),
});

// Asset schemas
const AssetSchema = z.object({
  id: z.string(),
  filename: z.string(),
  path: z.string(),
  collection: z.enum(['black_rose', 'signature', 'love_hurts', 'showroom', 'runway']),
  type: z.enum(['image', '3d_model', 'video', 'texture']),
  metadata: z.object({
    sku: z.string().optional(),
    product_name: z.string().optional(),
    tags: z.array(z.string()).optional(),
    width: z.number().optional(),
    height: z.number().optional(),
    size_bytes: z.number().optional(),
    format: z.string().optional(),
  }).optional(),
  thumbnail_url: z.string().optional(),
  created_at: z.string(),
  updated_at: z.string().optional(),
});

const AssetListResponseSchema = z.object({
  assets: z.array(AssetSchema),
  total: z.number(),
  page: z.number(),
  limit: z.number(),
  has_more: z.boolean(),
});

// QA Review schemas
const QAReviewSchema = z.object({
  id: z.string(),
  asset_id: z.string(),
  job_id: z.string(),
  reference_image_url: z.string(),
  generated_model_url: z.string(),
  fidelity_score: z.number().min(0).max(100),
  fidelity_breakdown: z.object({
    geometry: z.number(),
    materials: z.number(),
    colors: z.number(),
    proportions: z.number(),
    branding: z.number(),
    texture_detail: z.number(),
  }).optional(),
  status: z.enum(['pending', 'approved', 'rejected', 'regenerating']),
  notes: z.string().optional(),
  reviewed_by: z.string().optional(),
  created_at: z.string(),
  reviewed_at: z.string().optional(),
});

const QAReviewListResponseSchema = z.object({
  reviews: z.array(QAReviewSchema),
  total: z.number(),
  pending_count: z.number(),
  approved_count: z.number(),
  rejected_count: z.number(),
});

// Batch job schemas
const BatchJobSchema = z.object({
  id: z.string(),
  status: z.enum(['pending', 'processing', 'completed', 'failed', 'paused']),
  total_assets: z.number(),
  processed_assets: z.number(),
  failed_assets: z.number(),
  current_asset: z.string().optional(),
  progress_percentage: z.number(),
  started_at: z.string().optional(),
  completed_at: z.string().optional(),
  error_log: z.array(z.string()).optional(),
});

// =============================================================================
// TYPE EXPORTS (inferred from schemas)
// =============================================================================

export type ProviderInfo = z.infer<typeof ProviderInfoSchema>;
export type ProviderStats = z.infer<typeof ProviderStatsSchema>;
export type EntryScore = z.infer<typeof EntryScoreSchema>;
export type CompetitionEntry = z.infer<typeof CompetitionEntrySchema>;
export type CompetitionResponse = z.infer<typeof CompetitionResponseSchema>;
export type HistoryEntry = z.infer<typeof HistoryEntrySchema>;
export type PipelineStatus = z.infer<typeof PipelineStatusSchema>;
export type Provider3D = z.infer<typeof Provider3DSchema>;
export type Job3D = z.infer<typeof Job3DSchema>;
export type HealthResponse = z.infer<typeof HealthResponseSchema>;
export type Asset = z.infer<typeof AssetSchema>;
export type AssetListResponse = z.infer<typeof AssetListResponseSchema>;
export type QAReview = z.infer<typeof QAReviewSchema>;
export type QAReviewListResponse = z.infer<typeof QAReviewListResponseSchema>;
export type BatchJob = z.infer<typeof BatchJobSchema>;

// Request types (not from API, so defined manually)
export interface CompetitionRequest {
  prompt: string;
  providers?: string[];
  evaluation_criteria?: string[];
}

export interface TextTo3DRequest {
  prompt: string;
  provider?: string;
  quality?: 'draft' | 'standard' | 'high';
}

export interface ImageTo3DRequest {
  image_url: string;
  provider?: string;
  quality?: 'draft' | 'standard' | 'high';
}

export interface AssetFilters {
  collection?: 'black_rose' | 'signature' | 'love_hurts' | 'showroom' | 'runway';
  type?: 'image' | '3d_model' | 'video' | 'texture';
  search?: string;
  page?: number;
  limit?: number;
}

export interface AssetUpdateRequest {
  metadata?: {
    sku?: string;
    product_name?: string;
    tags?: string[];
  };
}

export interface BatchGenerationRequest {
  asset_ids: string[];
  provider?: string;
  quality?: 'draft' | 'standard' | 'high';
}

export interface QAReviewRequest {
  status: 'approved' | 'rejected';
  notes?: string;
}

export interface RegenerateRequest {
  provider?: string;
  quality?: 'draft' | 'standard' | 'high';
  adjustments?: {
    geometry?: number;
    materials?: number;
    lighting?: number;
  };
}

// =============================================================================
// REQUEST UTILITIES
// =============================================================================

const REQUEST_TIMEOUT = 30000; // 30 seconds

function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

async function getAuthHeaders(): Promise<HeadersInit> {
  const token = getAuthToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-Request-ID': crypto.randomUUID(),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeout = REQUEST_TIMEOUT
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

async function handleResponse<T>(
  response: Response,
  schema: z.ZodType<T>
): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw ApiError.fromResponse(response.status, body);
  }

  const data = await response.json();

  // Validate response against schema
  const result = schema.safeParse(data);
  if (!result.success) {
    console.error('API response validation failed:', result.error.issues);
    throw new ApiError(
      'Invalid API response format',
      500,
      'VALIDATION_ERROR',
      result.error.issues
    );
  }

  return result.data;
}

async function handleArrayResponse<T>(
  response: Response,
  schema: z.ZodType<T>
): Promise<T[]> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw ApiError.fromResponse(response.status, body);
  }

  const data = await response.json();

  if (!Array.isArray(data)) {
    throw new ApiError('Expected array response', 500, 'INVALID_FORMAT');
  }

  // Validate each item
  const results: T[] = [];
  for (const item of data) {
    const result = schema.safeParse(item);
    if (result.success) {
      results.push(result.data);
    } else {
      console.warn('Skipping invalid item:', result.error.issues);
    }
  }

  return results;
}

// =============================================================================
// API CLIENT
// =============================================================================

export const api = {
  // Round Table endpoints
  roundTable: {
    getProviders: async (): Promise<ProviderInfo[]> => {
      const res = await fetchWithTimeout(`${API_URL}/api/v1/round-table/providers`, {
        headers: await getAuthHeaders(),
      });
      return handleArrayResponse(res, ProviderInfoSchema);
    },

    getStats: async (): Promise<ProviderStats[]> => {
      const res = await fetchWithTimeout(`${API_URL}/api/v1/round-table/stats`, {
        headers: await getAuthHeaders(),
      });
      return handleArrayResponse(res, ProviderStatsSchema);
    },

    getHistory: async (limit = 10, offset = 0): Promise<HistoryEntry[]> => {
      // Sanitize inputs
      const safeLimit = Math.min(Math.max(1, limit), 100);
      const safeOffset = Math.max(0, offset);

      const res = await fetchWithTimeout(
        `${API_URL}/api/v1/round-table?limit=${safeLimit}&offset=${safeOffset}`,
        { headers: await getAuthHeaders() }
      );
      return handleArrayResponse(res, HistoryEntrySchema);
    },

    compete: async (request: CompetitionRequest): Promise<CompetitionResponse> => {
      // Validate input
      if (!request.prompt?.trim()) {
        throw new ApiError('Prompt is required', 400, 'INVALID_INPUT');
      }
      if (request.prompt.length > 10000) {
        throw new ApiError('Prompt too long (max 10000 chars)', 400, 'INVALID_INPUT');
      }

      const res = await fetchWithTimeout(`${API_URL}/api/v1/round-table/compete`, {
        method: 'POST',
        headers: await getAuthHeaders(),
        body: JSON.stringify({
          prompt: request.prompt.trim(),
          providers: request.providers,
          evaluation_criteria: request.evaluation_criteria,
        }),
      });
      return handleResponse(res, CompetitionResponseSchema);
    },
  },

  // 3D Pipeline endpoints
  pipeline3d: {
    getStatus: async (): Promise<PipelineStatus> => {
      const res = await fetchWithTimeout(`${API_URL}/api/v1/3d/status`, {
        headers: await getAuthHeaders(),
      });
      return handleResponse(res, PipelineStatusSchema);
    },

    getProviders: async (): Promise<Provider3D[]> => {
      const res = await fetchWithTimeout(`${API_URL}/api/v1/3d/providers`, {
        headers: await getAuthHeaders(),
      });
      return handleArrayResponse(res, Provider3DSchema);
    },

    getJobs: async (limit = 20): Promise<Job3D[]> => {
      const safeLimit = Math.min(Math.max(1, limit), 100);
      const res = await fetchWithTimeout(
        `${API_URL}/api/v1/3d/jobs?limit=${safeLimit}`,
        { headers: await getAuthHeaders() }
      );
      return handleArrayResponse(res, Job3DSchema);
    },

    getJob: async (jobId: string): Promise<Job3D> => {
      // Validate job ID format
      if (!jobId || !/^[a-zA-Z0-9_-]+$/.test(jobId)) {
        throw new ApiError('Invalid job ID format', 400, 'INVALID_INPUT');
      }

      const res = await fetchWithTimeout(`${API_URL}/api/v1/3d/jobs/${jobId}`, {
        headers: await getAuthHeaders(),
      });
      return handleResponse(res, Job3DSchema);
    },

    generateFromText: async (request: TextTo3DRequest): Promise<Job3D> => {
      if (!request.prompt?.trim()) {
        throw new ApiError('Prompt is required', 400, 'INVALID_INPUT');
      }
      if (request.prompt.length > 5000) {
        throw new ApiError('Prompt too long (max 5000 chars)', 400, 'INVALID_INPUT');
      }

      const res = await fetchWithTimeout(`${API_URL}/api/v1/3d/generate/text`, {
        method: 'POST',
        headers: await getAuthHeaders(),
        body: JSON.stringify({
          prompt: request.prompt.trim(),
          provider: request.provider,
          quality: request.quality || 'standard',
        }),
      });
      return handleResponse(res, Job3DSchema);
    },

    generateFromImage: async (request: ImageTo3DRequest): Promise<Job3D> => {
      // Validate URL
      try {
        new URL(request.image_url);
      } catch {
        throw new ApiError('Invalid image URL', 400, 'INVALID_INPUT');
      }

      // Basic URL sanitization
      if (request.image_url.length > 2000) {
        throw new ApiError('Image URL too long', 400, 'INVALID_INPUT');
      }

      const res = await fetchWithTimeout(`${API_URL}/api/v1/3d/generate/image`, {
        method: 'POST',
        headers: await getAuthHeaders(),
        body: JSON.stringify({
          image_url: request.image_url,
          provider: request.provider,
          quality: request.quality || 'standard',
        }),
      });
      return handleResponse(res, Job3DSchema);
    },
  },

  // Health endpoints (no auth required)
  health: {
    check: async (): Promise<HealthResponse> => {
      const res = await fetchWithTimeout(`${API_URL}/health`, {
        headers: { 'Content-Type': 'application/json' },
      });
      return handleResponse(res, HealthResponseSchema);
    },

    ready: async (): Promise<{ status: string }> => {
      const res = await fetchWithTimeout(`${API_URL}/ready`, {
        headers: { 'Content-Type': 'application/json' },
      });
      return handleResponse(res, z.object({ status: z.string() }));
    },
  },

  // Asset Library endpoints
  assets: {
    getList: async (filters?: AssetFilters): Promise<AssetListResponse> => {
      const params = new URLSearchParams();
      if (filters?.collection) params.set('collection', filters.collection);
      if (filters?.type) params.set('type', filters.type);
      if (filters?.search) params.set('search', filters.search);
      if (filters?.page) params.set('page', String(filters.page));
      if (filters?.limit) params.set('limit', String(Math.min(filters.limit, 100)));

      const res = await fetchWithTimeout(
        `${API_URL}/api/v1/assets?${params.toString()}`,
        { headers: await getAuthHeaders() }
      );
      return handleResponse(res, AssetListResponseSchema);
    },

    get: async (id: string): Promise<Asset> => {
      if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
        throw new ApiError('Invalid asset ID format', 400, 'INVALID_INPUT');
      }
      const res = await fetchWithTimeout(`${API_URL}/api/v1/assets/${id}`, {
        headers: await getAuthHeaders(),
      });
      return handleResponse(res, AssetSchema);
    },

    update: async (id: string, data: AssetUpdateRequest): Promise<Asset> => {
      if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
        throw new ApiError('Invalid asset ID format', 400, 'INVALID_INPUT');
      }
      const res = await fetchWithTimeout(`${API_URL}/api/v1/assets/${id}`, {
        method: 'PATCH',
        headers: await getAuthHeaders(),
        body: JSON.stringify(data),
      });
      return handleResponse(res, AssetSchema);
    },

    delete: async (id: string): Promise<void> => {
      if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
        throw new ApiError('Invalid asset ID format', 400, 'INVALID_INPUT');
      }
      const res = await fetchWithTimeout(`${API_URL}/api/v1/assets/${id}`, {
        method: 'DELETE',
        headers: await getAuthHeaders(),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw ApiError.fromResponse(res.status, body);
      }
    },

    upload: async (file: File, collection: string): Promise<Asset> => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('collection', collection);

      const token = getAuthToken();
      const headers: HeadersInit = {
        'X-Request-ID': crypto.randomUUID(),
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetchWithTimeout(`${API_URL}/api/v1/assets/upload`, {
        method: 'POST',
        headers,
        body: formData,
      }, 120000); // 2 minute timeout for uploads
      return handleResponse(res, AssetSchema);
    },

    getCollectionStats: async (): Promise<Record<string, number>> => {
      const res = await fetchWithTimeout(`${API_URL}/api/v1/assets/stats/collections`, {
        headers: await getAuthHeaders(),
      });
      const data = await res.json();
      return data as Record<string, number>;
    },
  },

  // QA Review endpoints
  qa: {
    getReviews: async (status?: string): Promise<QAReviewListResponse> => {
      const params = status ? `?status=${status}` : '';
      const res = await fetchWithTimeout(
        `${API_URL}/api/v1/qa/reviews${params}`,
        { headers: await getAuthHeaders() }
      );
      return handleResponse(res, QAReviewListResponseSchema);
    },

    getReview: async (id: string): Promise<QAReview> => {
      if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
        throw new ApiError('Invalid review ID format', 400, 'INVALID_INPUT');
      }
      const res = await fetchWithTimeout(`${API_URL}/api/v1/qa/reviews/${id}`, {
        headers: await getAuthHeaders(),
      });
      return handleResponse(res, QAReviewSchema);
    },

    submitReview: async (id: string, data: QAReviewRequest): Promise<QAReview> => {
      if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
        throw new ApiError('Invalid review ID format', 400, 'INVALID_INPUT');
      }
      const res = await fetchWithTimeout(`${API_URL}/api/v1/qa/reviews/${id}`, {
        method: 'PATCH',
        headers: await getAuthHeaders(),
        body: JSON.stringify(data),
      });
      return handleResponse(res, QAReviewSchema);
    },

    regenerate: async (id: string, data?: RegenerateRequest): Promise<QAReview> => {
      if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
        throw new ApiError('Invalid review ID format', 400, 'INVALID_INPUT');
      }
      const res = await fetchWithTimeout(`${API_URL}/api/v1/qa/reviews/${id}/regenerate`, {
        method: 'POST',
        headers: await getAuthHeaders(),
        body: JSON.stringify(data || {}),
      });
      return handleResponse(res, QAReviewSchema);
    },
  },

  // Batch Generation endpoints
  batch: {
    start: async (data: BatchGenerationRequest): Promise<BatchJob> => {
      if (!data.asset_ids?.length) {
        throw new ApiError('At least one asset ID is required', 400, 'INVALID_INPUT');
      }
      if (data.asset_ids.length > 500) {
        throw new ApiError('Maximum 500 assets per batch', 400, 'INVALID_INPUT');
      }
      const res = await fetchWithTimeout(`${API_URL}/api/v1/batch/generate`, {
        method: 'POST',
        headers: await getAuthHeaders(),
        body: JSON.stringify(data),
      });
      return handleResponse(res, BatchJobSchema);
    },

    getStatus: async (id: string): Promise<BatchJob> => {
      if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
        throw new ApiError('Invalid batch ID format', 400, 'INVALID_INPUT');
      }
      const res = await fetchWithTimeout(`${API_URL}/api/v1/batch/${id}`, {
        headers: await getAuthHeaders(),
      });
      return handleResponse(res, BatchJobSchema);
    },

    pause: async (id: string): Promise<BatchJob> => {
      if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
        throw new ApiError('Invalid batch ID format', 400, 'INVALID_INPUT');
      }
      const res = await fetchWithTimeout(`${API_URL}/api/v1/batch/${id}/pause`, {
        method: 'POST',
        headers: await getAuthHeaders(),
      });
      return handleResponse(res, BatchJobSchema);
    },

    resume: async (id: string): Promise<BatchJob> => {
      if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
        throw new ApiError('Invalid batch ID format', 400, 'INVALID_INPUT');
      }
      const res = await fetchWithTimeout(`${API_URL}/api/v1/batch/${id}/resume`, {
        method: 'POST',
        headers: await getAuthHeaders(),
      });
      return handleResponse(res, BatchJobSchema);
    },

    cancel: async (id: string): Promise<BatchJob> => {
      if (!id || !/^[a-zA-Z0-9_-]+$/.test(id)) {
        throw new ApiError('Invalid batch ID format', 400, 'INVALID_INPUT');
      }
      const res = await fetchWithTimeout(`${API_URL}/api/v1/batch/${id}/cancel`, {
        method: 'POST',
        headers: await getAuthHeaders(),
      });
      return handleResponse(res, BatchJobSchema);
    },

    list: async (): Promise<BatchJob[]> => {
      const res = await fetchWithTimeout(`${API_URL}/api/v1/batch`, {
        headers: await getAuthHeaders(),
      });
      return handleArrayResponse(res, BatchJobSchema);
    },
  },
};

// =============================================================================
// UTILITY EXPORTS
// =============================================================================

export { API_URL };
