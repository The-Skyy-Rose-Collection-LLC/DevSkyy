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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/backend';

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
      error.message || `API request failed: ${response.statusText}`,
      response.status,
      error.code
    );
  }

  return response.json();
}

// Agent APIs
export const agentsAPI = {
  list: () => fetchAPI<AgentInfo[]>('/agents'),

  get: (type: SuperAgentType) => fetchAPI<AgentInfo>(`/agents/${type}`),

  getStats: (type: SuperAgentType) =>
    fetchAPI<AgentInfo['stats']>(`/agents/${type}/stats`),

  getTools: (type: SuperAgentType) =>
    fetchAPI<ToolInfo[]>(`/agents/${type}/tools`),

  start: (type: SuperAgentType) =>
    fetchAPI<{ success: boolean }>(`/agents/${type}/start`, { method: 'POST' }),

  stop: (type: SuperAgentType) =>
    fetchAPI<{ success: boolean }>(`/agents/${type}/stop`, { method: 'POST' }),

  triggerLearning: (type: SuperAgentType) =>
    fetchAPI<{ success: boolean }>(`/agents/${type}/learn`, { method: 'POST' }),
};

// Task APIs
export const tasksAPI = {
  submit: (request: TaskRequest) =>
    fetchAPI<TaskResponse>('/tasks', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  get: (taskId: string) => fetchAPI<TaskResponse>(`/tasks/${taskId}`),

  list: (params?: { agentType?: SuperAgentType; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.agentType) searchParams.set('agent_type', params.agentType);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    const query = searchParams.toString();
    return fetchAPI<TaskResponse[]>(`/tasks${query ? `?${query}` : ''}`);
  },

  cancel: (taskId: string) =>
    fetchAPI<{ success: boolean }>(`/tasks/${taskId}/cancel`, {
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
      `/round-table${query ? `?${query}` : ''}`
    );
  },

  get: (id: string) => fetchAPI<RoundTableEntry>(`/round-table/${id}`),

  getLatest: () => fetchAPI<RoundTableEntry>('/round-table/latest'),

  getProviders: () => fetchAPI<LLMProviderInfo[]>('/round-table/providers'),

  runCompetition: (prompt: string, taskType?: string) =>
    fetchAPI<RoundTableEntry>('/round-table/compete', {
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
      `/ab-testing${query ? `?${query}` : ''}`
    );
  },

  get: (testId: string) => fetchAPI<ABTestHistoryEntry>(`/ab-testing/${testId}`),

  getStats: () =>
    fetchAPI<{
      totalTests: number;
      avgConfidence: number;
      winsByProvider: Record<string, number>;
    }>('/ab-testing/stats'),
};

// Visual Generation APIs
export const visualAPI = {
  generate: (request: VisualGenerationRequest) =>
    fetchAPI<VisualGenerationResult>('/visual/generate', {
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
    >('/visual/providers'),

  getHistory: (params?: { limit?: number; type?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.type) searchParams.set('type', params.type);
    const query = searchParams.toString();
    return fetchAPI<VisualGenerationResult[]>(
      `/visual/history${query ? `?${query}` : ''}`
    );
  },
};

// Metrics APIs
export const metricsAPI = {
  getDashboard: () => fetchAPI<DashboardMetrics>('/metrics/dashboard'),

  getTimeSeries: (params?: { range?: '1h' | '24h' | '7d' | '30d' }) => {
    const searchParams = new URLSearchParams();
    if (params?.range) searchParams.set('range', params.range);
    const query = searchParams.toString();
    return fetchAPI<MetricsTimeSeries>(
      `/metrics/timeseries${query ? `?${query}` : ''}`
    );
  },

  getAgentMetrics: (agentType: SuperAgentType) =>
    fetchAPI<{
      tasksByCategory: Record<string, number>;
      successByCategory: Record<string, number>;
      avgLatencyByCategory: Record<string, number>;
    }>(`/metrics/agents/${agentType}`),
};

// Tools API
export const toolsAPI = {
  list: () => fetchAPI<ToolInfo[]>('/tools'),

  getByCategory: (category: string) =>
    fetchAPI<ToolInfo[]>(`/tools/category/${category}`),

  test: (toolName: string, parameters: Record<string, unknown>) =>
    fetchAPI<{ result: unknown; error?: string }>('/tools/test', {
      method: 'POST',
      body: JSON.stringify({ tool_name: toolName, parameters }),
    }),
};

// Export all APIs
export const api = {
  agents: agentsAPI,
  tasks: tasksAPI,
  roundTable: roundTableAPI,
  abTesting: abTestingAPI,
  visual: visualAPI,
  metrics: metricsAPI,
  tools: toolsAPI,
};

export default api;
export { APIError };
