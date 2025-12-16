/**
 * Jest Global Teardown
 * Runs once after all test suites
 */
export default async () => {
    console.log('🧹 Cleaning up after tests...');
    // Clean up test database if needed
    // await cleanupTestDatabase();
    // Close any open connections
    // await closeConnections();
    console.log('✅ Global test teardown completed');
};
//# sourceMappingURL=globalTeardown.js.map
