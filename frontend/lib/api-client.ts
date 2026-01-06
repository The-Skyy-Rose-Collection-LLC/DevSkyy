/**
 * API Client
 * ==========
 * Centralized API client with TypeScript types, error handling, and WebSocket support.
 *
 * Features:
 * - Type-safe REST API calls
 * - WebSocket connection management
 * - Automatic error handling
 * - Request/response interceptors
 * - Connection health monitoring
 */

'use client';

import type {
  AgentInfo,
  SuperAgentType,
  TaskRequest,
  TaskResponse,
  RoundTableEntry,
  LLMProviderInfo,
  DashboardMetrics,
  ToolInfo,
  VisualGenerationRequest,
  VisualGenerationResult,
} from './types';

// =============================================================================
// Configuration
// =============================================================================

const API_BASE = typeof window !== 'undefined'
  ? process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  : 'http://localhost:8000';

const WS_BASE = typeof window !== 'undefined'
  ? process.env.NEXT_PUBLIC_WS_URL ||
    process.env.NEXT_PUBLIC_API_URL?.replace(/^http/, 'ws') ||
    'ws://localhost:8000'
  : 'ws://localhost:8000';

// =============================================================================
// Error Classes
// =============================================================================

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'APIError';
  }

  get isNetworkError(): boolean {
    return this.status === 0 || this.code === 'NETWORK_ERROR';
  }

  get isServerError(): boolean {
    return this.status >= 500;
  }

  get isClientError(): boolean {
    return this.status >= 400 && this.status < 500;
  }
}

export class ConnectionError extends Error {
  constructor(message: string, public url: string) {
    super(message);
    this.name = 'ConnectionError';
  }
}

// =============================================================================
// HTTP Client
// =============================================================================

interface RequestOptions extends RequestInit {
  timeout?: number;
  retries?: number;
}

class HTTPClient {
  private baseURL: string;
  private defaultTimeout = 30000; // 30 seconds
  private defaultRetries = 0;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const {
      timeout = this.defaultTimeout,
      retries = this.defaultRetries,
      ...fetchOptions
    } = options;

    const url = `${this.baseURL}${endpoint}`;
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(url, {
          ...fetchOptions,
          headers: {
            'Content-Type': 'application/json',
            ...fetchOptions.headers,
          },
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const error = await response.json().catch(() => ({}));
          throw new APIError(
            error.detail || error.message || `Request failed: ${response.statusText}`,
            response.status,
            error.code,
            error
          );
        }

        // Handle empty responses
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          return await response.json();
        }

        return {} as T;
      } catch (error) {
        lastError = error as Error;

        // Don't retry on client errors
        if (error instanceof APIError && error.isClientError) {
          throw error;
        }

        // Retry on network errors or server errors
        if (attempt < retries) {
          await new Promise((resolve) => setTimeout(resolve, 1000 * (attempt + 1)));
          continue;
        }

        break;
      }
    }

    // Convert fetch errors to APIError
    if (lastError) {
      if (lastError.name === 'AbortError') {
        throw new APIError('Request timeout', 0, 'TIMEOUT');
      }
      if (lastError instanceof APIError) {
        throw lastError;
      }
      throw new APIError(
        lastError.message || 'Network error',
        0,
        'NETWORK_ERROR'
      );
    }

    throw new APIError('Unknown error', 0, 'UNKNOWN');
  }

  get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  post<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  put<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

// =============================================================================
// WebSocket Client
// =============================================================================

export interface WebSocketOptions {
  reconnect?: boolean;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private options: Required<WebSocketOptions>;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private status: WebSocketStatus = 'disconnected';
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private statusListeners: Set<(status: WebSocketStatus) => void> = new Set();

