/**
 * useToastNotifications Hook
 * ===========================
 * Bridges WebSocket events to toast notifications for real-time user feedback.
 */

'use client';

import { useEffect, useRef } from 'react';
import { toast } from 'sonner';
import {
  agentsClient,
  roundTableClient,
  tasksClient,
  metricsClient,
  ConnectionState,
  type WebSocketMessage,
} from '../websocket';

interface ToastNotificationsOptions {
  showTaskToasts?: boolean;
  showAgentToasts?: boolean;
  showRoundTableToasts?: boolean;
  showConnectionToasts?: boolean;
  showErrorToasts?: boolean;
  debounceMs?: number;
}

class ToastDebouncer {
  private lastToastTime: Map<string, number> = new Map();
  canShow(key: string, debounceMs: number): boolean {
    const now = Date.now();
    const lastTime = this.lastToastTime.get(key) || 0;
    if (now - lastTime < debounceMs) return false;
    this.lastToastTime.set(key, now);
    return true;
  }
  clear(): void {
    this.lastToastTime.clear();
  }
}

export function useToastNotifications(options: ToastNotificationsOptions = {}): void {
  const {
    showTaskToasts = true,
    showAgentToasts = true,
    showRoundTableToasts = true,
    showConnectionToasts = true,
    showErrorToasts = true,
    debounceMs = 5000,
  } = options;

  const debouncerRef = useRef(new ToastDebouncer());

  useEffect(() => {
    if (!showTaskToasts) return;
    const handleTaskUpdate = (message: WebSocketMessage) => {
      const { task_id, status, data } = message;
      const debounceKey = `task-${task_id}-${status}`;
      if (!debouncerRef.current.canShow(debounceKey, debounceMs)) return;
      switch (status) {
        case 'completed':
          toast.success(`Task completed`, { description: data?.agent ? `Agent: ${data.agent}` : undefined, duration: 4000 });
          break;
        case 'failed':
          toast.error(`Task failed`, { description: data?.error || 'An error occurred', duration: 6000 });
          break;
      }
    };
    tasksClient.on('task_update', handleTaskUpdate);
    return () => tasksClient.off('task_update', handleTaskUpdate);
  }, [showTaskToasts, debounceMs]);

  useEffect(() => {
    if (!showAgentToasts) return;
    const handleAgentUpdate = (message: WebSocketMessage) => {
      const { agent_id, status, data } = message;
      const debounceKey = `agent-${agent_id}-${status}`;
      if (!debouncerRef.current.canShow(debounceKey, debounceMs)) return;
      switch (status) {
        case 'available':
          toast.success(`Agent ${data?.name || agent_id} is now available`, { duration: 3000 });
          break;
        case 'busy':
          if (data?.task_name) toast.info(`Agent ${data?.name || agent_id} started task`, { description: data.task_name, duration: 3000 });
          break;
        case 'error':
          toast.error(`Agent ${data?.name || agent_id} encountered an error`, { description: data?.error || 'Unknown error', duration: 5000 });
          break;
      }
    };
    agentsClient.on('agent_status_update', handleAgentUpdate);
    return () => agentsClient.off('agent_status_update', handleAgentUpdate);
  }, [showAgentToasts, debounceMs]);

  useEffect(() => {
    if (!showRoundTableToasts) return;
    const handleCompetitionUpdate = (message: WebSocketMessage) => {
      const { stage, data } = message;
      const debounceKey = `roundtable-${stage}`;
      if (!debouncerRef.current.canShow(debounceKey, debounceMs)) return;
      if (stage === 'completed' && data?.winner) {
        toast.success(`Round Table winner: ${data.winner}`, {
          description: data?.score ? `Score: ${data.score.toFixed(2)}` : undefined,
          duration: 5000,
        });
      } else if (stage === 'failed') {
        toast.error('Round Table competition failed', { description: data?.error || 'Unknown error', duration: 5000 });
      }
    };
    roundTableClient.on('competition_update', handleCompetitionUpdate);
    return () => roundTableClient.off('competition_update', handleCompetitionUpdate);
  }, [showRoundTableToasts, debounceMs]);

  useEffect(() => {
    if (!showConnectionToasts) return;
    let previousState: ConnectionState | null = null;
    const handleAgentsStateChange = (state: ConnectionState) => {
      const debounceKey = `connection-${state}`;
      if (!debouncerRef.current.canShow(debounceKey, debounceMs)) return;
      if (state === ConnectionState.CONNECTED && previousState === ConnectionState.RECONNECTING) {
        toast.success('Reconnected to server', { description: 'Real-time updates resumed', duration: 3000 });
      } else if (state === ConnectionState.DISCONNECTED && previousState === ConnectionState.CONNECTED) {
        toast.warning('Connection lost', { description: 'Attempting to reconnect...', duration: 4000 });
      } else if (state === ConnectionState.FAILED) {
        toast.error('Connection failed', { description: 'Unable to connect to server. Please refresh the page.', duration: 0 });
      }
      previousState = state;
    };
    agentsClient.onStateChange(handleAgentsStateChange);
    return () => agentsClient.offStateChange(handleAgentsStateChange);
  }, [showConnectionToasts, debounceMs]);

  useEffect(() => {
    if (!showErrorToasts) return;
    const handleError = (message: WebSocketMessage) => {
      const debounceKey = `error-${message.type || 'unknown'}`;
      if (!debouncerRef.current.canShow(debounceKey, debounceMs)) return;
      toast.error('An error occurred', { description: message.message || 'Unknown error', duration: 5000 });
    };
    agentsClient.on('error', handleError);
    tasksClient.on('error', handleError);
    roundTableClient.on('error', handleError);
    metricsClient.on('error', handleError);
    return () => {
      agentsClient.off('error', handleError);
      tasksClient.off('error', handleError);
      roundTableClient.off('error', handleError);
      metricsClient.off('error', handleError);
    };
  }, [showErrorToasts, debounceMs]);

  useEffect(() => {
    const debouncer = debouncerRef.current;
    return () => debouncer.clear();
  }, []);
}
