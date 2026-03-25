/**
 * Virtual Try-On Pipeline Configuration
 *
 * Provider: FASHN AI
 * Capabilities: garment overlay, body segmentation, virtual fitting
 */

import type { EnvVarDefinition, PipelineStatus, ServiceStatus } from '../types';
import { validateApiKey, validateEnvVars } from '../validators';

const ENV_VARS: EnvVarDefinition[] = [
  { key: 'FASHN_API_KEY', description: 'FASHN AI API key for virtual try-on' },
];

const REQUIRED_KEYS = ENV_VARS.map((v) => v.key);

export function getConnectionStatus(): PipelineStatus {
  const { present } = validateEnvVars(REQUIRED_KEYS);
  const connected = validateApiKey(process.env.FASHN_API_KEY);

  const services: ServiceStatus[] = [
    {
      name: 'FASHN Virtual Try-On',
      connected,
      mode: connected ? 'live' : 'offline',
      error: connected ? null : 'Missing env var: FASHN_API_KEY',
    },
  ];

  return {
    name: 'Virtual Try-On',
    connected,
    mode: connected ? 'live' : 'offline',
    services,
    env_vars_needed: REQUIRED_KEYS,
    env_vars_present: present,
  };
}

export function getDryRunData(): PipelineStatus {
  return {
    name: 'Virtual Try-On',
    connected: true,
    mode: 'live',
    services: [
      { name: 'FASHN Virtual Try-On', connected: true, mode: 'live', error: null },
    ],
    env_vars_needed: REQUIRED_KEYS,
    env_vars_present: [...REQUIRED_KEYS],
  };
}
