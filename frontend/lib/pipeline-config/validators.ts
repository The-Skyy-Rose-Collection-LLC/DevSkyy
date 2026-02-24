/**
 * Environment variable validators for pipeline configuration.
 *
 * Provides reusable helpers to check whether required env vars are
 * present and whether API keys match expected formats.
 */

import type { EnvValidationResult } from './types';

/**
 * Check which of the required env vars are set in `process.env`.
 * Re-evaluates on every call so hot-reloads are reflected.
 */
export function validateEnvVars(required: string[]): EnvValidationResult {
  const present: string[] = [];
  const missing: string[] = [];

  for (const key of required) {
    const value = process.env[key];
    if (value && value.trim().length > 0) {
      present.push(key);
    } else {
      missing.push(key);
    }
  }

  return {
    valid: missing.length === 0,
    missing,
    present,
  };
}

/**
 * Known API key prefix patterns.
 * When a prefix is provided, the key must start with it to be valid.
 */
const KNOWN_PREFIXES: Record<string, string> = {
  anthropic: 'sk-ant-',
  openai: 'sk-',
  stripe_secret: 'sk_',
  stripe_publishable: 'pk_',
  groq: 'gsk_',
  hf: 'hf_',
};

/**
 * Validate that an API key string is non-empty and optionally
 * matches an expected prefix.
 *
 * @param key   - The raw API key value (or undefined).
 * @param prefix - Optional prefix the key must start with
 *                 (e.g. "sk-ant-" for Anthropic).
 * @returns `true` when the key is present and matches the prefix.
 */
export function validateApiKey(
  key: string | undefined,
  prefix?: string,
): boolean {
  if (!key || key.trim().length === 0) {
    return false;
  }
  if (prefix && !key.startsWith(prefix)) {
    return false;
  }
  return true;
}

/**
 * Look up a well-known prefix by provider name.
 * Returns `undefined` when the provider is not in the lookup table.
 */
export function getKnownPrefix(provider: string): string | undefined {
  return KNOWN_PREFIXES[provider.toLowerCase()];
}

/**
 * Validate that a string is a well-formed URL.
 */
export function validateUrl(url: string | undefined): boolean {
  if (!url || url.trim().length === 0) {
    return false;
  }
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}
