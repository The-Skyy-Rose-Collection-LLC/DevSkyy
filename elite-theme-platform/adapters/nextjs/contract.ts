/**
 * Elite Theme Platform — Next.js Adapter Contract
 *
 * Typed interface stubs for the six-method adapter contract defined in
 * docs/superpowers/specs/elite-theme-platform.html §2.1.
 *
 * Theme-type: dashboard (devskyy.app — autonomous control interfaces)
 * Provider:   Next.js 16 App Router + Vercel
 *
 * Implement these six methods to satisfy the agnostic core. The WordPress
 * adapter (M0 reference) implements the same interface for PHP templates +
 * WooCommerce. The shapes below are dashboard-flavored — where WordPress
 * returns PHP file paths and WooCommerce hook names, this adapter returns
 * RSC route paths, API endpoint paths, and Vercel deployment handles.
 */

// ---------------------------------------------------------------------------
// Shared primitive types
// ---------------------------------------------------------------------------

/** Raw brand brief from the agnostic core intake layer (M4 will formalize). */
export interface BrandBrief {
  /** Brand identity slug, e.g. "skyyrose" */
  slug: string;
  /** Human display name */
  name: string;
  /** Design token overrides — merged over DASHBOARD_TOKENS defaults */
  tokenOverrides?: Partial<DashboardTokenOverrides>;
  /** Sections to scaffold in the admin route tree */
  sections: DashboardSection[];
  /** Commerce provider to bind */
  commerceProvider: 'shopify' | 'medusa' | 'stripe' | 'woocommerce-api';
}

export interface DashboardSection {
  slug: string;
  label: string;
  /** RSC page route relative to app/admin/, e.g. "storefront-autonomy" */
  routePath: string;
  /** Component kit entries required by this section */
  components: ComponentKitEntry[];
}

export interface DashboardTokenOverrides {
  accentPrimary: string;
  accentSecondary: string;
  surfaceBase: string;
  surfaceCard: string;
}

export type ComponentKitEntry =
  | 'StatCard'
  | 'SignalBadge'
  | 'CycleTimeline'
  | 'KBTable'
  | 'KeyholeRow'
  | 'AutonomyCockpitSkeleton';

// ---------------------------------------------------------------------------
// scaffold() — provider project skeleton
// ---------------------------------------------------------------------------

export interface ScaffoldOutput {
  /** App Router route paths created, relative to frontend/app/ */
  routes: string[];
  /** UI component files seeded from shadcn/ui registry */
  components: string[];
  /** lib/ modules created (hexagonal data-port layer) */
  libModules: string[];
  /** hooks/ polling hooks created */
  hooks: string[];
}

/**
 * Produces the Next.js 16 App Router project skeleton from a brand brief.
 *
 * WordPress equivalent: creates theme dir + style.css + functions.php
 * Next.js equivalent:   creates app/admin/ route tree + lib/autonomy/ +
 *                       lib/api/endpoints/ + hooks/
 */
export type ScaffoldFn = (brief: BrandBrief) => Promise<ScaffoldOutput>;

// ---------------------------------------------------------------------------
// build() — emit theme in provider language
// ---------------------------------------------------------------------------

export interface DesignSystem {
  /** Token set to apply — defaults to DASHBOARD_TOKENS from tokens.ts */
  tokens: DashboardTokenSet;
  /** shadcn/ui component variants already installed */
  installedComponents: string[];
  /** Whether to emit Tailwind config extension (true) or inline styles (false) */
  tailwindExtension: boolean;
}

export interface DashboardTokenSet {
  colors: Record<string, string>;
  typography: Record<string, string>;
  spacing: Record<string, string>;
  motion: Record<string, string>;
  shadows: Record<string, string>;
}

export interface BuildOutput {
  /** Files emitted (JSX/TSX components, CSS utilities) */
  filesEmitted: string[];
  /** Tailwind config extension written, if applicable */
  tailwindConfigPath?: string;
  /** globals.css utilities added */
  cssUtilities: string[];
  /** TypeScript type errors at time of build */
  typeErrors: number;
}

/**
 * Converts a design system into dashboard JSX/RSC + Tailwind/CSS.
 *
 * WordPress equivalent: emits PHP templates + CSS/JS
 * Next.js equivalent:   emits TSX components + Tailwind config extension +
 *                       globals.css utilities
 */
