/**
 * Elite Theme Platform — Next.js Adapter Design Tokens
 *
 * Dashboard token set for theme-type: dashboard (devskyy.app).
 * Dark ops aesthetic, data-dense, signal-driven.
 *
 * Derived from and consistent with the real dashboard design language at
 * frontend/app/globals.css and the color patterns in:
 *   - frontend/app/admin/monitoring/page.tsx (ServiceStatusBadge class map)
 *   - frontend/app/admin/autonomous/page.tsx (StatusBadge switch)
 *
 * Intentionally distinct from the WordPress storefront token set
 * (skyyrose.co design-tokens.css), which uses a luxury/editorial aesthetic
 * with rose-gold (#B76E79), holo cards, and collection palette switching.
 * The dashboard is the control layer, not the storefront.
 */

// ---------------------------------------------------------------------------
// Color system
// ---------------------------------------------------------------------------

/**
 * Surface colors — dark ops palette.
 * All surfaces are near-black; hierarchy expressed through saturation
 * and opacity steps, not hue variation.
 */
export const SURFACE = {
  /** Page background — pure near-black */
  base: '#0a0a0a',
  /** Card / panel background */
  card: '#111111',
  /** Elevated card (dialog, popover) */
  cardElevated: '#1a1a1a',
  /** Subtle separator / divider */
  border: '#222222',
  /** High-contrast border for active/focused states */
  borderActive: '#333333',
  /** bg-gray-950 Tailwind alias (matches layout.tsx SidebarInset) */
  sidebarBg: 'rgb(3 7 18)', // #030712 — gray-950
} as const;

/**
 * Signal colors — semantic verdict system.
 * All three tiers use the same opacity formula:
 *   bg: color-500/10 or /20 (ambient fill)
 *   text: color-400
 *   border: color-500/30
 *
 * Source: monitoring/page.tsx ServiceStatusBadge + autonomous/page.tsx StatusBadge
 */
export const SIGNAL = {
  healthy: {
    bg: 'bg-green-500/10',
    bgHeavy: 'bg-green-500/20',
    text: 'text-green-400',
    border: 'border-green-500/30',
    hex: '#4ade80',
  },
  degraded: {
    bg: 'bg-yellow-500/10',
    bgHeavy: 'bg-yellow-500/20',
    text: 'text-yellow-400',
    border: 'border-yellow-500/30',
    hex: '#facc15',
  },
  regressions: {
    // alias of degraded — REGRESSIONS verdict uses amber
    bg: 'bg-yellow-500/10',
    bgHeavy: 'bg-yellow-500/20',
    text: 'text-yellow-400',
    border: 'border-yellow-500/30',
    hex: '#facc15',
  },
  critical: {
    bg: 'bg-red-500/10',
    bgHeavy: 'bg-red-500/20',
    text: 'text-red-400',
    border: 'border-red-500/30',
    hex: '#f87171',
  },
  escalated: {
    // alias of critical — ESCALATED verdict uses red
    bg: 'bg-red-500/10',
    bgHeavy: 'bg-red-500/20',
    text: 'text-red-400',
    border: 'border-red-500/30',
    hex: '#f87171',
  },
  inactive: {
    bg: 'bg-gray-500/20',
    bgHeavy: 'bg-gray-500/30',
    text: 'text-gray-400',
    border: 'border-gray-500/30',
    hex: '#9ca3af',
  },
  advisory: {
    // S4 advisory-only styling — muted, non-alarming
    bg: 'bg-gray-800/50',
    bgHeavy: 'bg-gray-800/80',
    text: 'text-gray-500',
    border: 'border-gray-700/50',
    hex: '#6b7280',
  },
} as const;

/**
 * Accent — the dashboard accent is rose-gold derived but applied sparingly.
 * Used for: luxury-text-gradient headings, active nav indicators, link hover.
 * NOT used for signal state (signal state uses the semantic SIGNAL set above).
 *
 * Source: globals.css .luxury-text-gradient
 *   background: linear-gradient(135deg, #D4A5B0 0%, #B76E79 50%, #8B5465 100%)
 */
export const ACCENT = {
  /** Mid-stop of the luxury gradient — the canonical brand rose-gold */
  roseGold: '#B76E79',
  /** Light stop — used for glow/highlight */
  roseLight: '#D4A5B0',
  /** Dark stop — used for shadow/depth */
  roseDark: '#8B5465',
  /** CSS gradient string for luxury-text-gradient utility */
  gradient: 'linear-gradient(135deg, #D4A5B0 0%, #B76E79 50%, #8B5465 100%)',
} as const;

// ---------------------------------------------------------------------------
// Typography
// ---------------------------------------------------------------------------

/**
 * Font families — all self-hosted (zero Google Fonts CDN).
 * Source: globals.css font-display / font-body / font-mono.
 */
export const TYPOGRAPHY = {
  /** Display headings — Playfair Display (globals.css .font-display) */
  display: "var(--font-playfair), Georgia, serif",
  /** Body / editorial — Cormorant Garamond (globals.css .font-body) */
  body: "var(--font-cormorant), Georgia, serif",
  /** Code / data — Space Mono (globals.css .font-mono) */
  mono: "var(--font-space-mono), 'Courier New', monospace",
  /**
   * UI / system — Inter (Tailwind default; used for labels, table data,
   * navigation items). Not declared in globals.css because it falls
   * through to the browser sans-serif stack.
   */
  ui: "var(--font-inter), system-ui, sans-serif",
} as const;

/**
 * Typography scale for dashboard surfaces.
 * Data-dense: tighter line-height than editorial, smaller floor sizes.
 */
