/**
 * WebSocket client with auto-reconnect for real-time dashboard updates.
 *
 * Replaces HTTP polling with <100ms real-time updates via WebSocket channels.
 *
 * Channels:
 * - agents: Agent status and execution updates
 * - round_table: LLM Round Table competition progress
 * - tasks: Task execution status
 * - 3d_pipeline: 3D asset generation progress
 * - metrics: System performance metrics
 *
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Type-safe message handlers
 * - Connection state tracking
 * - Singleton instances per channel
 *
 * Usage:
 *   import { agentsClient } from '@/lib/websocket';
 *
 *   agentsClient.on('agent_status_update', (data) => {
 *     console.log('Agent update:', data);
 *   });
 */

export type MessageHandler<T = any> = (data: T) => void;

export enum ConnectionState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  RECONNECTING = 'reconnecting',
  FAILED = 'failed',
}

export interface WebSocketMessage {
  type: string;
  timestamp: string;
  [key: string]: any;
}

export interface RealtimeClientOptions {
  /** WebSocket URL (defaults to env or localhost) */
  url?: string;
  /** Maximum reconnection attempts before giving up */
  maxReconnectAttempts?: number;
  /** Initial reconnection delay in ms */
  reconnectDelay?: number;
  /** Maximum reconnection delay in ms */
  maxReconnectDelay?: number;
  /** Enable debug logging */
  debug?: boolean;
}

/**
 * WebSocket client with auto-reconnect and message routing.
 */
export class RealtimeClient {
  private ws: WebSocket | null = null;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private stateHandlers: Set<(state: ConnectionState) => void> = new Set();
  private reconnectAttempts = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private state: ConnectionState = ConnectionState.DISCONNECTED;

  private readonly channel: string;
  private readonly options: Required<RealtimeClientOptions>;

  constructor(channel: string, options: RealtimeClientOptions = {}) {
    this.channel = channel;
    this.options = {
      url: options.url || this.getDefaultUrl(),
      maxReconnectAttempts: options.maxReconnectAttempts ?? 10,
      reconnectDelay: options.reconnectDelay ?? 1000,
      maxReconnectDelay: options.maxReconnectDelay ?? 30000,
      debug: options.debug ?? false,
    };

    this.connect();
  }

  /**
   * Get default WebSocket URL from environment or fallback to localhost.
   */
  private getDefaultUrl(): string {
    if (typeof window === 'undefined') {
      return 'ws://localhost:8000';
    }

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = process.env.NEXT_PUBLIC_WS_URL ||
                   process.env.NEXT_PUBLIC_API_URL?.replace(/^https?:/, wsProtocol) ||
                   `${wsProtocol}//${window.location.host}`;

    return wsHost.replace(/\/$/, ''); // Remove trailing slash
  }

  /**
   * Update connection state and notify listeners.
   */
  private setState(newState: ConnectionState): void {
    if (this.state === newState) return;

    this.state = newState;
    this.log(`State changed: ${newState}`);

    this.stateHandlers.forEach(handler => {
      try {
        handler(newState);
      } catch (error) {
        console.error('[WebSocket] Error in state handler:', error);
      }
    });
  }

  /**
   * Log debug messages if debug mode enabled.
   */
  private log(...args: any[]): void {
    if (this.options.debug) {
      console.log(`[WS:${this.channel}]`, ...args);
    }
  }

