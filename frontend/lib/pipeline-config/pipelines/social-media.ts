/**
 * Social Media Pipeline Configuration
 *
 * Platforms: Instagram, TikTok, X/Twitter, Facebook
 * Re-uses the existing social-media config module for env checks.
 */

import type { PipelineStatus, ServiceStatus } from '../types';
import { validateEnvVars } from '../validators';

interface PlatformDef {
  name: string;
  required: string[];
}

const PLATFORMS: PlatformDef[] = [
  {
    name: 'Instagram',
    required: ['INSTAGRAM_ACCESS_TOKEN', 'INSTAGRAM_BUSINESS_ACCOUNT_ID'],
  },
  { name: 'TikTok', required: ['TIKTOK_ACCESS_TOKEN'] },
  {
    name: 'X / Twitter',
    required: [
      'TWITTER_API_KEY',
      'TWITTER_API_SECRET',
      'TWITTER_ACCESS_TOKEN',
      'TWITTER_ACCESS_SECRET',
    ],
  },
  { name: 'Facebook', required: ['FACEBOOK_ACCESS_TOKEN', 'FACEBOOK_PAGE_ID'] },
];

const ALL_KEYS = PLATFORMS.flatMap((p) => p.required);

function platformStatus(platform: PlatformDef): ServiceStatus {
  const { valid, missing } = validateEnvVars(platform.required);

  return {
    name: platform.name,
    connected: valid,
    mode: valid ? 'live' : 'offline',
    error: valid ? null : `Missing: ${missing.join(', ')}`,
  };
}

export function getConnectionStatus(): PipelineStatus {
  const { present } = validateEnvVars(ALL_KEYS);
  const services = PLATFORMS.map(platformStatus);

  const anyConnected = services.some((s) => s.connected);
  const allConnected = services.every((s) => s.connected);

  return {
    name: 'Social Media',
    connected: anyConnected,
    mode: allConnected ? 'live' : anyConnected ? 'dry-run' : 'offline',
    services,
    env_vars_needed: ALL_KEYS,
    env_vars_present: present,
  };
}

export function getDryRunData(): PipelineStatus {
  return {
    name: 'Social Media',
    connected: true,
    mode: 'live',
    services: PLATFORMS.map((p) => ({
      name: p.name,
      connected: true,
      mode: 'live' as const,
      error: null,
    })),
    env_vars_needed: ALL_KEYS,
    env_vars_present: [...ALL_KEYS],
  };
}
