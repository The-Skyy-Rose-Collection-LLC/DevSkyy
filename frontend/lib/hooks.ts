/**
 * DevSkyy Dashboard Hooks
 * =======================
 * Custom React hooks for data fetching and state management.
 */

'use client';

import useSWR, { type SWRConfiguration } from 'swr';
import useSWRMutation from 'swr/mutation';
import { api } from './api';
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

// Default SWR config
const defaultConfig: SWRConfiguration = {
  revalidateOnFocus: false,
  dedupingInterval: 5000,
};

// Agent Hooks
export function useAgents(config?: SWRConfiguration) {
  return useSWR<AgentInfo[]>('agents', () => api.agents.list(), {
    ...defaultConfig,
    ...config,
  });
}

export function useAgent(type: SuperAgentType, config?: SWRConfiguration) {
  return useSWR<AgentInfo>(
    type ? `agents/${type}` : null,
    () => api.agents.get(type),
    {
      ...defaultConfig,
      ...config,
    }
  );
}

export function useAgentTools(type: SuperAgentType, config?: SWRConfiguration) {
  return useSWR<ToolInfo[]>(
    type ? `agents/${type}/tools` : null,
    () => api.agents.getTools(type),
    {
      ...defaultConfig,
      ...config,
    }
  );
}

export function useAgentControl(type: SuperAgentType) {
  const startMutation = useSWRMutation(
    `agents/${type}/start`,
    () => api.agents.start(type)
  );

  const stopMutation = useSWRMutation(
    `agents/${type}/stop`,
    () => api.agents.stop(type)
  );

  const learnMutation = useSWRMutation(
    `agents/${type}/learn`,
    () => api.agents.triggerLearning(type)
  );

  return {
    start: startMutation.trigger,
    stop: stopMutation.trigger,
    triggerLearning: learnMutation.trigger,
    isStarting: startMutation.isMutating,
    isStopping: stopMutation.isMutating,
    isLearning: learnMutation.isMutating,
  };
}

// Task Hooks
export function useTasks(
  params?: { agentType?: SuperAgentType; limit?: number },
  config?: SWRConfiguration
) {
  const key = params
    ? `tasks?${new URLSearchParams(
        Object.entries(params)
          .filter(([, v]) => v !== undefined)
          .map(([k, v]) => [k, String(v)])
      ).toString()}`
    : 'tasks';

  return useSWR<TaskResponse[]>(key, () => api.tasks.list(params), {
    ...defaultConfig,
    refreshInterval: 5000, // Poll for task updates
    ...config,
  });
}

export function useTask(taskId: string | null, config?: SWRConfiguration) {
  return useSWR<TaskResponse>(
    taskId ? `tasks/${taskId}` : null,
    () => api.tasks.get(taskId!),
    {
      ...defaultConfig,
      refreshInterval: 2000, // Poll more frequently for individual task
      ...config,
    }
  );
}

export function useSubmitTask() {
  return useSWRMutation<TaskResponse, Error, string, TaskRequest>(
    'tasks/submit',
    (_key, { arg }) => api.tasks.submit(arg)
  );
}

// Round Table Hooks
export function useRoundTableHistory(
  params?: { limit?: number; status?: string },
  config?: SWRConfiguration
) {
  const key = params
    ? `round-table?${new URLSearchParams(
        Object.entries(params)
          .filter(([, v]) => v !== undefined)
          .map(([k, v]) => [k, String(v)])
      ).toString()}`
    : 'round-table';

  return useSWR<RoundTableEntry[]>(key, () => api.roundTable.list(params), {
    ...defaultConfig,
    ...config,
  });
}

export function useRoundTableEntry(id: string | null, config?: SWRConfiguration) {
  return useSWR<RoundTableEntry>(
    id ? `round-table/${id}` : null,
    () => api.roundTable.get(id!),
    {
      ...defaultConfig,
      ...config,
    }
  );
}

