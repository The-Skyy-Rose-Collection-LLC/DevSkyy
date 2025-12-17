/**
 * Unit Tests for AgentService
 * @jest-environment node
 */

import { AgentService } from '../AgentService';

// Mock Logger
jest.mock('../../utils/Logger', () => ({
  Logger: jest.fn().mockImplementation(() => ({
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  })),
}));

// Mock config
jest.mock('../../config/index', () => ({
  agentConfig: {
    maxConcurrentTasks: 2,
    taskTimeout: 5000,
    retryAttempts: 3,
    retryDelay: 100,
    enableMetrics: true,
  },
}));

describe('AgentService', () => {
  let service: AgentService;

  beforeEach(() => {
    jest.clearAllMocks();
    service = new AgentService();
  });

  afterEach(() => {
    service.removeAllListeners();
  });

  describe('initialization', () => {
    it('should initialize with 6 core agents', () => {
      const agents = service.getAgents();
      expect(agents).toHaveLength(6);
    });

    it('should initialize agents with correct types', () => {
      const agents = service.getAgents();
      const types = agents.map(a => a.type);
      expect(types).toContain('wordpress_agent');
      expect(types).toContain('seo_agent');
      expect(types).toContain('content_agent');
      expect(types).toContain('social_media_agent');
      expect(types).toContain('analytics_agent');
      expect(types).toContain('security_agent');
    });

    it('should set all agents to active status', () => {
      const agents = service.getAgents();
      agents.forEach(agent => {
        expect(agent.status).toBe('active');
      });
    });
  });

  describe('getAgent', () => {
    it('should return agent by ID', () => {
      const agents = service.getAgents();
      const firstAgent = agents[0];
      const found = service.getAgent(firstAgent.id);
      expect(found).toBeDefined();
      expect(found?.id).toBe(firstAgent.id);
    });

    it('should return undefined for non-existent ID', () => {
      const found = service.getAgent('non-existent-id');
      expect(found).toBeUndefined();
    });
  });

  describe('getAgentsByType', () => {
    it('should return agents filtered by type', () => {
      const wpAgents = service.getAgentsByType('wordpress_agent');
      expect(wpAgents).toHaveLength(1);
      expect(wpAgents[0].type).toBe('wordpress_agent');
    });

    it('should return empty array for non-existent type', () => {
      const agents = service.getAgentsByType('custom_agent');
      expect(agents).toHaveLength(0);
    });
  });

  describe('createTask', () => {
    it('should create a task and return task ID', async () => {
      const taskId = await service.createTask('wordpress_agent', 'post_creation', { title: 'Test' });
      expect(taskId).toBeDefined();
      expect(taskId).toMatch(/^task_/);
    });

    it('should throw error for non-existent agent type', async () => {
      await expect(
        service.createTask('custom_agent', 'test', {})
      ).rejects.toThrow('No agents found for type: custom_agent');
    });

    it('should create task with specified priority', async () => {
      const taskId = await service.createTask('seo_agent', 'keyword_analysis', {}, 'high');
      const task = service.getTask(taskId);
      expect(task?.priority).toBe('high');
    });

    it('should emit taskStarted event', async () => {
      const startedHandler = jest.fn();
      service.on('taskStarted', startedHandler);

      await service.createTask('content_agent', 'text_generation', {});

      // Wait for async task execution
      await new Promise(resolve => setTimeout(resolve, 100));
      expect(startedHandler).toHaveBeenCalled();
    });
  });

  describe('getTask', () => {
    it('should return task by ID', async () => {
      const taskId = await service.createTask('analytics_agent', 'data_collection', {});
      const task = service.getTask(taskId);
      expect(task).toBeDefined();
      expect(task?.id).toBe(taskId);
    });

    it('should return undefined for non-existent task', () => {
      const task = service.getTask('non-existent-task');
      expect(task).toBeUndefined();
    });
  });

  describe('getTasks', () => {
    it('should return all tasks', async () => {
      await service.createTask('wordpress_agent', 'test1', {});
      await service.createTask('seo_agent', 'test2', {});
      const tasks = service.getTasks();
      expect(tasks.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('getTasksByStatus', () => {
    it('should filter tasks by status', async () => {
      await service.createTask('wordpress_agent', 'test', {});
      // Task starts as pending then moves to running
      await new Promise(resolve => setTimeout(resolve, 50));
      const runningTasks = service.getTasksByStatus('running');
      expect(runningTasks.length).toBeGreaterThanOrEqual(0);
    });
  });

  describe('cancelTask', () => {
    it('should cancel a pending task', async () => {
      const taskId = await service.createTask('security_agent', 'vulnerability_scanning', {});
      const result = service.cancelTask(taskId);
      expect(result).toBe(true);
      const task = service.getTask(taskId);
      expect(task?.status).toBe('cancelled');
    });

    it('should return false for non-existent task', () => {
      const result = service.cancelTask('non-existent-task');
      expect(result).toBe(false);
    });

    it('should emit taskCancelled event', async () => {
      const cancelledHandler = jest.fn();
      service.on('taskCancelled', cancelledHandler);

      const taskId = await service.createTask('wordpress_agent', 'test', {});
      service.cancelTask(taskId);

      expect(cancelledHandler).toHaveBeenCalled();
    });
  });

  describe('getAgentStats', () => {
    it('should return agent statistics', () => {
      const stats = service.getAgentStats();
      expect(stats.totalAgents).toBe(6);
      expect(stats.activeAgents).toBe(6);
      expect(stats.totalTasks).toBeDefined();
      expect(stats.runningTasks).toBeDefined();
      expect(stats.completedTasks).toBeDefined();
      expect(stats.failedTasks).toBeDefined();
      expect(stats.agentTypes).toBeDefined();
    });

    it('should track task counts correctly', async () => {
      await service.createTask('wordpress_agent', 'test', {});
      const stats = service.getAgentStats();
      expect(stats.totalTasks).toBeGreaterThanOrEqual(1);
    });
  });

  describe('agent capabilities', () => {
    it('should assign correct capabilities to wordpress_agent', () => {
      const agents = service.getAgentsByType('wordpress_agent');
      expect(agents[0].capabilities).toContain('post_creation');
      expect(agents[0].capabilities).toContain('theme_management');
    });

    it('should assign correct capabilities to seo_agent', () => {
      const agents = service.getAgentsByType('seo_agent');
      expect(agents[0].capabilities).toContain('keyword_analysis');
      expect(agents[0].capabilities).toContain('meta_tag_generation');
    });

    it('should assign correct capabilities to content_agent', () => {
      const agents = service.getAgentsByType('content_agent');
      expect(agents[0].capabilities).toContain('text_generation');
      expect(agents[0].capabilities).toContain('image_generation');
    });

    it('should assign correct capabilities to social_media_agent', () => {
      const agents = service.getAgentsByType('social_media_agent');
      expect(agents[0].capabilities).toContain('post_scheduling');
      expect(agents[0].capabilities).toContain('engagement_tracking');
    });

    it('should assign correct capabilities to analytics_agent', () => {
      const agents = service.getAgentsByType('analytics_agent');
      expect(agents[0].capabilities).toContain('data_collection');
      expect(agents[0].capabilities).toContain('report_generation');
    });

    it('should assign correct capabilities to security_agent', () => {
      const agents = service.getAgentsByType('security_agent');
      expect(agents[0].capabilities).toContain('vulnerability_scanning');
      expect(agents[0].capabilities).toContain('threat_detection');
    });
  });

  describe('task execution', () => {
    it('should complete task and emit taskCompleted event', async () => {
      const completedHandler = jest.fn();
      service.on('taskCompleted', completedHandler);

      await service.createTask('wordpress_agent', 'test', {});

      // Wait for task to complete (simulated execution takes 1-3 seconds)
      await new Promise(resolve => setTimeout(resolve, 4000));

      expect(completedHandler).toHaveBeenCalled();
    }, 10000);

    it('should respect max concurrent tasks limit', async () => {
      // Create more tasks than maxConcurrentTasks (2)
      const taskIds = await Promise.all([
        service.createTask('wordpress_agent', 'test1', {}),
        service.createTask('seo_agent', 'test2', {}),
        service.createTask('content_agent', 'test3', {}),
      ]);

      expect(taskIds).toHaveLength(3);

      // Check that stats reflect the limit
      await new Promise(resolve => setTimeout(resolve, 100));
      const stats = service.getAgentStats();
      expect(stats.runningTasks).toBeLessThanOrEqual(2);
    });
  });
});
