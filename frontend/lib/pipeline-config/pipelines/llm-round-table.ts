/**
 * LLM Round Table Pipeline Configuration
 *
 * Models: Claude, GPT-4, Gemini, Llama/Groq, Mistral, Cohere
 * Used for multi-model consensus and debate in the admin panel.
 */

import type { EnvVarDefinition, PipelineStatus, ServiceStatus } from '../types';
import { validateApiKey, validateEnvVars } from '../validators';

interface LlmProviderDef {
  name: string;
  envVar: string;
  prefix?: string;
}

const PROVIDERS: LlmProviderDef[] = [
  { name: 'Claude', envVar: 'ANTHROPIC_API_KEY', prefix: 'sk-ant-' },
  { name: 'GPT-4', envVar: 'OPENAI_API_KEY', prefix: 'sk-' },
  { name: 'Gemini', envVar: 'GOOGLE_AI_API_KEY' },
  { name: 'Llama / Groq', envVar: 'GROQ_API_KEY', prefix: 'gsk_' },
  { name: 'Mistral', envVar: 'MISTRAL_API_KEY' },
  { name: 'Cohere', envVar: 'COHERE_API_KEY' },
];

const ENV_VARS: EnvVarDefinition[] = PROVIDERS.map((p) => ({
  key: p.envVar,
  description: `API key for ${p.name}`,
  prefix: p.prefix,
}));

const REQUIRED_KEYS = ENV_VARS.map((v) => v.key);

function providerStatus(provider: LlmProviderDef): ServiceStatus {
  const value = process.env[provider.envVar];
  const connected = validateApiKey(value, provider.prefix);

  return {
    name: provider.name,
    connected,
    mode: connected ? 'live' : 'offline',
    error: connected ? null : `Missing env var: ${provider.envVar}`,
  };
}

export function getConnectionStatus(): PipelineStatus {
  const { present } = validateEnvVars(REQUIRED_KEYS);
  const services = PROVIDERS.map(providerStatus);

  const connectedCount = services.filter((s) => s.connected).length;
  const allConnected = connectedCount === services.length;

  return {
    name: 'LLM Round Table',
    connected: connectedCount >= 2,
    mode: allConnected ? 'live' : connectedCount >= 2 ? 'dry-run' : 'offline',
    services,
    env_vars_needed: REQUIRED_KEYS,
    env_vars_present: present,
  };
}

export function getDryRunData(): PipelineStatus {
  return {
    name: 'LLM Round Table',
    connected: true,
    mode: 'live',
    services: PROVIDERS.map((p) => ({
      name: p.name,
      connected: true,
      mode: 'live' as const,
      error: null,
    })),
    env_vars_needed: REQUIRED_KEYS,
    env_vars_present: [...REQUIRED_KEYS],
  };
}