export type BuildFn = (designSystem: DesignSystem) => Promise<BuildOutput>;

// ---------------------------------------------------------------------------
// deploy() — ship to provider host (gated)
// ---------------------------------------------------------------------------

export interface DeployConfig {
  /**
   * Vercel project ID. Resolved from frontend/.vercel/project.json.
   * Never hardcoded — read from env or project config at runtime.
   */
  projectId: string;
  /** Target environment */
  env: 'preview' | 'production';
  /**
   * Deploy keyhole acknowledgement. Must be set to true by the owner in the
   * terminal (STOPSHOW_ACK=1) before deploy executes. The agent never
   * self-grants this. See platform spec §4 and STOP-AND-SHOW protocol.
   */
  stopShowAck: boolean;
}

export interface DeployResult {
  /** Vercel deployment URL */
  url: string;
  /** Vercel deployment ID */
  deploymentId: string;
  /** HTTP status of the deployed root route */
  rootHttpStatus: number;
  /** Whether the deployment is live on the production alias */
  isProduction: boolean;
  /** Duration in milliseconds */
  durationMs: number;
}

/**
 * Ships the dashboard to Vercel. Gated by stopShowAck — will throw
 * DeployKeyholeError if stopShowAck is false.
 *
 * WordPress equivalent: deploy-theme.sh SFTP hot-swap
 * Next.js equivalent:   vercel deploy --prod from frontend/
 */
export type DeployFn = (config: DeployConfig) => Promise<DeployResult>;

export class DeployKeyholeError extends Error {
  constructor() {
    super(
      'Deploy keyhole not open. Set STOPSHOW_ACK=1 in the terminal and acknowledge the manifest before deploying.'
    );
    this.name = 'DeployKeyholeError';
  }
}

// ---------------------------------------------------------------------------
// monitor() — curl-reliable live signals
// ---------------------------------------------------------------------------

export interface MonitorConfig {
  /** Base URL of the deployed dashboard, e.g. "https://devskyy.app" */
  baseUrl: string;
  /** Routes to check with expected HTTP status codes */
  routeChecks: RouteCheck[];
  /** RSC-specific checks (server component render errors in response body) */
  rscChecks: RSCCheck[];
  /** Brand canon checks against rendered HTML */
  canonChecks: CanonCheck[];
}

export interface RouteCheck {
  path: string;
  expectedStatus: number;
  /** Minimum response body bytes — fails if smaller (likely error page) */
  floorBytes: number;
}

export interface RSCCheck {
  path: string;
  /** Strings that must NOT appear in the RSC payload */
  forbiddenPatterns: string[];
}

export interface CanonCheck {
  path: string;
  label: string;
  /** CSS selector or text that must be present */
  expectedPresence: string;
}

export interface MonitorResult {
  /** ISO timestamp of the check */
  timestamp: string;
  /** Overall signal: PASS, DEGRADED, or FAIL */
  verdict: 'PASS' | 'DEGRADED' | 'FAIL';
  routeResults: Array<RouteCheck & { actualStatus: number; actualBytes: number; passed: boolean }>;
  rscResults: Array<RSCCheck & { violationsFound: string[]; passed: boolean }>;
  canonResults: Array<CanonCheck & { found: boolean; passed: boolean }>;
  /** Core Web Vitals from CrUX (best-effort; omitted if unavailable) */
  webVitals?: {
    lcp?: number;
    inp?: number;
    cls?: number;
  };
}

/**
 * Runs curl-reliable live signal checks against the deployed dashboard.
 *
 * WordPress equivalent: HTTP/size/PHP-err/canon checks (theme-health-baseline.json)
 * Next.js equivalent:   HTTP/RSC-console-errors/canon checks + optional CrUX vitals
 *
 * Must be headless/cron-safe. MCP tools (Lighthouse, Chrome DevTools) are
 * best-effort enhancement, never a cycle-blocker. See platform spec §8.
 */
export type MonitorFn = (config: MonitorConfig) => Promise<MonitorResult>;

// ---------------------------------------------------------------------------
// commerceBind() — wire commerce data to dashboard
// ---------------------------------------------------------------------------

