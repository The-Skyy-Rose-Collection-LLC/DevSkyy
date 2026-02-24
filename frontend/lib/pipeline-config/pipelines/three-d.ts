/**
 * 3D Pipeline Configuration
 *
 * Providers: Tripo, Meshy, HuggingFace (3D models)
 * Capabilities: text-to-3d, image-to-3d
 */

import type { EnvVarDefinition, PipelineStatus, ServiceStatus } from '../types';
import { validateApiKey, validateEnvVars } from '../validators';

const ENV_VARS: EnvVarDefinition[] = [
  { key: 'TRIPO_API_KEY', description: 'Tripo3D API key for text/image-to-3D' },
  { key: 'MESHY_API_KEY', description: 'Meshy API key for text/image-to-3D' },
  { key: 'HF_TOKEN', description: 'HuggingFace token for 3D model spaces', prefix: 'hf_' },
];

const REQUIRED_KEYS = ENV_VARS.map((v) => v.key);

function getServiceStatus(envVar: string, label: string, prefix?: string): ServiceStatus {
  const value = process.env[envVar];
  const connected = validateApiKey(value, prefix);

  return {
    name: label,
    connected,
    mode: connected ? 'live' : 'offline',
    error: connected ? null : `Missing env var: ${envVar}`,
  };
}

export function getConnectionStatus(): PipelineStatus {
  const { present } = validateEnvVars(REQUIRED_KEYS);

  const services: ServiceStatus[] = [
    getServiceStatus('TRIPO_API_KEY', 'Tripo'),
    getServiceStatus('MESHY_API_KEY', 'Meshy'),
    getServiceStatus('HF_TOKEN', 'HuggingFace 3D', 'hf_'),
  ];

  const anyConnected = services.some((s) => s.connected);
  const allConnected = services.every((s) => s.connected);

  return {
    name: '3D Pipeline',
    connected: anyConnected,
    mode: allConnected ? 'live' : anyConnected ? 'dry-run' : 'offline',
    services,
    env_vars_needed: REQUIRED_KEYS,
    env_vars_present: present,
  };
}

export function getDryRunData(): PipelineStatus {
  return {
    name: '3D Pipeline',
    connected: true,
    mode: 'live',
    services: [
      { name: 'Tripo', connected: true, mode: 'live', error: null },
      { name: 'Meshy', connected: true, mode: 'live', error: null },
      { name: 'HuggingFace 3D', connected: true, mode: 'live', error: null },
    ],
    env_vars_needed: REQUIRED_KEYS,
    env_vars_present: [...REQUIRED_KEYS],
  };
}
