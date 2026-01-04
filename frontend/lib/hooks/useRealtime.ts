/**
 * React hooks for WebSocket real-time updates.
 *
 * These hooks replace SWR polling with WebSocket-based real-time updates,
 * achieving <100ms latency vs 2-30s with HTTP polling.
 *
 * Available hooks:
 * - useRealtimeAgents: Agent status and execution updates
 * - useRealtimeRoundTable: Round Table competition progress
 * - useRealtimeTasks: Task execution status
 * - useRealtime3DPipeline: 3D asset generation progress
 * - useRealtimeMetrics: System performance metrics
 * - useConnectionState: WebSocket connection state tracking
 *
 * Usage:
 *   const { agents, isConnected } = useRealtimeAgents();
 *   const { competition, loading } = useRealtimeRoundTable();
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  agentsClient,
  roundTableClient,
  tasksClient,
  pipelineClient,
  metricsClient,
  RealtimeClient,
  ConnectionState,
  type WebSocketMessage,
} from '../websocket';

// =============================================================================
// Type Definitions
// =============================================================================

import type { AgentInfo, RoundTableEntry } from '../types';

export type Agent = AgentInfo;
export type RoundTableCompetition = RoundTableEntry;

export interface Task {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number;
  message?: string;
  result?: any;
  error?: string;
  [key: string]: any;
}

export interface Pipeline3D {
  id: string;
  stage: 'generating' | 'validating' | 'uploading' | 'completed' | 'failed';
  progress?: number;
  asset_url?: string;
  validation_results?: any;
  [key: string]: any;
}

export interface SystemMetrics {
  timestamp: string;
  cpu_usage?: number;
  memory_usage?: number;
  active_agents?: number;
  active_competitions?: number;
  [key: string]: any;
}

// =============================================================================
// useConnectionState - Track WebSocket connection state
// =============================================================================

export function useConnectionState(client: RealtimeClient) {
  const [state, setState] = useState<ConnectionState>(client.getState());

  useEffect(() => {
    const handleStateChange = (newState: ConnectionState) => {
      setState(newState);
    };

    client.onStateChange(handleStateChange);

    return () => {
      client.offStateChange(handleStateChange);
    };
  }, [client]);

  return {
    state,
    isConnected: state === ConnectionState.CONNECTED,
    isConnecting: state === ConnectionState.CONNECTING || state === ConnectionState.RECONNECTING,
    isFailed: state === ConnectionState.FAILED,
  };
}

// =============================================================================
// useRealtimeAgents - Agent status updates
// =============================================================================

export interface UseRealtimeAgentsResult {
  agents: Agent[];
  isConnected: boolean;
  error: string | null;
  refresh: () => void;
}

export function useRealtimeAgents(): UseRealtimeAgentsResult {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const { isConnected } = useConnectionState(agentsClient);

  useEffect(() => {
    const handleAgentUpdate = (message: WebSocketMessage) => {
      const { agent_id, status, data } = message;

      setAgents(prev => {
        const index = prev.findIndex(a => a.id === agent_id);

        if (index >= 0) {
          // Update existing agent
          const updated = [...prev];
          updated[index] = {
            ...updated[index],
            status,
            ...data,
            last_updated: message.timestamp,
          };
          return updated;
        } else {
          // Add new agent
          return [
            ...prev,
            {
              id: agent_id,
              status,
              ...data,
              last_updated: message.timestamp,
            },
          ];
        }
      });
    };

    const handleError = (message: WebSocketMessage) => {
      setError(message.message || 'Unknown error');
    };

    agentsClient.on('agent_status_update', handleAgentUpdate);
    agentsClient.on('error', handleError);

    return () => {
      agentsClient.off('agent_status_update', handleAgentUpdate);
      agentsClient.off('error', handleError);
    };
  }, []);

  const refresh = useCallback(() => {
    // Request full agent list from server
    agentsClient.send({ type: 'get_agents' });
  }, []);

  return { agents, isConnected, error, refresh };
}

// =============================================================================
// useRealtimeRoundTable - Round Table competition updates
// =============================================================================

export interface UseRealtimeRoundTableResult {
  competition: RoundTableCompetition | null;
  history: RoundTableCompetition[];
  isConnected: boolean;
  error: string | null;
}

export function useRealtimeRoundTable(): UseRealtimeRoundTableResult {
  const [competition, setCompetition] = useState<RoundTableCompetition | null>(null);
  const [history, setHistory] = useState<RoundTableCompetition[]>([]);
  const [error, setError] = useState<string | null>(null);
  const { isConnected } = useConnectionState(roundTableClient);

  useEffect(() => {
    const handleCompetitionUpdate = (message: WebSocketMessage) => {
      const { competition_id, stage, data } = message;

      const updated: RoundTableCompetition = {
        id: competition_id,
        stage,
        ...data,
        last_updated: message.timestamp,
      };

      setCompetition(updated);

      // Add to history if completed
      if (stage === 'completed' || stage === 'failed') {
        setHistory(prev => [updated, ...prev].slice(0, 50)); // Keep last 50
      }
    };

    const handleError = (message: WebSocketMessage) => {
      setError(message.message || 'Unknown error');
    };

    roundTableClient.on('competition_update', handleCompetitionUpdate);
    roundTableClient.on('error', handleError);

    return () => {
      roundTableClient.off('competition_update', handleCompetitionUpdate);
      roundTableClient.off('error', handleError);
    };
  }, []);

  return { competition, history, isConnected, error };
}

// =============================================================================
// useRealtimeTasks - Task execution updates
// =============================================================================

export interface UseRealtimeTasksResult {
  tasks: Task[];
  isConnected: boolean;
  error: string | null;
}

export function useRealtimeTasks(): UseRealtimeTasksResult {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState<string | null>(null);
  const { isConnected } = useConnectionState(tasksClient);

  useEffect(() => {
    const handleTaskUpdate = (message: WebSocketMessage) => {
      const { task_id, status, progress, data } = message;

      setTasks(prev => {
        const index = prev.findIndex(t => t.id === task_id);

        if (index >= 0) {
          // Update existing task
          const updated = [...prev];
          updated[index] = {
            ...updated[index],
            status,
            progress,
            ...data,
            last_updated: message.timestamp,
          };
          return updated;
        } else {
          // Add new task
          return [
            ...prev,
            {
              id: task_id,
              status,
              progress,
              ...data,
              last_updated: message.timestamp,
            },
          ];
        }
      });
    };

    const handleError = (message: WebSocketMessage) => {
      setError(message.message || 'Unknown error');
    };

    tasksClient.on('task_update', handleTaskUpdate);
    tasksClient.on('error', handleError);

    return () => {
      tasksClient.off('task_update', handleTaskUpdate);
      tasksClient.off('error', handleError);
    };
  }, []);

  return { tasks, isConnected, error };
}

// =============================================================================
// useRealtime3DPipeline - 3D asset generation progress
// =============================================================================

export interface UseRealtime3DPipelineResult {
  pipelines: Pipeline3D[];
  isConnected: boolean;
  error: string | null;
}

export function useRealtime3DPipeline(): UseRealtime3DPipelineResult {
  const [pipelines, setPipelines] = useState<Pipeline3D[]>([]);
  const [error, setError] = useState<string | null>(null);
  const { isConnected } = useConnectionState(pipelineClient);

  useEffect(() => {
    const handlePipelineUpdate = (message: WebSocketMessage) => {
      const { pipeline_id, stage, progress, data } = message;

      setPipelines(prev => {
        const index = prev.findIndex(p => p.id === pipeline_id);

        if (index >= 0) {
          // Update existing pipeline
          const updated = [...prev];
          updated[index] = {
            ...updated[index],
            stage,
            progress,
            ...data,
            last_updated: message.timestamp,
          };
          return updated;
        } else {
          // Add new pipeline
          return [
            ...prev,
            {
              id: pipeline_id,
              stage,
              progress,
              ...data,
              last_updated: message.timestamp,
            },
          ];
        }
      });
    };

    const handleError = (message: WebSocketMessage) => {
      setError(message.message || 'Unknown error');
    };

    pipelineClient.on('pipeline_update', handlePipelineUpdate);
    pipelineClient.on('error', handleError);

    return () => {
      pipelineClient.off('pipeline_update', handlePipelineUpdate);
      pipelineClient.off('error', handleError);
    };
  }, []);

  return { pipelines, isConnected, error };
}

// =============================================================================
// useRealtimeMetrics - System performance metrics
// =============================================================================

export interface UseRealtimeMetricsResult {
  metrics: SystemMetrics | null;
  history: SystemMetrics[];
  isConnected: boolean;
  error: string | null;
}

export function useRealtimeMetrics(historySize: number = 100): UseRealtimeMetricsResult {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [history, setHistory] = useState<SystemMetrics[]>([]);
  const [error, setError] = useState<string | null>(null);
  const { isConnected } = useConnectionState(metricsClient);

  useEffect(() => {
    const handleMetricsUpdate = (message: WebSocketMessage) => {
      const metricsData: SystemMetrics = {
        timestamp: message.timestamp,
        ...message.metrics,
      };

      setMetrics(metricsData);

      // Add to history
      setHistory(prev => [metricsData, ...prev].slice(0, historySize));
    };

    const handleError = (message: WebSocketMessage) => {
      setError(message.message || 'Unknown error');
    };

    metricsClient.on('metrics_update', handleMetricsUpdate);
    metricsClient.on('error', handleError);

    return () => {
      metricsClient.off('metrics_update', handleMetricsUpdate);
      metricsClient.off('error', handleError);
    };
  }, [historySize]);

  return { metrics, history, isConnected, error };
}

// =============================================================================
// useWebSocketPing - Send periodic pings to keep connection alive
// =============================================================================

export function useWebSocketPing(client: RealtimeClient, intervalMs: number = 30000) {
  useEffect(() => {
    const interval = setInterval(() => {
      if (client.isConnected()) {
        client.send({ type: 'ping' });
      }
    }, intervalMs);

    return () => {
      clearInterval(interval);
    };
  }, [client, intervalMs]);
}
