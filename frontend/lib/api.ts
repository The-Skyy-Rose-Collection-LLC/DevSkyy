/**
 * DevSkyy API Client
 * ==================
 * Client library for communicating with the Python backend.
 */

import type {
  ABTestHistoryEntry,
  AgentInfo,
  DashboardMetrics,
  LLMProviderInfo,
  MetricsTimeSeries,
  RoundTableEntry,
  SuperAgentType,
  TaskRequest,
  TaskResponse,
  ToolInfo,
  VisualGenerationRequest,
  VisualGenerationResult,
} from './types';

// Use /api which maps to Python serverless functions
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new APIError(
        error.detail || error.message || `API request failed: ${response.statusText}`,
        response.status,
        error.code
      );
    }

    return response.json();
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(
      error instanceof Error ? error.message : 'Network error',
      0,
      'NETWORK_ERROR'
    );
  }
}

// Agent APIs - using /api/v1/ prefix for versioned API
export const agentsAPI = {
  list: () => fetchAPI<AgentInfo[]>('/api/v1/agents'),

  get: (type: SuperAgentType) => fetchAPI<AgentInfo>(`/api/v1/agents/${type}`),

  getStats: (type: SuperAgentType) =>
    fetchAPI<AgentInfo['stats']>(`/api/v1/agents/${type}/stats`),

  getTools: (type: SuperAgentType) =>
    fetchAPI<ToolInfo[]>(`/api/v1/agents/${type}/tools`),

  start: (type: SuperAgentType) =>
    fetchAPI<{ success: boolean; message: string }>(`/api/v1/agents/${type}/start`, { method: 'POST' }),

  stop: (type: SuperAgentType) =>
    fetchAPI<{ success: boolean; message: string }>(`/api/v1/agents/${type}/stop`, { method: 'POST' }),

  triggerLearning: (type: SuperAgentType) =>
    fetchAPI<{ success: boolean }>(`/api/v1/agents/${type}/learn`, { method: 'POST' }),

  chat: async (type: SuperAgentType, message: string, stream = true) => {
    const url = `${API_BASE}/api/v1/agents/chat`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent_type: type, message, stream }),
    });

    if (!response.ok) {
      throw new APIError(
        `Chat request failed: ${response.statusText}`,
        response.status
      );
    }

    return response;
  },
};

