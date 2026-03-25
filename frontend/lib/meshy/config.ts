/**
 * Meshy API Configuration
 *
 * Validates the MESHY_API_KEY environment variable and exports
 * connection status. When the key is absent, the Meshy client
 * operates in dry-run mode with mock responses.
 */

export interface MeshyConnectionStatus {
  connected: boolean;
  mode: 'live' | 'dry-run';
  env_var: string;
  env_present: boolean;
  base_url: string;
  error: string | null;
}

const MESHY_ENV_VAR = 'MESHY_API_KEY';
const MESHY_BASE_URL = 'https://api.meshy.ai';

/**
 * Get the current Meshy API key from the environment.
 * Returns undefined when not set (triggers dry-run mode).
 */
export function getMeshyApiKey(): string | undefined {
  return process.env[MESHY_ENV_VAR];
}

/**
 * Check whether Meshy is configured for live API calls.
 */
export function isMeshyConnected(): boolean {
  return Boolean(getMeshyApiKey());
}

/**
 * Build the full connection status object for Meshy.
 * Re-evaluates env vars on every call so hot-reloads are reflected.
 */
export function getMeshyConnectionStatus(): MeshyConnectionStatus {
  const apiKey = getMeshyApiKey();
  const envPresent = Boolean(apiKey);

  return {
    connected: envPresent,
    mode: envPresent ? 'live' : 'dry-run',
    env_var: MESHY_ENV_VAR,
    env_present: envPresent,
    base_url: MESHY_BASE_URL,
    error: envPresent ? null : `Missing required env var: ${MESHY_ENV_VAR}`,
  };
}

export const MESHY_CONFIG = {
  base_url: MESHY_BASE_URL,
  env_var: MESHY_ENV_VAR,
  provider_id: 'meshy',
  provider_name: 'Meshy',
  provider_type: 'commercial' as const,
  capabilities: ['text-to-3d', 'image-to-3d'],
  default_timeout_ms: 60_000,
} as const;