export function useLatestRoundTable(config?: SWRConfiguration) {
  return useSWR<RoundTableEntry>('round-table/latest', () => api.roundTable.getLatest(), {
    ...defaultConfig,
    refreshInterval: 3000,
    ...config,
  });
}

export function useLLMProviders(config?: SWRConfiguration) {
  return useSWR<LLMProviderInfo[]>(
    'round-table/providers',
    () => api.roundTable.getProviders(),
    {
      ...defaultConfig,
      ...config,
    }
  );
}

export function useRunCompetition() {
  return useSWRMutation<
    RoundTableEntry,
    Error,
    string,
    { prompt: string; taskType?: string }
  >('round-table/compete', (_key, { arg }) =>
    api.roundTable.runCompetition(arg.prompt, arg.taskType)
  );
}

// A/B Testing Hooks
export function useABTestHistory(
  params?: { limit?: number },
  config?: SWRConfiguration
) {
  return useSWR<ABTestHistoryEntry[]>(
    'ab-testing',
    () => api.abTesting.list(params),
    {
      ...defaultConfig,
      ...config,
    }
  );
}

export function useABTestStats(config?: SWRConfiguration) {
  return useSWR(
    'ab-testing/stats',
    () => api.abTesting.getStats(),
    {
      ...defaultConfig,
      ...config,
    }
  );
}

// Visual Generation Hooks
export function useVisualHistory(
  params?: { limit?: number; type?: string },
  config?: SWRConfiguration
) {
  return useSWR<VisualGenerationResult[]>(
    'visual/history',
    () => api.visual.getHistory(params),
    {
      ...defaultConfig,
      ...config,
    }
  );
}

export function useVisualProviders(config?: SWRConfiguration) {
  return useSWR('visual/providers', () => api.visual.getProviders(), {
    ...defaultConfig,
    ...config,
  });
}

export function useGenerateVisual() {
  return useSWRMutation<
    VisualGenerationResult,
    Error,
    string,
    VisualGenerationRequest
  >('visual/generate', (_key, { arg }) => api.visual.generate(arg));
}

// Metrics Hooks
export function useDashboardMetrics(config?: SWRConfiguration) {
  return useSWR<DashboardMetrics>(
    'metrics/dashboard',
    () => api.metrics.getDashboard(),
    {
      ...defaultConfig,
      refreshInterval: 30000, // Refresh every 30 seconds
      ...config,
    }
  );
}

export function useMetricsTimeSeries(
  range?: '1h' | '24h' | '7d' | '30d',
  config?: SWRConfiguration
) {
  return useSWR<MetricsTimeSeries>(
    `metrics/timeseries?range=${range || '24h'}`,
    () => api.metrics.getTimeSeries({ range }),
    {
      ...defaultConfig,
      refreshInterval: 60000,
      ...config,
    }
  );
}

export function useAgentMetrics(type: SuperAgentType, config?: SWRConfiguration) {
  return useSWR(
    type ? `metrics/agents/${type}` : null,
    () => api.metrics.getAgentMetrics(type),
    {
      ...defaultConfig,
      ...config,
    }
  );
}

// Tools Hooks
export function useTools(config?: SWRConfiguration) {
  return useSWR<ToolInfo[]>('tools', () => api.tools.list(), {
    ...defaultConfig,
    ...config,
  });
}

export function useToolsByCategory(category: string, config?: SWRConfiguration) {
  return useSWR<ToolInfo[]>(
    category ? `tools/category/${category}` : null,
    () => api.tools.getByCategory(category),
    {
      ...defaultConfig,
      ...config,
    }
  );
}

export function useTestTool() {
  return useSWRMutation<
    { result: unknown; error?: string },
    Error,
    string,
    { toolName: string; parameters: Record<string, unknown> }
  >('tools/test', (_key, { arg }) =>
    api.tools.test(arg.toolName, arg.parameters)
  );
}
