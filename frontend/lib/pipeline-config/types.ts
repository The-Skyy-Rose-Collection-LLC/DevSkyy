/**
 * Shared types for the unified pipeline configuration system.
 *
 * Every pipeline module implements these interfaces so the master
 * aggregator can treat them uniformly.
 */

export type PipelineMode = 'live' | 'dry-run' | 'offline';

export interface ServiceStatus {
  name: string;
  connected: boolean;
  mode: PipelineMode;
  error: string | null;
}

export interface PipelineStatus {
  name: string;
  connected: boolean;
  mode: PipelineMode;
  services: ServiceStatus[];
  env_vars_needed: string[];
  env_vars_present: string[];
}

export interface EnvVarDefinition {
  key: string;
  description: string;
  prefix?: string;
}

export interface EnvValidationResult {
  valid: boolean;
  missing: string[];
  present: string[];
}

export interface PipelineStatusResponse {
  success: boolean;
  dry_run: boolean;
  timestamp: string;
  summary: {
    total_pipelines: number;
    connected_pipelines: number;
    total_services: number;
    connected_services: number;
  };
  pipelines: PipelineStatus[];
}