  /**
   * Connect to WebSocket server.
   */
  private connect(): void {
    // Clear any pending reconnection timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    const wsUrl = `${this.options.url}/ws/${this.channel}`;
    this.log(`Connecting to ${wsUrl}`);
    this.setState(this.reconnectAttempts > 0 ? ConnectionState.RECONNECTING : ConnectionState.CONNECTING);

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.log('Connected');
        this.setState(ConnectionState.CONNECTED);
        this.reconnectAttempts = 0;

        // Send initial ping to verify connection
        this.send({ type: 'ping' });
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.log('Received message:', message.type);

          // Route message to registered handlers
          const messageHandlers = this.handlers.get(message.type) || new Set();
          messageHandlers.forEach(handler => {
            try {
              handler(message);
            } catch (error) {
              console.error(`[WebSocket] Error in handler for ${message.type}:`, error);
            }
          });
        } catch (error) {
          console.error('[WebSocket] Error parsing message:', error);
        }
      };

      this.ws.onclose = (event) => {
        this.log(`Disconnected (code: ${event.code}, reason: ${event.reason})`);
        this.setState(ConnectionState.DISCONNECTED);
        this.ws = null;

        // Attempt reconnection if not explicitly closed
        if (event.code !== 1000) {
          this.reconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error(`[WebSocket:${this.channel}] Error:`, error);
        // onclose will be called after onerror, so reconnection handled there
      };

    } catch (error) {
      console.error(`[WebSocket:${this.channel}] Connection error:`, error);
      this.setState(ConnectionState.DISCONNECTED);
      this.reconnect();
    }
  }

  /**
   * Attempt to reconnect with exponential backoff.
   */
  private reconnect(): void {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.error(`[WebSocket:${this.channel}] Max reconnect attempts (${this.options.maxReconnectAttempts}) reached`);
      this.setState(ConnectionState.FAILED);
      return;
    }

    this.reconnectAttempts++;

    // Exponential backoff: delay * 2^(attempts - 1)
    const delay = Math.min(
      this.options.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.options.maxReconnectDelay
    );

    this.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.options.maxReconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Send message to server.
   */
  public send(message: Record<string, any>): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn(`[WebSocket:${this.channel}] Cannot send message, not connected`);
      return;
    }

    try {
      this.ws.send(JSON.stringify(message));
      this.log('Sent message:', message.type);
    } catch (error) {
      console.error(`[WebSocket:${this.channel}] Error sending message:`, error);
    }
  }

  /**
   * Register handler for specific message type.
   */
  public on<T = any>(messageType: string, handler: MessageHandler<T>): void {
    if (!this.handlers.has(messageType)) {
      this.handlers.set(messageType, new Set());
    }
    this.handlers.get(messageType)!.add(handler);
    this.log(`Registered handler for ${messageType}`);
  }

  /**
   * Unregister handler for specific message type.
   */
  public off<T = any>(messageType: string, handler: MessageHandler<T>): void {
    const handlers = this.handlers.get(messageType);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.handlers.delete(messageType);
      }
      this.log(`Unregistered handler for ${messageType}`);
    }
  }

  /**
   * Register handler for connection state changes.
   */
  public onStateChange(handler: (state: ConnectionState) => void): void {
    this.stateHandlers.add(handler);
  }

  /**
   * Unregister handler for connection state changes.
   */
  public offStateChange(handler: (state: ConnectionState) => void): void {
    this.stateHandlers.delete(handler);
  }

  /**
   * Get current connection state.
   */
  public getState(): ConnectionState {
    return this.state;
  }

  /**
   * Check if currently connected.
   */
  public isConnected(): boolean {
    return this.state === ConnectionState.CONNECTED;
  }

  /**
   * Manually disconnect and stop reconnection attempts.
   */
  public disconnect(): void {
    this.log('Disconnecting');

    // Clear reconnection timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Close WebSocket connection
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.setState(ConnectionState.DISCONNECTED);
    this.reconnectAttempts = this.options.maxReconnectAttempts; // Prevent auto-reconnect
  }

  /**
   * Manually trigger reconnection.
   */
  public reconnectNow(): void {
    this.log('Manual reconnection triggered');
    this.reconnectAttempts = 0;
    this.disconnect();
    this.connect();
  }
}

// =============================================================================
// Singleton Instances for Each Channel
// =============================================================================

/**
 * Singleton WebSocket client for agent status updates.
 */
export const agentsClient = new RealtimeClient('agents', {
  debug: process.env.NODE_ENV === 'development',
});

/**
 * Singleton WebSocket client for Round Table competition updates.
 */
export const roundTableClient = new RealtimeClient('round_table', {
  debug: process.env.NODE_ENV === 'development',
});

/**
 * Singleton WebSocket client for task execution updates.
 */
export const tasksClient = new RealtimeClient('tasks', {
  debug: process.env.NODE_ENV === 'development',
});

/**
 * Singleton WebSocket client for 3D pipeline updates.
 */
export const pipelineClient = new RealtimeClient('3d_pipeline', {
  debug: process.env.NODE_ENV === 'development',
});

/**
 * Singleton WebSocket client for system metrics updates.
 */
export const metricsClient = new RealtimeClient('metrics', {
  debug: process.env.NODE_ENV === 'development',
});

// =============================================================================
// Cleanup on Module Unload (Browser Only)
// =============================================================================

if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    agentsClient.disconnect();
    roundTableClient.disconnect();
    tasksClient.disconnect();
    pipelineClient.disconnect();
    metricsClient.disconnect();
  });
}