  constructor(url: string, options: WebSocketOptions = {}) {
    this.url = url;
    this.options = {
      reconnect: options.reconnect ?? true,
      reconnectDelay: options.reconnectDelay ?? 1000,
      maxReconnectAttempts: options.maxReconnectAttempts ?? 5,
      heartbeatInterval: options.heartbeatInterval ?? 30000,
    };
  }

  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    this.setStatus('connecting');

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.setStatus('connected');
        this.reconnectAttempts = 0;
        this.startHeartbeat();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.emit(data.type || 'message', data);
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
        this.setStatus('error');
      };

      this.ws.onclose = () => {
        this.setStatus('disconnected');
        this.stopHeartbeat();

        if (this.options.reconnect && this.reconnectAttempts < this.options.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };
    } catch (error) {
      console.error('[WebSocket] Connection error:', error);
      this.setStatus('error');
      if (this.options.reconnect) {
        this.scheduleReconnect();
      }
    }
  }

  disconnect(): void {
    this.options.reconnect = false;
    this.stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.setStatus('disconnected');
  }

  send(data: unknown): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('[WebSocket] Cannot send message, not connected');
    }
  }

  on(event: string, callback: (data: any) => void): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: string, callback: (data: any) => void): void {
    const listeners = this.listeners.get(event);
    if (listeners) {
      listeners.delete(callback);
    }
  }

  onStatus(callback: (status: WebSocketStatus) => void): void {
    this.statusListeners.add(callback);
  }

  offStatus(callback: (status: WebSocketStatus) => void): void {
    this.statusListeners.delete(callback);
  }

  getStatus(): WebSocketStatus {
    return this.status;
  }

  isConnected(): boolean {
    return this.status === 'connected';
  }

  private emit(event: string, data: any): void {
    const listeners = this.listeners.get(event);
    if (listeners) {
      listeners.forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[WebSocket] Error in listener for ${event}:`, error);
        }
      });
    }
  }

  private setStatus(status: WebSocketStatus): void {
    if (this.status !== status) {
      this.status = status;
      this.statusListeners.forEach((callback) => {
        try {
          callback(status);
        } catch (error) {
          console.error('[WebSocket] Error in status listener:', error);
        }
      });
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    const delay = this.options.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;

    this.reconnectTimer = setTimeout(() => {
      console.log(`[WebSocket] Reconnecting (attempt ${this.reconnectAttempts})...`);
      this.connect();
    }, delay);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      this.send({ type: 'ping', timestamp: new Date().toISOString() });
    }, this.options.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }
}

// =============================================================================
// API Client
// =============================================================================

class APIClient {
  private http: HTTPClient;
  private wsClients: Map<string, WebSocketClient> = new Map();

  constructor() {
    this.http = new HTTPClient(API_BASE);
  }

  // Health check
  async healthCheck(): Promise<{ status: string; version: string }> {
    return this.http.get('/health');
  }

  // Agents
  agents = {
    list: () => this.http.get<AgentInfo[]>('/api/v1/agents'),
    get: (type: SuperAgentType) => this.http.get<AgentInfo>(`/api/v1/agents/${type}`),
    execute: (type: SuperAgentType, task: string) =>
      this.http.post<TaskResponse>(`/api/v1/agents/${type}/execute`, { task }),
    start: (type: SuperAgentType) =>
      this.http.post<{ success: boolean }>(`/api/v1/agents/${type}/start`),
    stop: (type: SuperAgentType) =>
      this.http.post<{ success: boolean }>(`/api/v1/agents/${type}/stop`),
  };

  // Tasks
  tasks = {
    submit: (request: TaskRequest) =>
      this.http.post<TaskResponse>('/api/v1/tasks', request),
    get: (id: string) => this.http.get<TaskResponse>(`/api/v1/tasks/${id}`),
    list: (params?: { limit?: number; agent?: SuperAgentType }) =>
      this.http.get<TaskResponse[]>(`/api/v1/tasks${this.buildQuery(params)}`),
  };

  // Round Table
  roundTable = {
    list: (params?: { limit?: number; status?: string }) =>
      this.http.get<RoundTableEntry[]>(`/api/v1/round-table${this.buildQuery(params)}`),
    get: (id: string) => this.http.get<RoundTableEntry>(`/api/v1/round-table/${id}`),
    compete: (prompt: string) =>
      this.http.post<RoundTableEntry>('/api/v1/round-table/compete', { prompt }),
    providers: () => this.http.get<LLMProviderInfo[]>('/api/v1/round-table/providers'),
  };

  // Metrics
  metrics = {
    dashboard: () => this.http.get<DashboardMetrics>('/api/v1/metrics/dashboard'),
    agent: (type: SuperAgentType) =>
      this.http.get(`/api/v1/metrics/agents/${type}`),
  };

  // Tools
  tools = {
    list: () => this.http.get<ToolInfo[]>('/api/v1/tools'),
    test: (name: string, params: Record<string, unknown>) =>
      this.http.post('/api/v1/tools/test', { tool_name: name, parameters: params }),
  };

  // Visual Generation
  visual = {
    generate: (request: VisualGenerationRequest) =>
      this.http.post<VisualGenerationResult>('/api/v1/visual/generate', request),
    getJob: (id: string) => this.http.get(`/api/v1/visual/jobs/${id}`),
  };

  // 3D Pipeline
  threeD = {
    status: () => this.http.get('/api/v1/3d/status'),
    providers: () => this.http.get('/api/v1/3d/providers'),
    jobs: (params?: { limit?: number; status?: string }) =>
      this.http.get(`/api/v1/3d/jobs${this.buildQuery(params)}`),
    getJob: (id: string) => this.http.get(`/api/v1/3d/jobs/${id}`),
    generate: (data: unknown) => this.http.post('/api/v1/3d/generate', data),
  };

  // WebSocket connections
  websocket(channel: string, options?: WebSocketOptions): WebSocketClient {
    const key = channel;

    if (!this.wsClients.has(key)) {
      const url = `${WS_BASE}/ws/${channel}`;
      const client = new WebSocketClient(url, options);
      this.wsClients.set(key, client);
      client.connect();
    }

    return this.wsClients.get(key)!;
  }

  // Helper to build query strings
  private buildQuery(params?: Record<string, any>): string {
    if (!params || Object.keys(params).length === 0) return '';
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.set(key, String(value));
      }
    });
    const query = searchParams.toString();
    return query ? `?${query}` : '';
  }

  // Cleanup
  disconnect(): void {
    this.wsClients.forEach((client) => client.disconnect());
    this.wsClients.clear();
  }
}

// =============================================================================
// Singleton Export
// =============================================================================

export const apiClient = new APIClient();
export default apiClient;

// Cleanup on browser unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    apiClient.disconnect();
  });
}
