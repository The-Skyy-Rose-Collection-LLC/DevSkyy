/**
 * DevSkyy Enterprise Platform - Configuration Management
 * Centralized configuration with environment-specific settings
 */

import type { DevSkyyConfig, DatabaseConfig } from '../types/index';

// Environment variables with defaults
const getEnvVar = (key: string, defaultValue?: string): string => {
  const value = process.env[key];
  if (value === undefined && defaultValue === undefined) {
    throw new Error(`Environment variable ${key} is required but not set`);
  }
  return value ?? defaultValue!;
};

const getOptionalEnvVar = (key: string, defaultValue: string = ''): string => {
  return process.env[key] || defaultValue;
};

const getEnvNumber = (key: string, defaultValue: number): number => {
  const value = process.env[key];
  if (value === undefined) return defaultValue;
  const parsed = parseInt(value, 10);
  if (isNaN(parsed)) {
    throw new Error(`Environment variable ${key} must be a valid number`);
  }
  return parsed;
};

const getEnvBoolean = (key: string, defaultValue: boolean): boolean => {
  const value = process.env[key];
  if (value === undefined) return defaultValue;
  return value.toLowerCase() === 'true';
};

// Core platform configuration
export const config: DevSkyyConfig = {
  environment: getEnvVar('NODE_ENV', 'development') as DevSkyyConfig['environment'],
  apiVersion: getEnvVar('API_VERSION', 'v1'),
  baseUrl: getEnvVar('BASE_URL', 'http://localhost:3000'),
  timeout: getEnvNumber('REQUEST_TIMEOUT', 30000),
  retryAttempts: getEnvNumber('RETRY_ATTEMPTS', 3),
  enableLogging: getEnvBoolean('ENABLE_LOGGING', true),
  enableMetrics: getEnvBoolean('ENABLE_METRICS', true),
};

// Database configuration
export const databaseConfig: DatabaseConfig = {
  host: getEnvVar('DB_HOST', 'localhost'),
  port: getEnvNumber('DB_PORT', 5432),
  database: getEnvVar('DB_NAME', 'devskyy'),
  username: getEnvVar('DB_USER', 'devskyy'),
  password: getEnvVar('DB_PASSWORD'),
  ssl: getEnvBoolean('DB_SSL', config.environment === 'production'),
  poolSize: getEnvNumber('DB_POOL_SIZE', 20),
  timeout: getEnvNumber('DB_TIMEOUT', 10000),
};

// Redis configuration
export const redisConfig = {
  host: getEnvVar('REDIS_HOST', 'localhost'),
  port: getEnvNumber('REDIS_PORT', 6379),
  password: getEnvVar('REDIS_PASSWORD', ''),
  db: getEnvNumber('REDIS_DB', 0),
  keyPrefix: getEnvVar('REDIS_KEY_PREFIX', 'devskyy:'),
  maxRetriesPerRequest: getEnvNumber('REDIS_MAX_RETRIES', 3),
  retryDelayOnFailover: getEnvNumber('REDIS_RETRY_DELAY', 100),
};

// JWT configuration
export const jwtConfig = {
  secret: getEnvVar('JWT_SECRET'),
  expiresIn: getEnvVar('JWT_EXPIRES_IN', '24h'),
  refreshExpiresIn: getEnvVar('JWT_REFRESH_EXPIRES_IN', '7d'),
  issuer: getEnvVar('JWT_ISSUER', 'devskyy'),
  audience: getEnvVar('JWT_AUDIENCE', 'devskyy-api'),
};

