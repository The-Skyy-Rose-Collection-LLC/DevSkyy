/**
 * Jest Test Setup for DevSkyy Enterprise Platform
 * Global test configuration and utilities
 */

import 'jest';

// Mock environment variables for testing
process.env.NODE_ENV = 'testing';
process.env.JWT_SECRET = 'test-jwt-secret-key-for-testing-only';
process.env.ENCRYPTION_KEY = 'test-encryption-key-for-testing-only';
process.env.DB_PASSWORD = 'test-db-password';
process.env.OPENAI_API_KEY = 'test-openai-key';
process.env.ANTHROPIC_API_KEY = 'test-anthropic-key';

// Global test utilities
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeValidDate(): R;
      toBeValidUUID(): R;
      toHaveValidStructure(expected: Record<string, string>): R;
    }
  }
}

// Custom Jest matchers
expect.extend({
  toBeValidDate(received: unknown) {
    const pass = received instanceof Date && !isNaN(received.getTime());
    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid date`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be a valid date`,
        pass: false,
      };
    }
  },

  toBeValidUUID(received: unknown) {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    const pass = typeof received === 'string' && uuidRegex.test(received);

    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid UUID`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be a valid UUID`,
        pass: false,
      };
    }
  },

  toHaveValidStructure(received: unknown, expected: Record<string, string>) {
    if (typeof received !== 'object' || received === null) {
      return {
        message: () => `expected ${received} to be an object`,
        pass: false,
      };
    }

    const obj = received as Record<string, unknown>;
    const missingKeys: string[] = [];
    const wrongTypes: string[] = [];

    for (const [key, expectedType] of Object.entries(expected)) {
      if (!(key in obj)) {
        missingKeys.push(key);
      } else if (typeof obj[key] !== expectedType) {
        wrongTypes.push(`${key} (expected ${expectedType}, got ${typeof obj[key]})`);
      }
    }

    const pass = missingKeys.length === 0 && wrongTypes.length === 0;

    if (pass) {
      return {
        message: () => `expected object not to have valid structure`,
        pass: true,
      };
    } else {
      const errors = [
        ...missingKeys.map(key => `missing key: ${key}`),
        ...wrongTypes.map(error => `wrong type: ${error}`),
      ];
      return {
        message: () => `expected object to have valid structure. Issues: ${errors.join(', ')}`,
        pass: false,
      };
    }
  },
});

// Mock console methods for cleaner test output
const originalConsole = { ...console };

beforeAll(() => {
  // Suppress console output during tests unless explicitly needed
  console.log = jest.fn();
  console.info = jest.fn();
  console.warn = jest.fn();
  console.error = jest.fn();
});

afterAll(() => {
  // Restore console methods
  Object.assign(console, originalConsole);
});

// Global test helpers
export const createMockAgent = (overrides: Partial<import('@/types').Agent> = {}) => ({
  id: 'test-agent-id',
  name: 'Test Agent',
  type: 'custom_agent' as const,
  status: 'active' as const,
  capabilities: ['test_capability'],
  version: '1.0.0',
  lastActive: new Date(),
  metadata: {},
  ...overrides,
});

export const createMockTask = (overrides: Partial<import('@/types').AgentTask> = {}) => ({
  id: 'test-task-id',
  agentId: 'test-agent-id',
  type: 'test_task',
  payload: { test: 'data' },
  status: 'pending' as const,
  priority: 'medium' as const,
  createdAt: new Date(),
  updatedAt: new Date(),
  ...overrides,
});

export const createMockUser = (overrides: Partial<import('@/types').User> = {}) => ({
  id: 'test-user-id',
  username: 'testuser',
  email: 'test@example.com',
  role: 'developer' as const,
  permissions: [],
  isActive: true,
  createdAt: new Date(),
  updatedAt: new Date(),
  ...overrides,
});

// Test database helpers
export const clearTestDatabase = async (): Promise<void> => {
  // In a real implementation, this would clear test database tables
  // For now, it's a placeholder
};

export const seedTestDatabase = async (): Promise<void> => {
  // In a real implementation, this would seed test data
  // For now, it's a placeholder
};

// Async test helpers
export const waitFor = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

export const waitForCondition = async (
  condition: () => boolean | Promise<boolean>,
  timeout = 5000,
  interval = 100
): Promise<void> => {
  const start = Date.now();

  while (Date.now() - start < timeout) {
    if (await condition()) {
      return;
    }
    await waitFor(interval);
  }

  throw new Error(`Condition not met within ${timeout}ms`);
};

// Mock API responses
export const createMockApiResponse = <T>(data: T, overrides: Partial<import('@/types').ApiResponse<T>> = {}) => ({
  success: true,
  data,
  metadata: {
    requestId: 'test-request-id',
    timestamp: new Date().toISOString(),
    version: 'v1',
    executionTime: 100,
  },
  ...overrides,
});

// Error testing helpers
export const expectToThrowAsync = async (
  fn: () => Promise<unknown>,
  expectedError?: string | RegExp
): Promise<void> => {
  try {
    await fn();
    throw new Error('Expected function to throw, but it did not');
  } catch (error) {
    if (expectedError) {
      if (typeof expectedError === 'string') {
        expect(error).toHaveProperty('message', expectedError);
      } else {
        expect(error).toHaveProperty('message');
        expect((error as Error).message).toMatch(expectedError);
      }
    }
  }
};
