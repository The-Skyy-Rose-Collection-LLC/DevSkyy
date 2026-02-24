/**
 * Payments Pipeline Configuration
 *
 * Provider: Stripe
 * Capabilities: checkout, subscriptions, invoicing
 */

import type { EnvVarDefinition, PipelineStatus, ServiceStatus } from '../types';
import { validateApiKey, validateEnvVars } from '../validators';

const ENV_VARS: EnvVarDefinition[] = [
  { key: 'STRIPE_API_KEY', description: 'Stripe secret key (sk_live_* or sk_test_*)', prefix: 'sk_' },
  {
    key: 'STRIPE_PUBLISHABLE_KEY',
    description: 'Stripe publishable key (pk_live_* or pk_test_*)',
    prefix: 'pk_',
  },
];

const REQUIRED_KEYS = ENV_VARS.map((v) => v.key);

export function getConnectionStatus(): PipelineStatus {
  const { present } = validateEnvVars(REQUIRED_KEYS);

  const secretConnected = validateApiKey(process.env.STRIPE_API_KEY, 'sk_');
  const publishableConnected = validateApiKey(process.env.STRIPE_PUBLISHABLE_KEY, 'pk_');
  const bothConnected = secretConnected && publishableConnected;

  const services: ServiceStatus[] = [
    {
      name: 'Stripe Secret Key',
      connected: secretConnected,
      mode: secretConnected ? 'live' : 'offline',
      error: secretConnected ? null : 'Missing or invalid STRIPE_API_KEY (must start with sk_)',
    },
    {
      name: 'Stripe Publishable Key',
      connected: publishableConnected,
      mode: publishableConnected ? 'live' : 'offline',
      error: publishableConnected
        ? null
        : 'Missing or invalid STRIPE_PUBLISHABLE_KEY (must start with pk_)',
    },
  ];

  return {
    name: 'Payments',
    connected: bothConnected,
    mode: bothConnected ? 'live' : secretConnected ? 'dry-run' : 'offline',
    services,
    env_vars_needed: REQUIRED_KEYS,
    env_vars_present: present,
  };
}

export function getDryRunData(): PipelineStatus {
  return {
    name: 'Payments',
    connected: true,
    mode: 'live',
    services: [
      { name: 'Stripe Secret Key', connected: true, mode: 'live', error: null },
      { name: 'Stripe Publishable Key', connected: true, mode: 'live', error: null },
    ],
    env_vars_needed: REQUIRED_KEYS,
    env_vars_present: [...REQUIRED_KEYS],
  };
}
