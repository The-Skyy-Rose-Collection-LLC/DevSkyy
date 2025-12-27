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

// Agent APIs - using /v1/ prefix for versioned API
export const agentsAPI = {
  list: () => fetchAPI<AgentInfo[]>('/v1/agents'),

  get: (type: SuperAgentType) => fetchAPI<AgentInfo>(`/v1/agents/${type}`),

  getStats: (type: SuperAgentType) =>
    fetchAPI<AgentInfo['stats']>(`/v1/agents/${type}/stats`),

  getTools: (type: SuperAgentType) =>
    fetchAPI<ToolInfo[]>(`/v1/agents/${type}/tools`),

  start: (type: SuperAgentType) =>
    fetchAPI<{ success: boolean; message: string }>(`/v1/agents/${type}/start`, { method: 'POST' }),

  stop: (type: SuperAgentType) =>
    fetchAPI<{ success: boolean; message: string }>(`/v1/agents/${type}/stop`, { method: 'POST' }),

  triggerLearning: (type: SuperAgentType) =>
    fetchAPI<{ success: boolean }>(`/v1/agents/${type}/learn`, { method: 'POST' }),
};

// Task APIs
export const tasksAPI = {
  submit: (request: TaskRequest) =>
    fetchAPI<TaskResponse>('/v1/tasks', {
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

  getLatest: () => fetchAPI<RoundTableEntry>('/v1/round-table/latest'),

  getProviders: () => fetchAPI<LLMProviderInfo[]>('/v1/round-table/providers'),

  runCompetition: (prompt: string, taskType?: string) =>
    fetchAPI<RoundTableEntry>('/v1/round-table/compete', {
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
    }>('/v1/ab-testing/stats'),
};

// Visual Generation APIs
export const visualAPI = {
  generate: (request: VisualGenerationRequest) =>
    fetchAPI<VisualGenerationResult>('/v1/visual/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  getProviders: () =>
    fetchAPI<
      Array<{
        provider: string;
        name: string;
        types: string[];
        status: string;
      }>
    >('/v1/visual/providers'),

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

// 3D Pipeline APIs
export const threeDAPI = {
  getStatus: () => fetchAPI<{
    status: string;
    models: string[];
    queueLength: number;
    processingTime: number;
    lastGenerated: string;
  }>('/v1/3d/status'),

  generate: (request: { prompt: string; model?: string }) =>
    fetchAPI<{ jobId: string; status: string }>('/v1/3d/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    }),
};

// Metrics APIs
export const metricsAPI = {
  getDashboard: () => fetchAPI<DashboardMetrics>('/v1/metrics/dashboard'),

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
  list: () => fetchAPI<ToolInfo[]>('/v1/tools'),

  getByCategory: (category: string) =>
    fetchAPI<ToolInfo[]>(`/v1/tools/category/${category}`),

  test: (toolName: string, parameters: Record<string, unknown>) =>
    fetchAPI<{ result: unknown; error?: string }>('/v1/tools/test', {
      method: 'POST',
      body: JSON.stringify({ tool_name: toolName, parameters }),
    }),
};

// Brand API
export const brandAPI = {
  get: () =>
    fetchAPI<{
      brand: {
        name: string;
        tagline: string;
        philosophy: string;
        location: string;
        tone: { primary: string; descriptors: string[]; avoid: string[] };
        colors: Record<string, { name: string; hex: string; rgb: string }>;
        typography: { heading: string; body: string; accent: string };
        target_audience: {
          age_range: string;
          description: string;
          interests: string[];
          values: string[];
        };
        product_types: string[];
        quality_descriptors: string[];
      };
      collections: Record<
        string,
        {
          name: string;
          tagline: string;
          mood: string;
          colors: string;
          style: string;
          description: string;
        }
      >;
    }>('/brand'),
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
};

export default api;
export { APIError };
