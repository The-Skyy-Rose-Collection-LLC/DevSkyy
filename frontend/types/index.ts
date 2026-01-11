/**
 * DevSkyy Enterprise Platform - Core Type Definitions
 * Comprehensive TypeScript interfaces and types for the 54-agent ecosystem
 */

// Core Platform Types
export interface DevSkyyConfig {
  environment: 'development' | 'production' | 'testing';
  apiVersion: string;
  baseUrl: string;
  timeout: number;
  retryAttempts: number;
  enableLogging: boolean;
  enableMetrics: boolean;
}

// Agent System Types
export interface Agent {
  id: string;
  name: string;
  type: AgentType;
  status: AgentStatus;
  capabilities: string[];
  version: string;
  lastActive: Date;
  metadata: Record<string, unknown>;
}

export type AgentType =
  | 'wordpress_agent'
  | 'seo_agent'
  | 'content_agent'
  | 'social_media_agent'
  | 'analytics_agent'
  | 'security_agent'
  | 'custom_agent';

export type AgentStatus = 'active' | 'inactive' | 'error' | 'maintenance';

export interface AgentTask {
  id: string;
  agentId: string;
  type: string;
  payload: Record<string, unknown>;
  status: TaskStatus;
  priority: TaskPriority;
  createdAt: Date;
  updatedAt: Date;
  completedAt?: Date;
  result?: TaskResult;
  error?: TaskError;
}

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';

export interface TaskResult {
  success: boolean;
  data: Record<string, unknown>;
  metrics: TaskMetrics;
  logs: string[];
}

export interface TaskError {
  code: string;
  message: string;
  details: Record<string, unknown>;
  stack?: string;
}

export interface TaskMetrics {
  executionTime: number;
  memoryUsage: number;
  cpuUsage: number;
  networkRequests: number;
}

// API Types
export interface ApiResponse<T = unknown> {
  success: boolean;
  data: T;
  message?: string;
  error?: ApiError;
  metadata: ResponseMetadata;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp: string;
}

export interface ResponseMetadata {
  requestId: string;
  timestamp: string;
  version: string;
  executionTime: number;
  rateLimit?: RateLimitInfo;
}

export interface RateLimitInfo {
  limit: number;
  remaining: number;
  resetTime: Date;
}

// Authentication & Security Types
export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  permissions: Permission[];
  isActive: boolean;
  lastLogin?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export type UserRole = 'admin' | 'developer' | 'operator' | 'viewer';

export interface Permission {
  resource: string;
  actions: string[];
  conditions?: Record<string, unknown>;
}

export interface AuthToken {
  accessToken: string;
  refreshToken: string;
  tokenType: 'Bearer';
  expiresIn: number;
  scope: string[];
}

export interface SecurityContext {
  user: User;
  token: AuthToken;
  permissions: Permission[];
  sessionId: string;
  ipAddress: string;
  userAgent: string;
}

// Database Types
export interface DatabaseConfig {
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl: boolean;
  poolSize: number;
  timeout: number;
}

export interface QueryOptions {
  limit?: number;
  offset?: number;
  orderBy?: string;
  orderDirection?: 'ASC' | 'DESC';
  filters?: Record<string, unknown>;
  include?: string[];
}

export interface QueryResult<T = unknown> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// Monitoring & Metrics Types
export interface Metric {
  name: string;
  value: number;
  unit: string;
  timestamp: Date;
  tags: Record<string, string>;
}

export interface HealthCheck {
  service: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: Date;
  responseTime: number;
  details: Record<string, unknown>;
}

export interface LogEntry {
  level: 'debug' | 'info' | 'warn' | 'error' | 'fatal';
  message: string;
  timestamp: Date;
  service: string;
  requestId?: string;
  userId?: string;
  metadata: Record<string, unknown>;
}

// Event System Types
export interface Event {
  id: string;
  type: string;
  source: string;
  data: Record<string, unknown>;
  timestamp: Date;
  version: string;
}

export interface EventHandler {
  eventType: string;
  handler: (event: Event) => Promise<void>;
  priority: number;
}

// Utility Types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

export type OptionalFields<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type Nullable<T> = T | null;

export type Optional<T> = T | undefined;

// Re-export product types
export * from './product';
