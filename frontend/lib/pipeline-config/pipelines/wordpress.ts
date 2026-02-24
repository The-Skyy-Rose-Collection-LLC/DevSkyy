/**
 * WordPress / WooCommerce Pipeline Configuration
 *
 * Services: WordPress REST API, WooCommerce REST API
 * Used for product sync, content publishing, and order management.
 */

import type { EnvVarDefinition, PipelineStatus, ServiceStatus } from '../types';
import { validateEnvVars, validateUrl } from '../validators';

const ENV_VARS: EnvVarDefinition[] = [
  { key: 'WORDPRESS_SITE_URL', description: 'WordPress site URL (e.g. https://skyyrose.co)' },
  { key: 'WORDPRESS_API_TOKEN', description: 'WordPress application password or JWT token' },
  { key: 'WOOCOMMERCE_KEY', description: 'WooCommerce REST API consumer key' },
  { key: 'WOOCOMMERCE_SECRET', description: 'WooCommerce REST API consumer secret' },
];

const REQUIRED_KEYS = ENV_VARS.map((v) => v.key);

export function getConnectionStatus(): PipelineStatus {
  const { present } = validateEnvVars(REQUIRED_KEYS);

  const siteUrl = process.env.WORDPRESS_SITE_URL;
  const urlValid = validateUrl(siteUrl);
  const tokenPresent = Boolean(process.env.WORDPRESS_API_TOKEN?.trim());
  const wooKeyPresent = Boolean(process.env.WOOCOMMERCE_KEY?.trim());
  const wooSecretPresent = Boolean(process.env.WOOCOMMERCE_SECRET?.trim());

  const wpConnected = urlValid && tokenPresent;
  const wooConnected = urlValid && wooKeyPresent && wooSecretPresent;

  const services: ServiceStatus[] = [
    {
      name: 'WordPress REST API',
      connected: wpConnected,
      mode: wpConnected ? 'live' : 'offline',
      error: !urlValid
        ? 'Invalid or missing WORDPRESS_SITE_URL'
        : !tokenPresent
          ? 'Missing WORDPRESS_API_TOKEN'
          : null,
    },
    {
      name: 'WooCommerce REST API',
      connected: wooConnected,
      mode: wooConnected ? 'live' : 'offline',
      error: !urlValid
        ? 'Invalid or missing WORDPRESS_SITE_URL'
        : !wooKeyPresent
          ? 'Missing WOOCOMMERCE_KEY'
          : !wooSecretPresent
            ? 'Missing WOOCOMMERCE_SECRET'
            : null,
    },
  ];

  const anyConnected = services.some((s) => s.connected);
  const allConnected = services.every((s) => s.connected);

  return {
    name: 'WordPress',
    connected: anyConnected,
    mode: allConnected ? 'live' : anyConnected ? 'dry-run' : 'offline',
    services,
    env_vars_needed: REQUIRED_KEYS,
    env_vars_present: present,
  };
}

export function getDryRunData(): PipelineStatus {
  return {
    name: 'WordPress',
    connected: true,
    mode: 'live',
    services: [
      { name: 'WordPress REST API', connected: true, mode: 'live', error: null },
      { name: 'WooCommerce REST API', connected: true, mode: 'live', error: null },
    ],
    env_vars_needed: REQUIRED_KEYS,
    env_vars_present: [...REQUIRED_KEYS],
  };
}