export const TYPE_SCALE = {
  /** Page title (h1, luxury-text-gradient) */
  pageTitle: { size: '2.25rem', weight: '700', lineHeight: '1.15', letterSpacing: '-0.02em' },
  /** Section title (h2, CardTitle) */
  sectionTitle: { size: '1.125rem', weight: '600', lineHeight: '1.3' },
  /** Data label / table header */
  label: { size: '0.75rem', weight: '600', lineHeight: '1', letterSpacing: '0.05em', textTransform: 'uppercase' },
  /** Body / description */
  body: { size: '0.875rem', weight: '400', lineHeight: '1.5' },
  /** Monospace data (cycle#, version, JSON) */
  data: { size: '0.8125rem', weight: '400', lineHeight: '1.4' },
  /** Badge / chip */
  badge: { size: '0.75rem', weight: '500', lineHeight: '1' },
} as const;

// ---------------------------------------------------------------------------
// Spacing
// ---------------------------------------------------------------------------

/**
 * Component-level spacing constants.
 * Dense by default — this is an ops dashboard, not a storefront.
 */
export const SPACING = {
  /** Standard card padding (pt-6 / p-4..6) */
  cardPadding: '1.5rem',
  /** Section gap in multi-column grids */
  sectionGap: '1.5rem',
  /** Row height for table/list items */
  rowHeight: '3rem',
  /** Chip / badge horizontal padding */
  badgePx: '0.5rem',
  /** Inner card content gap */
  cardInnerGap: '0.75rem',
} as const;

// ---------------------------------------------------------------------------
// Motion
// ---------------------------------------------------------------------------

/**
 * Motion presets — framer-motion values used across dashboard pages.
 * Source: monitoring/page.tsx, elite-studio/operations/[id]/page.tsx pattern.
 *
 * Single page-entry animation per route. Individual cards do NOT animate
 * on mount — only the top-level container. This avoids layout jank on
 * data-dense pages.
 */
export const MOTION = {
  /** Page entry — fade up from y:12 */
  pageEntry: {
    initial: { opacity: 0, y: 12 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.3, ease: 'easeOut' },
  },
  /** Reduced motion fallback — no transform, immediate */
  reducedMotionEntry: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.15 },
  },
} as const;

// ---------------------------------------------------------------------------
// Shadow
// ---------------------------------------------------------------------------

export const SHADOWS = {
  /** Card elevation — subtle on dark surface */
  card: '0 1px 3px 0 rgba(0, 0, 0, 0.5), 0 1px 2px -1px rgba(0, 0, 0, 0.5)',
  /** Dialog / elevated card */
  elevated: '0 8px 32px 0 rgba(0, 0, 0, 0.6)',
  /** Glassmorphism — used on select hero containers only */
  glass: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
} as const;

// ---------------------------------------------------------------------------
// Contrast reference (WordPress storefront)
// ---------------------------------------------------------------------------

/**
 * WP storefront palette — listed here for contrast / comparison only.
 * These values are NOT used in the dashboard. They appear in:
 *   - wordpress-theme/skyyrose-flagship/assets/css/design-tokens.css
 *   - CLAUDE.md Brand section
 *
 * The dashboard is operationally distinct from the storefront:
 *   storefront = luxury editorial, holo cards, rose-gold primary
 *   dashboard  = dark ops, data-dense, semantic signal colors
 */
export const WP_STOREFRONT_CONTRAST = {
  roseGold: '#B76E79',   // --skyyrose-accent (default / Kids Capsule)
  gold: '#D4AF37',        // Signature collection accent
  crimson: '#DC143C',     // Love Hurts collection accent
  silver: '#C0C0C0',      // Black Rose collection accent
  dark: '#0A0A0A',        // Background (shared with dashboard surface.base)
} as const;

// ---------------------------------------------------------------------------
// Composed token set (satisfies DashboardTokenSet from contract.ts)
// ---------------------------------------------------------------------------

import type { DashboardTokenSet } from './contract';

export const DASHBOARD_TOKENS: DashboardTokenSet = {
  colors: {
    // Surfaces
    'surface-base': SURFACE.base,
    'surface-card': SURFACE.card,
    'surface-card-elevated': SURFACE.cardElevated,
    'surface-border': SURFACE.border,
    'surface-border-active': SURFACE.borderActive,
    // Signals
    'signal-healthy': SIGNAL.healthy.hex,
    'signal-degraded': SIGNAL.degraded.hex,
    'signal-critical': SIGNAL.critical.hex,
    'signal-inactive': SIGNAL.inactive.hex,
    // Accent
    'accent-primary': ACCENT.roseGold,
    'accent-light': ACCENT.roseLight,
    'accent-dark': ACCENT.roseDark,
  },
  typography: {
    'font-display': TYPOGRAPHY.display,
    'font-body': TYPOGRAPHY.body,
    'font-mono': TYPOGRAPHY.mono,
    'font-ui': TYPOGRAPHY.ui,
  },
  spacing: {
    'card-padding': SPACING.cardPadding,
    'section-gap': SPACING.sectionGap,
    'row-height': SPACING.rowHeight,
    'badge-px': SPACING.badgePx,
    'card-inner-gap': SPACING.cardInnerGap,
  },
  motion: {
    'page-entry-duration': '0.3s',
    'page-entry-ease': 'ease-out',
    'page-entry-y': '12px',
  },
  shadows: {
    card: SHADOWS.card,
    elevated: SHADOWS.elevated,
    glass: SHADOWS.glass,
  },
} as const;
