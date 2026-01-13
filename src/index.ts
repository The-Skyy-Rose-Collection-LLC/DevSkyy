/**
 * DevSkyy Enterprise Platform - Main Entry Point
 * TypeScript/JavaScript SDK for the 6-agent ecosystem
 */

import { config, validateConfig } from './config/index';
import { Logger, createLogger } from './utils/Logger';
import { AgentService } from './services/AgentService';

// Export all public APIs
export * from './types/index';
export * from './config/index';
export * from './utils/Logger';
export * from './services/AgentService';

// Main DevSkyy SDK class
export class DevSkyy {
  private logger: Logger;
  private agentService: AgentService;
  private initialized = false;

  constructor() {
    this.logger = createLogger('DevSkyy-SDK');
    this.agentService = new AgentService();
  }

  /**
   * Initialize the DevSkyy platform
   */
  public async initialize(): Promise<void> {
    if (this.initialized) {
      this.logger.warn('DevSkyy platform already initialized');
      return;
    }

    try {
      this.logger.info('Initializing DevSkyy Enterprise Platform...');

      // Validate configuration
      if (config.environment === 'production') {
        validateConfig();
      }

      // Initialize services
      await this.initializeServices();

      this.initialized = true;
      this.logger.info('DevSkyy platform initialized successfully', {
        environment: config.environment,
        version: config.apiVersion,
        agentCount: this.agentService.getAgents().length,
      });
    } catch (error) {
      this.logger.error('Failed to initialize DevSkyy platform', error);
      throw error;
    }
  }

  /**
   * Initialize all services
   */
  private async initializeServices(): Promise<void> {
    // Agent service is already initialized in constructor
    this.logger.info('All services initialized');
  }

  /**
   * Get agent service instance
   */
  public get agents(): AgentService {
    this.ensureInitialized();
    return this.agentService;
  }

  /**
   * Get platform statistics
   */
  public getStats(): Record<string, unknown> {
    this.ensureInitialized();

    return {
      platform: {
        version: config.apiVersion,
        environment: config.environment,
        initialized: this.initialized,
        uptime: process.uptime(),
      },
      agents: this.agentService.getAgentStats(),
    };
  }

  /**
   * Health check
   */
  public async healthCheck(): Promise<{ status: string; details: Record<string, unknown> }> {
    const details: Record<string, unknown> = {
      platform: this.initialized ? 'healthy' : 'not_initialized',
      agents: this.agentService.getAgents().length > 0 ? 'healthy' : 'no_agents',
      memory: process.memoryUsage(),
      uptime: process.uptime(),
    };

    const isHealthy = this.initialized && this.agentService.getAgents().length > 0;

    return {
      status: isHealthy ? 'healthy' : 'unhealthy',
      details,
    };
  }

  /**
   * Shutdown the platform gracefully
   */
  public async shutdown(): Promise<void> {
    if (!this.initialized) {
      return;
    }

    this.logger.info('Shutting down DevSkyy platform...');

    try {
      // Cancel all running tasks
      const runningTasks = this.agentService.getTasksByStatus('running');
      for (const task of runningTasks) {
        this.agentService.cancelTask(task.id);
      }

      this.initialized = false;
      this.logger.info('DevSkyy platform shutdown completed');
    } catch (error) {
      this.logger.error('Error during platform shutdown', error);
      throw error;
    }
  }

  /**
   * Ensure platform is initialized
   */
  private ensureInitialized(): void {
    if (!this.initialized) {
      throw new Error('DevSkyy platform not initialized. Call initialize() first.');
    }
  }
}

// Create default instance
export const devSkyy = new DevSkyy();

// Convenience functions
export const initialize = (): Promise<void> => devSkyy.initialize();
export const getStats = (): Record<string, unknown> => devSkyy.getStats();
export const healthCheck = (): Promise<{ status: string; details: Record<string, unknown> }> => devSkyy.healthCheck();
export const shutdown = (): Promise<void> => devSkyy.shutdown();

// Agent convenience functions
export const createTask = (
  agentType: import('./types/index.js').AgentType,
  taskType: string,
  payload: Record<string, unknown>,
  priority?: import('./types/index.js').TaskPriority
): Promise<string> => devSkyy.agents.createTask(agentType, taskType, payload, priority);

export const getTask = (taskId: string): import('./types/index.js').AgentTask | undefined => devSkyy.agents.getTask(taskId);

export const getAgents = (): import('./types/index.js').Agent[] => devSkyy.agents.getAgents();

export const getAgentsByType = (type: import('./types/index.js').AgentType): import('./types/index.js').Agent[] =>
  devSkyy.agents.getAgentsByType(type);

// Auto-initialize in Node.js environment
if (typeof window === 'undefined' && typeof process !== 'undefined') {
  // Only auto-initialize if not in test environment
  if (process.env['NODE_ENV'] !== 'test') {
    initialize().catch(error => {
      console.error('Failed to auto-initialize DevSkyy platform:', error);
    });
  }
}

// Handle graceful shutdown
if (typeof process !== 'undefined') {
  const gracefulShutdown = (signal: string) => {
    console.log(`Received ${signal}, shutting down gracefully...`);
    shutdown()
      .then(() => {
        console.log('Shutdown completed');
        process.exit(0);
      })
      .catch(error => {
        console.error('Error during shutdown:', error);
        process.exit(1);
      });
  };

  process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
  process.on('SIGINT', () => gracefulShutdown('SIGINT'));
}
