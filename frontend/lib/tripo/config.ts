/**
 * Tripo 3D API Configuration
 *
 * Validates the TRIPO_API_KEY environment variable and exports
 * connection status. When the key is absent, the Tripo client
 * operates in dry-run mode with mock responses.
 */

export interface TripoConnectionStatus {
  connected: boolean;
  mode: 'live' | 'dry-run';
  env_var: string;
  env_present: boolean;
  base_url: string;
  error: string | null;
}

const TRIPO_ENV_VAR = 'TRIPO_API_KEY';
const TRIPO_BASE_URL = 'https://api.tripo3d.ai/v2/openapi';

/**
 * Get the current Tripo API key from the environment.
 * Returns undefined when not set (triggers dry-run mode).
 */
export function getTripoApiKey(): string | undefined {
  return process.env[TRIPO_ENV_VAR];
}

/**
 * Check whether Tripo is configured for live API calls.
 */
export function isTripoConnected(): boolean {
  return Boolean(getTripoApiKey());
}

/**
 * Build the full connection status object for Tripo.
 * Re-evaluates env vars on every call so hot-reloads are reflected.
 */
export function getTripoConnectionStatus(): TripoConnectionStatus {
  const apiKey = getTripoApiKey();
  const envPresent = Boolean(apiKey);

  return {
    connected: envPresent,
    mode: envPresent ? 'live' : 'dry-run',
    env_var: TRIPO_ENV_VAR,
    env_present: envPresent,
    base_url: TRIPO_BASE_URL,
    error: envPresent ? null : `Missing required env var: ${TRIPO_ENV_VAR}`,
  };
}

export const TRIPO_CONFIG = {
  base_url: TRIPO_BASE_URL,
  env_var: TRIPO_ENV_VAR,
  provider_id: 'tripo',
  provider_name: 'Tripo',
  provider_type: 'commercial' as const,
  capabilities: ['text-to-3d', 'image-to-3d'],
  default_timeout_ms: 60_000,
} as const;
