/**
 * Jest Global Setup
 * Runs once before all test suites
 */

export default async (): Promise<void> => {
  console.log('🚀 Starting DevSkyy test suite...');

  // Set test environment variables
  process.env.NODE_ENV = 'testing';
  process.env.LOG_LEVEL = 'error'; // Reduce log noise during tests

  // Initialize test database if needed
  // await initializeTestDatabase();

  console.log('✅ Global test setup completed');
};
