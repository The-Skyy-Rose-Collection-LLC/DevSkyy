/**
 * Unified Pipeline Configuration - Master Aggregator
 *
 * Imports every pipeline module and exposes a single entry point
 * that returns the status of ALL content-automation pipelines.
 *
 * Usage:
 *   import { getAllPipelineStatuses } from '@/lib/pipeline-config';
 *   const report = getAllPipelineStatuses();
 */

import type { PipelineStatus, PipelineStatusResponse } from './types';

import * as threeD from './pipelines/three-d';
import * as imagery from './pipelines/imagery';
import * as socialMedia from './pipelines/social-media';
import * as llmRoundTable from './pipelines/llm-round-table';
import * as wordpress from './pipelines/wordpress';
import * as huggingface from './pipelines/huggingface';
import * as virtualTryOn from './pipelines/virtual-tryon';
import * as payments from './pipelines/payments';

export type { PipelineStatus, PipelineStatusResponse, ServiceStatus } from './types';
export type { EnvValidationResult } from './types';
export { validateEnvVars, validateApiKey, validateUrl } from './validators';

interface PipelineModule {
  getConnectionStatus: () => PipelineStatus;
  getDryRunData: () => PipelineStatus;
}

/**
 * Registry of all pipeline modules.
 * Add new pipelines here; the aggregator picks them up automatically.
 */
const PIPELINE_REGISTRY: PipelineModule[] = [
  threeD,
  imagery,
  socialMedia,
  llmRoundTable,
  wordpress,
  huggingface,
  virtualTryOn,
  payments,
];

function buildResponse(
  pipelines: PipelineStatus[],
  dryRun: boolean,
): PipelineStatusResponse {
  const totalServices = pipelines.reduce((sum, p) => sum + p.services.length, 0);
  const connectedServices = pipelines.reduce(
    (sum, p) => sum + p.services.filter((s) => s.connected).length,
    0,
  );

  return {
    success: true,
    dry_run: dryRun,
    timestamp: new Date().toISOString(),
    summary: {
      total_pipelines: pipelines.length,
      connected_pipelines: pipelines.filter((p) => p.connected).length,
      total_services: totalServices,
      connected_services: connectedServices,
    },
    pipelines,
  };
}

/**
 * Get the live status of every registered pipeline.
 * Re-evaluates environment variables on every call.
 */
export function getAllPipelineStatuses(): PipelineStatusResponse {
  const pipelines = PIPELINE_REGISTRY.map((m) => m.getConnectionStatus());
  return buildResponse(pipelines, false);
}

/**
 * Get a simulated all-green response for UI development and testing.
 */
export function getAllPipelineStatusesDryRun(): PipelineStatusResponse {
  const pipelines = PIPELINE_REGISTRY.map((m) => m.getDryRunData());
  return buildResponse(pipelines, true);
}

/**
 * Get the status of a single pipeline by name.
 * Returns undefined if the name does not match any registered pipeline.
 */
export function getPipelineStatus(name: string): PipelineStatus | undefined {
  const all = PIPELINE_REGISTRY.map((m) => m.getConnectionStatus());
  return all.find((p) => p.name.toLowerCase() === name.toLowerCase());
}
