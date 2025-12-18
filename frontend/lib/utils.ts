/**
 * DevSkyy Dashboard Utilities
 * ===========================
 * Utility functions for the frontend dashboard.
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { LLMProvider, SuperAgentType } from './types';

/**
 * Merge Tailwind CSS classes with clsx and tailwind-merge.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a number as currency (USD).
 */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(value);
}

/**
 * Format milliseconds as a human-readable duration.
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${Math.round(ms)}ms`;
  }
  if (ms < 60000) {
    return `${(ms / 1000).toFixed(1)}s`;
  }
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.round((ms % 60000) / 1000);
  return `${minutes}m ${seconds}s`;
}

/**
 * Format a number with appropriate suffixes (K, M, B).
 */
export function formatNumber(value: number): string {
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1)}B`;
  }
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`;
  }
  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(1)}K`;
  }
  return value.toLocaleString();
}

/**
 * Format a percentage value.
 */
export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

/**
 * Format a date as a relative time string.
 */
export function formatRelativeTime(date: Date | string): string {
  const now = new Date();
  const then = new Date(date);
  const diffMs = now.getTime() - then.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return 'just now';
  }
  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }
  if (diffDays < 7) {
    return `${diffDays}d ago`;
  }
  return then.toLocaleDateString();
}

/**
 * Get the display name for a SuperAgent type.
 */
export function getAgentDisplayName(type: SuperAgentType): string {
  const names: Record<SuperAgentType, string> = {
    commerce: 'Commerce Agent',
    creative: 'Creative Agent',
    marketing: 'Marketing Agent',
    support: 'Support Agent',
    operations: 'Operations Agent',
    analytics: 'Analytics Agent',
  };
  return names[type] || type;
}

/**
 * Get the description for a SuperAgent type.
 */
export function getAgentDescription(type: SuperAgentType): string {
  const descriptions: Record<SuperAgentType, string> = {
    commerce: 'E-commerce, products, orders, inventory, pricing optimization',
    creative: '3D assets, images, virtual try-on, videos, visual generation',
    marketing: 'Content, campaigns, SEO, social media, brand management',
    support: 'Customer service, tickets, FAQs, escalation handling',
    operations: 'WordPress, deployment, monitoring, system health',
    analytics: 'Reports, forecasting, insights, data analysis',
  };
  return descriptions[type] || '';
}

/**
 * Get the color class for a SuperAgent type.
 */
export function getAgentColor(type: SuperAgentType): string {
  const colors: Record<SuperAgentType, string> = {
    commerce: 'bg-agent-commerce text-white',
    creative: 'bg-agent-creative text-white',
    marketing: 'bg-agent-marketing text-white',
    support: 'bg-agent-support text-white',
    operations: 'bg-agent-operations text-white',
    analytics: 'bg-agent-analytics text-white',
  };
  return colors[type] || 'bg-gray-500 text-white';
}

/**
 * Get the icon name for a SuperAgent type.
 */
export function getAgentIcon(type: SuperAgentType): string {
  const icons: Record<SuperAgentType, string> = {
    commerce: 'ShoppingCart',
    creative: 'Palette',
    marketing: 'Megaphone',
    support: 'HeadphonesIcon',
    operations: 'Settings',
    analytics: 'BarChart3',
  };
  return icons[type] || 'Bot';
}

/**
 * Get the display name for an LLM provider.
 */
export function getProviderDisplayName(provider: LLMProvider): string {
  const names: Record<LLMProvider, string> = {
    anthropic: 'Claude (Anthropic)',
    openai: 'GPT-4 (OpenAI)',
    google: 'Gemini (Google)',
    mistral: 'Mistral',
    cohere: 'Command R (Cohere)',
    groq: 'Llama (Groq)',
  };
  return names[provider] || provider;
}

/**
 * Get the color class for an LLM provider.
 */
export function getProviderColor(provider: LLMProvider): string {
  const colors: Record<LLMProvider, string> = {
    anthropic: 'bg-llm-anthropic text-white',
    openai: 'bg-llm-openai text-white',
    google: 'bg-llm-google text-white',
    mistral: 'bg-llm-mistral text-white',
    cohere: 'bg-llm-cohere text-white',
    groq: 'bg-llm-groq text-white',
  };
  return colors[provider] || 'bg-gray-500 text-white';
}

/**
 * Truncate a string to a maximum length.
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return `${str.slice(0, maxLength - 3)}...`;
}

/**
 * Generate a random ID.
 */
export function generateId(): string {
  return Math.random().toString(36).substring(2, 11);
}

/**
 * Debounce a function.
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

/**
 * Sleep for a specified duration.
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Check if we're running on the server.
 */
export function isServer(): boolean {
  return typeof window === 'undefined';
}

/**
 * Safely parse JSON with a fallback.
 */
export function safeJsonParse<T>(json: string, fallback: T): T {
  try {
    return JSON.parse(json);
  } catch {
    return fallback;
  }
}
