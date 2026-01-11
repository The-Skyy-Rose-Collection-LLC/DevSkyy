/**
 * Real-Time Inventory Management System
 * WebSocket-based inventory tracking with visual indicators for Three.js
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import { Logger } from '../utils/Logger';
import type { InventoryStatus, StockStatus } from '../types/product';

/**
 * Inventory update event
 */
export interface InventoryUpdateEvent {
  productId: string;
  status: InventoryStatus;
  reason?: string;
}

/**
 * WebSocket message types
 */
export type InventoryMessageType = 'subscribe' | 'unsubscribe' | 'update' | 'heartbeat';

export interface InventoryMessage {
  type: InventoryMessageType;
  productId?: string;
  data?: InventoryStatus;
  timestamp: number;
}

/**
 * Inventory subscription callback
 */
export type InventoryCallback = (status: InventoryStatus) => void;

/**
 * Inventory configuration
 */
export interface InventoryConfig {
  wsUrl?: string;
  reconnectDelay?: number;
  heartbeatInterval?: number;
  lowStockThreshold?: number;
}

/**
 * Visual indicator colors for Three.js (hex)
 */
export const INVENTORY_COLORS = {
  in_stock: 0x00ff00,      // Green
  low_stock: 0xffa500,     // Orange
  out_of_stock: 0xff0000,  // Red
  default: 0xd4af37,       // Rose gold (SkyyRose brand)
} as const;

/**
 * Default configuration
 */
const DEFAULT_CONFIG: Required<InventoryConfig> = {
  wsUrl: process.env['INVENTORY_WS_URL'] || 'ws://localhost:8080/inventory',
  reconnectDelay: 3000,
  heartbeatInterval: 30000,
  lowStockThreshold: 10,
};

/**
 * Real-time inventory manager with WebSocket support
 */
export class InventoryManager {
  private logger: Logger;
  private config: Required<InventoryConfig>;
  private ws: WebSocket | null = null;
  private inventory: Map<string, InventoryStatus> = new Map();
  private subscriptions: Map<string, Set<InventoryCallback>> = new Map();
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private isConnected = false;

  constructor(config: InventoryConfig = {}) {
    this.logger = new Logger('InventoryManager');
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Connect to WebSocket server
   */
  public connect(wsUrl?: string): void {
    const url = wsUrl || this.config.wsUrl;

    try {
      this.logger.info(`Connecting to inventory WebSocket: ${url}`);
      this.ws = new WebSocket(url);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
    } catch (error) {
      this.logger.error('Failed to connect to WebSocket', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  public disconnect(): void {
    this.logger.info('Disconnecting from inventory WebSocket');
    this.isConnected = false;

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Handle WebSocket connection open
   */
  private handleOpen(): void {
    this.logger.info('Connected to inventory WebSocket');
    this.isConnected = true;

    // Start heartbeat
    this.startHeartbeat();

    // Resubscribe to all products
    for (const productId of this.subscriptions.keys()) {
      this.sendMessage({
        type: 'subscribe',
        productId,
        timestamp: Date.now(),
      });
    }
  }

  /**
   * Handle WebSocket message
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message = JSON.parse(event.data as string) as InventoryMessage;

      switch (message.type) {
        case 'update':
          if (message.data) {
            this.handleInventoryUpdate(message.data);
          }
          break;

        case 'heartbeat':
          // Heartbeat received - connection is alive
          break;

        default:
          this.logger.warn(`Unknown message type: ${message.type}`);
      }
    } catch (error) {
      this.logger.error('Failed to parse WebSocket message', error);
    }
  }

  /**
   * Handle WebSocket error
   */
  private handleError(event: Event): void {
    this.logger.error('WebSocket error', event);
  }

  /**
   * Handle WebSocket connection close
   */
  private handleClose(event: CloseEvent): void {
    this.logger.warn(`WebSocket closed: ${event.code} - ${event.reason}`);
    this.isConnected = false;

    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    // Attempt to reconnect
    this.scheduleReconnect();
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimeout) return;

    this.logger.info(`Scheduling reconnect in ${this.config.reconnectDelay}ms`);
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      this.connect();
    }, this.config.reconnectDelay);
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }

    this.heartbeatInterval = setInterval(() => {
      this.sendMessage({
        type: 'heartbeat',
        timestamp: Date.now(),
      });
    }, this.config.heartbeatInterval);
  }

  /**
   * Send message to WebSocket server
   */
  private sendMessage(message: InventoryMessage): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.logger.warn('Cannot send message - WebSocket not connected');
      return;
    }