// Task APIs
export const tasksAPI = {
  submit: (request: TaskRequest) =>
    fetchAPI<TaskResponse>('/api/v1/tasks', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  get: (taskId: string) => fetchAPI<TaskResponse>(`/v1/tasks/${taskId}`),

  list: (params?: { agentType?: SuperAgentType; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.agentType) searchParams.set('agent_type', params.agentType);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    const query = searchParams.toString();
    return fetchAPI<TaskResponse[]>(`/v1/tasks${query ? `?${query}` : ''}`);
  },

  cancel: (taskId: string) =>
    fetchAPI<{ success: boolean }>(`/v1/tasks/${taskId}/cancel`, {
      method: 'POST',
    }),
};

// Round Table APIs
export const roundTableAPI = {
  list: (params?: { limit?: number; status?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.status) searchParams.set('status', params.status);
    const query = searchParams.toString();
    return fetchAPI<RoundTableEntry[]>(
      `/v1/round-table${query ? `?${query}` : ''}`
    );
  },

  get: (id: string) => fetchAPI<RoundTableEntry>(`/v1/round-table/${id}`),

  getLatest: () => fetchAPI<RoundTableEntry>('/api/v1/round-table/latest'),

  getProviders: () => fetchAPI<LLMProviderInfo[]>('/api/v1/round-table/providers'),

  runCompetition: (prompt: string, taskType?: string) =>
    fetchAPI<RoundTableEntry>('/api/v1/round-table/compete', {
      method: 'POST',
      body: JSON.stringify({ prompt, task_type: taskType }),
    }),
};

// A/B Testing APIs
export const abTestingAPI = {
  list: (params?: { limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    const query = searchParams.toString();
    return fetchAPI<ABTestHistoryEntry[]>(
      `/v1/ab-testing${query ? `?${query}` : ''}`
    );
  },

  get: (testId: string) => fetchAPI<ABTestHistoryEntry>(`/v1/ab-testing/${testId}`),

  getStats: () =>
    fetchAPI<{
      totalTests: number;
      avgConfidence: number;
      winsByProvider: Record<string, number>;
    }>('/api/v1/ab-testing/stats'),
};

// Visual Generation APIs
export const visualAPI = {
  generate: (request: VisualGenerationRequest) =>
    fetchAPI<VisualGenerationResult>('/api/v1/visual/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  getJobStatus: (jobId: string) =>
    fetchAPI<{
      job_id: string;
      status: 'pending' | 'processing' | 'completed' | 'failed';
      progress?: number;
      image_url?: string;
      error?: string;
    }>(`/api/v1/visual/jobs/${jobId}`),

  getProviders: () =>
    fetchAPI<
      Array<{
        provider: string;
        name: string;
        types: string[];
        status: string;
      }>
    >('/api/v1/visual/providers'),

  getHistory: (params?: { limit?: number; type?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.type) searchParams.set('type', params.type);
    const query = searchParams.toString();
    return fetchAPI<VisualGenerationResult[]>(
      `/v1/visual/history${query ? `?${query}` : ''}`
    );
  },
};

// 3D Pipeline Types
interface ThreeDProvider {
  id: string;
  name: string;
  description: string;
  supported_inputs: string[];
  avg_generation_time_s: number;
  cost_per_generation: number;
  available: boolean;
}

interface ThreeDJob {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  provider: string;
  prompt?: string;
  image_url?: string;
  progress: number;
  result_url?: string;
  error_message?: string;
  created_at: string;
  completed_at?: string;
  processing_time_s?: number;
}

interface ThreeDStatus {
  status: string;
  providers: string[];
  active_jobs: number;
  completed_today: number;
  avg_processing_time_s: number;
  queue_length: number;
}

// 3D Pipeline APIs - Real endpoints
export const threeDAPI = {
  // Get pipeline status
  getStatus: () => fetchAPI<ThreeDStatus>('/api/v1/3d/status'),

  // List available providers (TRELLIS, TRIPO)
  getProviders: () => fetchAPI<ThreeDProvider[]>('/api/v1/3d/providers'),

  // List generation jobs
  listJobs: (params?: { limit?: number; status?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.status) searchParams.set('status', params.status);
    const query = searchParams.toString();
    return fetchAPI<ThreeDJob[]>(`/v1/3d/jobs${query ? `?${query}` : ''}`);
  },

  // Get single job by ID
  getJob: (jobId: string) => fetchAPI<ThreeDJob>(`/v1/3d/jobs/${jobId}`),

  // Generate from text prompt (requires image_url for TRELLIS)
  generateFromText: (request: {
    prompt: string;
    provider?: 'trellis' | 'tripo';
    image_url?: string;
    options?: Record<string, unknown>;
  }) =>
    fetchAPI<ThreeDJob>('/api/v1/3d/generate/text', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  // Generate from image URL
  generateFromImage: (request: {
    image_url: string;
    provider?: 'trellis' | 'tripo';
    prompt?: string;
    options?: Record<string, unknown>;
  }) =>
    fetchAPI<ThreeDJob>('/api/v1/3d/generate/image', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  // Generate from file upload (FormData)
  generateFromUpload: async (
    file: File,
    provider: 'trellis' | 'tripo' = 'trellis',
    prompt?: string
  ): Promise<ThreeDJob> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('provider', provider);
    if (prompt) formData.append('prompt', prompt);

    const url = `${API_BASE}/v1/3d/generate/upload`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type - browser will set it with boundary for FormData
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new APIError(
        error.detail || 'Upload failed',
        response.status,
        error.code
      );
    }

    return response.json();
  },

  // Poll job until completion (utility)
  pollJob: async (
    jobId: string,
    onProgress?: (job: ThreeDJob) => void,
    intervalMs = 2000,
    maxAttempts = 60
  ): Promise<ThreeDJob> => {
    let attempts = 0;
    while (attempts < maxAttempts) {
      const job = await threeDAPI.getJob(jobId);
      if (onProgress) onProgress(job);

      if (job.status === 'completed' || job.status === 'failed') {
        return job;
      }

      await new Promise((resolve) => setTimeout(resolve, intervalMs));
      attempts++;
    }
    throw new Error('Job polling timeout');
  },
};

// Metrics APIs
export const metricsAPI = {
  getDashboard: () => fetchAPI<DashboardMetrics>('/api/v1/metrics/dashboard'),

  getTimeSeries: (params?: { range?: '1h' | '24h' | '7d' | '30d' }) => {
    const searchParams = new URLSearchParams();
    if (params?.range) searchParams.set('range', params.range);
    const query = searchParams.toString();
    return fetchAPI<MetricsTimeSeries>(
      `/v1/metrics/timeseries${query ? `?${query}` : ''}`
    );
  },

  getAgentMetrics: (agentType: SuperAgentType) =>
    fetchAPI<{
      tasksByCategory: Record<string, number>;
      successByCategory: Record<string, number>;
      avgLatencyByCategory: Record<string, number>;
    }>(`/v1/metrics/agents/${agentType}`),
};

// Tools API
export const toolsAPI = {
  list: () => fetchAPI<ToolInfo[]>('/api/v1/tools'),

  getByCategory: (category: string) =>
    fetchAPI<ToolInfo[]>(`/v1/tools/category/${category}`),

  test: (toolName: string, parameters: Record<string, unknown>) =>
    fetchAPI<{ result: unknown; error?: string }>('/api/v1/tools/test', {
      method: 'POST',
      body: JSON.stringify({ tool_name: toolName, parameters }),
    }),
};

// Brand API
export const brandAPI = {
  get: () =>
    fetchAPI<{
      name: string;
      tagline: string;
      philosophy: string;
      location: string;
      tone: { primary: string; descriptors: string[]; avoid: string[] };
      colors: {
        primary: { name: string; hex: string; rgb: string };
        accent: { name: string; hex: string; rgb: string };
        highlight: { name: string; hex: string; rgb: string };
        ivory: { name: string; hex: string; rgb: string };
        obsidian: { name: string; hex: string; rgb: string };
      };
      typography: { heading: string; body: string; accent: string };
      target_audience: {
        age_range: string;
        description: string;
        interests: string[];
        values: string[];
      };
      product_types: string[];
      quality_descriptors: string[];
      collections?: Array<{
        id: string;
        name: string;
        tagline: string;
        mood: string;
        colors: string;
        style: string;
        description: string;
      }>;
    }>('/api/v1/brand'),

  getSummary: () =>
    fetchAPI<{
      name: string;
      tagline: string;
      philosophy: string;
      primary_color: string;
      accent_color: string;
    }>('/api/v1/brand/summary'),

  getCollections: () =>
    fetchAPI<
      Array<{
        id: string;
        name: string;
        tagline: string;
        mood: string;
        colors: string;
        style: string;
        description: string;
      }>
    >('/api/v1/brand/collections'),

  getCollection: (id: string) =>
    fetchAPI<{
      id: string;
      name: string;
      tagline: string;
      mood: string;
      colors: string;
      style: string;
      description: string;
    }>(`/v1/brand/collections/${id}`),

  update: (data: {
    name?: string;
    tagline?: string;
    philosophy?: string;
    location?: string;
    tone?: { primary: string; descriptors: string[]; avoid: string[] };
    colors?: {
      primary: { name: string; hex: string; rgb: string };
      accent: { name: string; hex: string; rgb: string };
      highlight: { name: string; hex: string; rgb: string };
      ivory: { name: string; hex: string; rgb: string };
      obsidian: { name: string; hex: string; rgb: string };
    };
    typography?: { heading: string; body: string; accent: string };
    target_audience?: {
      age_range: string;
      description: string;
      interests: string[];
      values: string[];
    };
    product_types?: string[];
    quality_descriptors?: string[];
    collections?: Array<{
      id: string;
      name: string;
      tagline: string;
      mood: string;
      colors: string;
      style: string;
      description: string;
    }>;
  }) =>
    fetchAPI<{ success: boolean; message: string }>('/api/v1/brand', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
};

// Virtual Try-On API
export const virtualTryOnAPI = {
  generateModel: (params: {
    gender: string;
    ethnicity: string;
    age_range: string;
    body_type?: string;
  }) =>
    fetchAPI<{ job_id: string; status: string }>('/api/v1/virtual-tryon/generate-model', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  tryOn: (params: {
    model_url: string;
    garment_url: string;
    category?: string;
  }) =>
    fetchAPI<{ job_id: string; status: string }>('/api/v1/virtual-tryon/try-on', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  getJobStatus: (jobId: string) =>
    fetchAPI<{
      job_id: string;
      status: 'pending' | 'processing' | 'completed' | 'failed';
      result_url?: string;
      error?: string;
      progress?: number;
    }>(`/api/v1/virtual-tryon/jobs/${jobId}`),
};

// WordPress Types
interface WordPressPage {
  id: number;
  title: string;
  slug: string;
  status: string;
  link: string;
  modified: string;
  excerpt: string;
  content?: string;
  author?: number;
  created?: string;
}

interface WordPressStatus {
  connected: boolean;
  site_url: string;
  last_sync: string | null;
  pages_count: number;
  posts_count: number;
  media_count: number;
}

// WordPress API
export const wordpressAPI = {
  getStatus: () => fetchAPI<WordPressStatus>('/api/v1/wordpress/status'),

  listPages: (params?: { status?: string; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    const query = searchParams.toString();
    return fetchAPI<WordPressPage[]>(`/v1/wordpress/pages${query ? `?${query}` : ''}`);
  },

  getPage: (pageId: number) => fetchAPI<WordPressPage>(`/v1/wordpress/pages/${pageId}`),

  updatePage: (pageId: number, data: Partial<WordPressPage>) =>
    fetchAPI<WordPressPage>(`/v1/wordpress/pages/${pageId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  createPage: (data: { title: string; content: string; status?: string }) =>
    fetchAPI<WordPressPage>('/api/v1/wordpress/pages', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  deletePage: (pageId: number, force?: boolean) =>
    fetchAPI<{ success: boolean; message: string }>(
      `/v1/wordpress/pages/${pageId}${force ? '?force=true' : ''}`,
      { method: 'DELETE' }
    ),

  sync: () =>
    fetchAPI<{ status: string; message: string }>('/api/v1/wordpress/sync', {
      method: 'POST',
    }),
};

// Export all APIs
export const api = {
  agents: agentsAPI,
  tasks: tasksAPI,
  roundTable: roundTableAPI,
  abTesting: abTestingAPI,
  visual: visualAPI,
  threeD: threeDAPI,
  metrics: metricsAPI,
  tools: toolsAPI,
  brand: brandAPI,
  virtualTryOn: virtualTryOnAPI,
  wordpress: wordpressAPI,
};

export default api;
export { APIError };
