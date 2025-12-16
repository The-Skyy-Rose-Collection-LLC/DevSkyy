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
// Custom Jest matchers
expect.extend({
    toBeValidDate(received) {
        const pass = received instanceof Date && !isNaN(received.getTime());
        if (pass) {
            return {
                message: () => `expected ${received} not to be a valid date`,
                pass: true,
            };
        }
        else {
            return {
                message: () => `expected ${received} to be a valid date`,
                pass: false,
            };
        }
    },
    toBeValidUUID(received) {
        const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
        const pass = typeof received === 'string' && uuidRegex.test(received);
        if (pass) {
            return {
                message: () => `expected ${received} not to be a valid UUID`,
                pass: true,
            };
        }
        else {
            return {
                message: () => `expected ${received} to be a valid UUID`,
                pass: false,
            };
        }
    },
    toHaveValidStructure(received, expected) {
        if (typeof received !== 'object' || received === null) {
            return {
                message: () => `expected ${received} to be an object`,
                pass: false,
            };
        }
        const obj = received;
        const missingKeys = [];
        const wrongTypes = [];
        for (const [key, expectedType] of Object.entries(expected)) {
            if (!(key in obj)) {
                missingKeys.push(key);
            }
            else if (typeof obj[key] !== expectedType) {
                wrongTypes.push(`${key} (expected ${expectedType}, got ${typeof obj[key]})`);
            }
        }
        const pass = missingKeys.length === 0 && wrongTypes.length === 0;
        if (pass) {
            return {
                message: () => `expected object not to have valid structure`,
                pass: true,
            };
        }
        else {
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
export const createMockAgent = (overrides = {}) => ({
    id: 'test-agent-id',
    name: 'Test Agent',
    type: 'custom_agent',
    status: 'active',
    capabilities: ['test_capability'],
    version: '1.0.0',
    lastActive: new Date(),
    metadata: {},
    ...overrides,
});
export const createMockTask = (overrides = {}) => ({
    id: 'test-task-id',
    agentId: 'test-agent-id',
    type: 'test_task',
    payload: { test: 'data' },
    status: 'pending',
    priority: 'medium',
    createdAt: new Date(),
    updatedAt: new Date(),
    ...overrides,
});
export const createMockUser = (overrides = {}) => ({
    id: 'test-user-id',
    username: 'testuser',
    email: 'test@example.com',
    role: 'developer',
    permissions: [],
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date(),
    ...overrides,
});
// Test database helpers
export const clearTestDatabase = async () => {
    // In a real implementation, this would clear test database tables
    // For now, it's a placeholder
};
export const seedTestDatabase = async () => {
    // In a real implementation, this would seed test data
    // For now, it's a placeholder
};
// Async test helpers
export const waitFor = (ms) => {
    return new Promise(resolve => setTimeout(resolve, ms));
};
export const waitForCondition = async (condition, timeout = 5000, interval = 100) => {
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
export const createMockApiResponse = (data, overrides = {}) => ({
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
export const expectToThrowAsync = async (fn, expectedError) => {
    try {
        await fn();
        throw new Error('Expected function to throw, but it did not');
    }
    catch (error) {
        if (expectedError) {
            if (typeof expectedError === 'string') {
                expect(error).toHaveProperty('message', expectedError);
            }
            else {
                expect(error).toHaveProperty('message');
                expect(error.message).toMatch(expectedError);
            }
        }
    }
};
//# sourceMappingURL=setup.js.map