export interface CommerceBindConfig {
  provider: BrandBrief['commerceProvider'];
  /** API credentials resolved from env vars — never hardcoded */
  credentials: CommerceCredentials;
  /**
   * For the dashboard theme-type: bind the ADMIN READ surface only.
   * Product counts, order summaries, pipeline status.
   * Full purchase-flow commerce-bind (storefront) is out of scope for
   * this adapter variant.
   */
  bindMode: 'admin-read' | 'storefront-full';
}

export interface CommerceCredentials {
  /** Environment variable name holding the API key — not the key itself */
  apiKeyEnvVar: string;
  /** Environment variable name holding the store URL — not the URL itself */
  storeUrlEnvVar: string;
}

export interface CommerceBindResult {
  provider: string;
  bindMode: CommerceBindConfig['bindMode'];
  /** API endpoint modules created in frontend/lib/api/endpoints/ */
  endpointsCreated: string[];
  /** React Query hooks created in frontend/hooks/ */
  hooksCreated: string[];
  /** Verified: at least one successful API call completed */
  verified: boolean;
  /** Error message if verification failed */
  verificationError?: string;
}

/**
 * Wires commerce data to the dashboard UI layer.
 *
 * WordPress equivalent: WooCommerce REST API (full purchase flow)
 * Next.js dashboard equivalent: admin-read surface — product/order summaries,
 *   pipeline status cards. Storefront commerce-bind is M2 scope (Next.js
 *   headless storefront, not this dashboard adapter variant).
 */
export type CommerceBindFn = (config: CommerceBindConfig) => Promise<CommerceBindResult>;

// ---------------------------------------------------------------------------
// heal() — root-cause fix + improve
// ---------------------------------------------------------------------------

export interface Regression {
  /** Regression signature matching a known pattern in heal-knowledge.json */
  signature: string;
  /** Surface where the regression was observed */
  surface: string;
  /** Raw monitor signal that triggered detection */
  monitorSignal: string;
  /** Number of times this signature has recurred */
  recurrences: number;
}

export interface HealResult {
  /** Whether the regression was fixed in this cycle */
  healed: boolean;
  /** Files modified */
  filesChanged: string[];
  /** Root cause identified */
  rootCause: string;
  /** Fix pattern applied */
  fixPattern: string;
  /**
   * Improvement applied beyond the immediate fix:
   * - new monitor signal to prevent recurrence, or
   * - permanent structural fix in the component
   */
  improvement?: string;
  /**
   * Prevention string to add to heal-knowledge.json.
   * null if no prevention could be derived from this fix.
   */
  prevention: string | null;
  /** Whether the fix requires a re-deploy to take effect */
  requiresDeploy: boolean;
}

/**
 * Applies root-cause fix for a detected regression and proposes an improvement.
 *
 * WordPress equivalent: theme-heal-doctor.md agent with PHP rules
 * Next.js equivalent:   same agent, JSX/RSC rules
 *
 * Dashboard-specific regression categories:
 * - Broken API route (404 on /api/*)
 * - Missing Suspense boundary (build fails with Cache Components error)
 * - RSC console error in response body
 * - Stale mock data path accidentally shipped to production
 * - Badge color drift from the canonical color system
 * - fs-adapter imported from a client component (build fails fast)
 *
 * The heal agent inherits accumulated intelligence from heal-knowledge.json.
 * Fix-patterns for a11y, contrast, and canon are provider-neutral and
 * transfer from the WordPress adapter. See platform spec §5.
 */
export type HealFn = (regression: Regression) => Promise<HealResult>;

// ---------------------------------------------------------------------------
// Adapter interface (compose all six methods)
// ---------------------------------------------------------------------------

/**
 * The complete Next.js adapter. Implements all six methods of the
 * Elite Theme Platform adapter contract for theme-type: dashboard.
 *
 * Instantiate with provider-specific config; the agnostic core calls
 * each method in sequence: scaffold → build → deploy → monitor → heal.
 * commerceBind is called after scaffold, before or after build depending
 * on whether the commerce SDK affects the component layer.
 */
export interface NextjsThemeAdapter {
  readonly themeType: 'dashboard';
  readonly provider: 'nextjs';
  readonly providerVersion: '16';

  scaffold: ScaffoldFn;
  build: BuildFn;
  deploy: DeployFn;
  monitor: MonitorFn;
  commerceBind: CommerceBindFn;
  heal: HealFn;
}
