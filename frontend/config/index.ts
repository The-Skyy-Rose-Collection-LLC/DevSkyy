/**
 * Minimal configuration stub for frontend
 * Provides default values for monitoring and logging
 */

export const monitoringConfig = {
  logLevel: 'info',
  enableMetrics: false,
  enableTracing: false,
};

export const apiConfig = {
  baseUrl: process.env['NEXT_PUBLIC_API_URL'] || 'http://localhost:8000',
  timeout: 30000,
};
