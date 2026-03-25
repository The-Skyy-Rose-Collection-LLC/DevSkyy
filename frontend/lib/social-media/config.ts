/**
 * Social Media Platform Configuration
 *
 * Validates environment variables for each social media platform
 * and exports connection status. Import this module to check which
 * platforms are ready for live API calls.
 */

export type PlatformId = 'instagram' | 'tiktok' | 'twitter' | 'facebook';

export interface PlatformConnection {
  platform: PlatformId;
  label: string;
  connected: boolean;
  env_var: string;
  env_present: boolean;
  error: string | null;
}

interface PlatformEnvConfig {
  platform: PlatformId;
  label: string;
  env_var: string;
  additional_vars?: string[];
}

const PLATFORM_ENV_MAP: PlatformEnvConfig[] = [
  {
    platform: 'instagram',
    label: 'Instagram',
    env_var: 'INSTAGRAM_ACCESS_TOKEN',
    additional_vars: ['INSTAGRAM_BUSINESS_ACCOUNT_ID'],
  },
  {
    platform: 'tiktok',
    label: 'TikTok',
    env_var: 'TIKTOK_ACCESS_TOKEN',
  },
  {
    platform: 'twitter',
    label: 'X / Twitter',
    env_var: 'TWITTER_API_KEY',
    additional_vars: ['TWITTER_API_SECRET', 'TWITTER_ACCESS_TOKEN', 'TWITTER_ACCESS_SECRET'],
  },
  {
    platform: 'facebook',
    label: 'Facebook',
    env_var: 'FACEBOOK_ACCESS_TOKEN',
    additional_vars: ['FACEBOOK_PAGE_ID'],
  },
];

/**
 * Check whether the LLM (Claude) key is available for caption generation.
 */
export function hasLlmKey(): boolean {
  return Boolean(process.env.ANTHROPIC_API_KEY);
}

/**
 * Build connection status for a single platform.
 */
function checkPlatform(config: PlatformEnvConfig): PlatformConnection {
  const primaryPresent = Boolean(process.env[config.env_var]);

  const missingAdditional: string[] = [];
  if (config.additional_vars) {
    for (const v of config.additional_vars) {
      if (!process.env[v]) {
        missingAdditional.push(v);
      }
    }
  }

  const connected = primaryPresent && missingAdditional.length === 0;

  let error: string | null = null;
  if (!primaryPresent) {
    error = `Missing required env var: ${config.env_var}`;
  } else if (missingAdditional.length > 0) {
    error = `Missing additional env vars: ${missingAdditional.join(', ')}`;
  }

  return {
    platform: config.platform,
    label: config.label,
    connected,
    env_var: config.env_var,
    env_present: primaryPresent,
    error,
  };
}

/**
 * Get the connection status for all platforms.
 * Re-evaluates env vars on every call so hot-reloads are reflected.
 */
export function getPlatformConnections(): PlatformConnection[] {
  return PLATFORM_ENV_MAP.map(checkPlatform);
}

/**
 * Get connection status for a specific platform.
 */
export function getPlatformConnection(platform: PlatformId): PlatformConnection {
  const config = PLATFORM_ENV_MAP.find((c) => c.platform === platform);
  if (!config) {
    return {
      platform,
      label: platform,
      connected: false,
      env_var: 'UNKNOWN',
      env_present: false,
      error: `Unknown platform: ${platform}`,
    };
  }
  return checkPlatform(config);
}

/**
 * Convenience: get the raw token for a platform (or undefined).
 */
export function getPlatformToken(platform: PlatformId): string | undefined {
  const envMap: Record<PlatformId, string> = {
    instagram: 'INSTAGRAM_ACCESS_TOKEN',
    tiktok: 'TIKTOK_ACCESS_TOKEN',
    twitter: 'TWITTER_API_KEY',
    facebook: 'FACEBOOK_ACCESS_TOKEN',
  };
  return process.env[envMap[platform]];
}
