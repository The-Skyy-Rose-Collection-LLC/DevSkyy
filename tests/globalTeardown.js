"use strict";
/**
 * Jest Global Teardown
 * Runs once after all test suites
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = async () => {
    console.log('🧹 Cleaning up after tests...');
    // Clean up test database if needed
    // await cleanupTestDatabase();
    // Close any open connections
    // await closeConnections();
    console.log('✅ Global test teardown completed');
};
