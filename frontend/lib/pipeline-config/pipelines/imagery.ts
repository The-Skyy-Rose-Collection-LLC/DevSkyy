/**
 * Imagery Pipeline Configuration
 *
 * Providers: Google Gemini, Google Imagen, HuggingFace Flux
 * Capabilities: image generation, image editing, style transfer
 */

import type { EnvVarDefinition, PipelineStatus, ServiceStatus } from '../types';
import { validateApiKey, validateEnvVars } from '../validators';

const ENV_VARS: EnvVarDefinition[] = [
  {
    key: 'GOOGLE_AI_API_KEY',
    description: 'Google AI API key for Gemini vision and Imagen generation',
  },
  { key: 'HF_TOKEN', description: 'HuggingFace token for Flux image models', prefix: 'hf_' },
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

  const googleKey = process.env.GOOGLE_AI_API_KEY;
  const googleConnected = validateApiKey(googleKey);

  const services: ServiceStatus[] = [
    {
      name: 'Gemini',
      connected: googleConnected,
      mode: googleConnected ? 'live' : 'offline',
      error: googleConnected ? null : 'Missing env var: GOOGLE_AI_API_KEY',
    },
    {
      name: 'Imagen',
      connected: googleConnected,
      mode: googleConnected ? 'live' : 'offline',
      error: googleConnected ? null : 'Missing env var: GOOGLE_AI_API_KEY',
    },
    getServiceStatus('HF_TOKEN', 'HuggingFace Flux', 'hf_'),
  ];

  const anyConnected = services.some((s) => s.connected);
  const allConnected = services.every((s) => s.connected);

  return {
    name: 'Imagery Pipeline',
    connected: anyConnected,
    mode: allConnected ? 'live' : anyConnected ? 'dry-run' : 'offline',
    services,
    env_vars_needed: REQUIRED_KEYS,
    env_vars_present: present,
  };
}

export function getDryRunData(): PipelineStatus {
  return {
    name: 'Imagery Pipeline',
    connected: true,
    mode: 'live',
    services: [
      { name: 'Gemini', connected: true, mode: 'live', error: null },
      { name: 'Imagen', connected: true, mode: 'live', error: null },
      { name: 'HuggingFace Flux', connected: true, mode: 'live', error: null },
    ],
    env_vars_needed: REQUIRED_KEYS,
    env_vars_present: [...REQUIRED_KEYS],
  };
}