// OpenAI configuration
export const openaiConfig = {
  apiKey: getOptionalEnvVar('OPENAI_API_KEY', 'demo_key_for_development'),
  organization: getEnvVar('OPENAI_ORGANIZATION', ''),
  baseURL: getEnvVar('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
  defaultModel: getEnvVar('OPENAI_DEFAULT_MODEL', 'gpt-4o'),
  maxTokens: getEnvNumber('OPENAI_MAX_TOKENS', 4000),
  temperature: parseFloat(getEnvVar('OPENAI_TEMPERATURE', '0.7')),
  timeout: getEnvNumber('OPENAI_TIMEOUT', 60000),
};

// Anthropic configuration
export const anthropicConfig = {
  apiKey: getOptionalEnvVar('ANTHROPIC_API_KEY', 'demo_key_for_development'),
  baseURL: getEnvVar('ANTHROPIC_BASE_URL', 'https://api.anthropic.com'),
  defaultModel: getEnvVar('ANTHROPIC_DEFAULT_MODEL', 'claude-3-sonnet-20240229'),
  maxTokens: getEnvNumber('ANTHROPIC_MAX_TOKENS', 4000),
  timeout: getEnvNumber('ANTHROPIC_TIMEOUT', 60000),
};

// Security configuration
export const securityConfig = {
  encryptionKey: getEnvVar('ENCRYPTION_KEY'),
  hashRounds: getEnvNumber('HASH_ROUNDS', 12),
  sessionSecret: getEnvVar('SESSION_SECRET'),
  corsOrigins: getEnvVar('CORS_ORIGINS', '*').split(','),
  rateLimitWindow: getEnvNumber('RATE_LIMIT_WINDOW', 900000), // 15 minutes
  rateLimitMax: getEnvNumber('RATE_LIMIT_MAX', 100),
  csrfSecret: getEnvVar('CSRF_SECRET', ''),
};

// Monitoring configuration
export const monitoringConfig = {
  enableHealthChecks: getEnvBoolean('ENABLE_HEALTH_CHECKS', true),
  healthCheckInterval: getEnvNumber('HEALTH_CHECK_INTERVAL', 30000),
  metricsPort: getEnvNumber('METRICS_PORT', 9090),
  logLevel: getEnvVar('LOG_LEVEL', 'info'),
  sentryDsn: getEnvVar('SENTRY_DSN', ''),
};

// Agent configuration
export const agentConfig = {
  maxConcurrentTasks: getEnvNumber('AGENT_MAX_CONCURRENT_TASKS', 10),
  taskTimeout: getEnvNumber('AGENT_TASK_TIMEOUT', 300000), // 5 minutes
  retryAttempts: getEnvNumber('AGENT_RETRY_ATTEMPTS', 3),
  retryDelay: getEnvNumber('AGENT_RETRY_DELAY', 1000),
  enableMetrics: getEnvBoolean('AGENT_ENABLE_METRICS', true),
};

// WordPress configuration
export const wordpressConfig = {
  url: getEnvVar('WORDPRESS_URL', ''),
  username: getEnvVar('WORDPRESS_USERNAME', ''),
  password: getEnvVar('WORDPRESS_PASSWORD', ''),
  apiVersion: getEnvVar('WORDPRESS_API_VERSION', 'wp/v2'),
  timeout: getEnvNumber('WORDPRESS_TIMEOUT', 30000),
};

// Three.js configuration
export const threejsConfig = {
  enableWebGL2: getEnvBoolean('THREEJS_ENABLE_WEBGL2', true),
  enableShadows: getEnvBoolean('THREEJS_ENABLE_SHADOWS', true),
  antialias: getEnvBoolean('THREEJS_ANTIALIAS', true),
  pixelRatio: getEnvNumber('THREEJS_PIXEL_RATIO', 1),
  maxTextureSize: getEnvNumber('THREEJS_MAX_TEXTURE_SIZE', 2048),
};

// Export all configurations
export const allConfigs = {
  config,
  databaseConfig,
  redisConfig,
  jwtConfig,
  openaiConfig,
  anthropicConfig,
  securityConfig,
  monitoringConfig,
  agentConfig,
  wordpressConfig,
  threejsConfig,
};

// Configuration validation
export const validateConfig = (): void => {
  const requiredEnvVars = ['JWT_SECRET', 'ENCRYPTION_KEY', 'DB_PASSWORD', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY'];

  const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);

  if (missingVars.length > 0) {
    throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
  }

  // Validate configuration values
  if (config.timeout < 1000) {
    throw new Error('REQUEST_TIMEOUT must be at least 1000ms');
  }

  if (databaseConfig.poolSize < 1) {
    throw new Error('DB_POOL_SIZE must be at least 1');
  }

  if (securityConfig.hashRounds < 10) {
    throw new Error('HASH_ROUNDS must be at least 10 for security');
  }
};

// Initialize configuration validation
if (config.environment === 'production') {
  validateConfig();
}