    try {
      this.ws.send(JSON.stringify(message));
    } catch (error) {
      this.logger.error('Failed to send WebSocket message', error);
    }
  }

  /**
   * Handle inventory update from server
   */
  private handleInventoryUpdate(status: InventoryStatus): void {
    this.logger.debug(`Inventory update for ${status.productId}`, { status });

    // Update local cache
    this.inventory.set(status.productId, status);

    // Notify subscribers
    const callbacks = this.subscriptions.get(status.productId);
    if (callbacks) {
      for (const callback of callbacks) {
        try {
          callback(status);
        } catch (error) {
          this.logger.error(`Error in inventory callback for ${status.productId}`, error);
        }
      }
    }
  }

  /**
   * Get inventory status for a product
   */
  public getStatus(productId: string): InventoryStatus | null {
    return this.inventory.get(productId) || null;
  }

  /**
   * Subscribe to inventory updates for a product
   */
  public subscribe(productId: string, callback: InventoryCallback): () => void {
    // Add to subscriptions
    if (!this.subscriptions.has(productId)) {
      this.subscriptions.set(productId, new Set());
    }
    this.subscriptions.get(productId)!.add(callback);

    // Send subscribe message if connected
    if (this.isConnected) {
      this.sendMessage({
        type: 'subscribe',
        productId,
        timestamp: Date.now(),
      });
    }

    // Return unsubscribe function
    return () => {
      this.unsubscribe(productId, callback);
    };
  }

  /**
   * Unsubscribe from inventory updates
   */
  private unsubscribe(productId: string, callback: InventoryCallback): void {
    const callbacks = this.subscriptions.get(productId);
    if (callbacks) {
      callbacks.delete(callback);

      // If no more callbacks, unsubscribe from server
      if (callbacks.size === 0) {
        this.subscriptions.delete(productId);

        if (this.isConnected) {
          this.sendMessage({
            type: 'unsubscribe',
            productId,
            timestamp: Date.now(),
          });
        }
      }
    }
  }

  /**
   * Get glow color for inventory status (Three.js hex color)
   */
  public getGlowColor(status: InventoryStatus): number {
    return INVENTORY_COLORS[status.stockStatus];
  }

  /**
   * Get opacity based on inventory status
   */
  public getOpacity(status: InventoryStatus): number {
    switch (status.stockStatus) {
      case 'in_stock':
        return 1.0;
      case 'low_stock':
        return 0.8;
      case 'out_of_stock':
        return 0.4;
      default:
        return 1.0;
    }
  }

  /**
   * Get badge text for inventory status
   */
  public getBadgeText(status: InventoryStatus): string | null {
    switch (status.stockStatus) {
      case 'low_stock':
        return `Only ${status.stockQuantity} left`;
      case 'out_of_stock':
        return 'Out of Stock';
      default:
        return null;
    }
  }

  /**
   * Determine stock status based on quantity
   */
  public determineStockStatus(quantity: number): StockStatus {
    if (quantity === 0) {
      return 'out_of_stock';
    } else if (quantity <= this.config.lowStockThreshold) {
      return 'low_stock';
    } else {
      return 'in_stock';
    }
  }

  /**
   * Manually update inventory (for testing or fallback)
   */
  public updateInventory(status: InventoryStatus): void {
    this.handleInventoryUpdate(status);
  }

  /**
   * Check if manager is connected
   */
  public isConnectedToServer(): boolean {
    return this.isConnected;
  }

  /**
   * Get all cached inventory statuses
   */
  public getAllInventory(): Map<string, InventoryStatus> {
    return new Map(this.inventory);
  }

  /**
   * Clear all inventory cache
   */
  public clearCache(): void {
    this.inventory.clear();
    this.logger.info('Inventory cache cleared');
  }
}

/**
 * Create a singleton inventory manager instance
 */
let inventoryManagerInstance: InventoryManager | null = null;

export function getInventoryManager(config?: InventoryConfig): InventoryManager {
  if (!inventoryManagerInstance) {
    inventoryManagerInstance = new InventoryManager(config);
  }
  return inventoryManagerInstance;
}

export default InventoryManager;
