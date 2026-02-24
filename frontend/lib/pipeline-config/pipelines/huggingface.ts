/**
 * HuggingFace Pipeline Configuration
 *
 * Services: 3 HuggingFace Spaces (3D, Image, Try-On)
 * Token: HF_TOKEN grants access to all spaces.
 */

import type { EnvVarDefinition, PipelineStatus, ServiceStatus } from '../types';
import { validateApiKey, validateEnvVars } from '../validators';

const ENV_VARS: EnvVarDefinition[] = [
  { key: 'HF_TOKEN', description: 'HuggingFace API token for Spaces access', prefix: 'hf_' },
];

const REQUIRED_KEYS = ENV_VARS.map((v) => v.key);

const SPACES = [
  'SkyyRose 3D Space',
  'SkyyRose Image Space',
  'SkyyRose Try-On Space',
];

export function getConnectionStatus(): PipelineStatus {
  const { present } = validateEnvVars(REQUIRED_KEYS);
  const token = process.env.HF_TOKEN;
  const connected = validateApiKey(token, 'hf_');

  const services: ServiceStatus[] = SPACES.map((name) => ({
    name,
    connected,
    mode: connected ? 'live' : 'offline',
    error: connected ? null : 'Missing env var: HF_TOKEN',
  }));

  return {
    name: 'HuggingFace',
    connected,
    mode: connected ? 'live' : 'offline',
    services,
    env_vars_needed: REQUIRED_KEYS,
    env_vars_present: present,
  };
}

export function getDryRunData(): PipelineStatus {
  return {
    name: 'HuggingFace',
    connected: true,
    mode: 'live',
    services: SPACES.map((name) => ({
      name,
      connected: true,
      mode: 'live' as const,
      error: null,
    })),
    env_vars_needed: REQUIRED_KEYS,
    env_vars_present: [...REQUIRED_KEYS],
  };
}
