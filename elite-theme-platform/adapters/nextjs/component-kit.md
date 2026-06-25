# Next.js Adapter — Cockpit Component Vocabulary

This document maps the reusable component patterns extracted from the Storefront
Autonomy cockpit (`frontend/app/admin/storefront-autonomy/`) to named vocabulary
entries usable across all dashboard sections built by this adapter.

These are patterns, not duplicated code. Each entry points to the canonical
implementation in `frontend/` — when building a new dashboard section, import
from there or extract a shared component if the pattern is used in three or more
places.

---

## StatCard

**What it is:** A metric card showing a single value with a label, optional icon,
and a signal badge. The dashboard's atomic display unit for any scalar
(cycle count, version number, KB size, recurrence count).

**Canonical instances:**
- Loop status bar cycle-number display — `LoopStatusBar.tsx`
- Version delta card (Live vs Source version) — `DeployKeyholePanel.tsx`
- S3 asset version card — `StorefrontHealthPanel.tsx`

**Anatomy:**
```
Card (bg-gray-900 border-gray-800)
  CardHeader (flex items-center justify-between)
    CardTitle (text-sm font-medium text-gray-400 uppercase tracking-wider)
    Icon (lucide, h-4 w-4 text-gray-500)
  CardContent
    <value> (text-2xl font-mono font-bold text-white)
    <sublabel> (text-xs text-gray-500 mt-1)
    [SignalBadge] (optional)
```

**shadcn/ui dependencies:** `Card`, `CardContent`, `CardHeader`, `CardTitle`
**Tailwind pattern:** `bg-gray-900 border-gray-800` card base

**When to use:** Any single metric that needs ambient context (status, trend,
comparison). Never use for tabular data — use KBTable for that.

---

## SignalBadge

**What it is:** A colored pill conveying a verdict or status. Uses the canonical
`bg-*-500/[10|20] text-*-400 border-*-500/30 border` formula derived from
`monitoring/page.tsx` `ServiceStatusBadge` and `autonomous/page.tsx` `StatusBadge`.

**Canonical instances:**
- Cycle verdict (HEALTHY / REGRESSIONS / ESCALATED) — `LoopStatusBar.tsx`, `HealLogTimeline.tsx`
- Signal status (PASS / FAIL / UNAVAILABLE) — `StorefrontHealthPanel.tsx`
- Last outcome (healed / dry / escalated) — `LearningKBPanel.tsx`
- Gate badge — `HealLogTimeline.tsx`

**Color map (from `tokens.ts` SIGNAL constants):**
| Verdict/State          | bg class          | text class        | border class            |
|------------------------|-------------------|-------------------|-------------------------|
| HEALTHY / PASS / healed| `bg-green-500/10` | `text-green-400`  | `border-green-500/30`   |
| REGRESSIONS / degraded | `bg-yellow-500/10`| `text-yellow-400` | `border-yellow-500/30`  |
| ESCALATED / FAIL       | `bg-red-500/10`   | `text-red-400`    | `border-red-500/30`     |
| inactive / stopped     | `bg-gray-500/20`  | `text-gray-400`   | `border-gray-500/30`    |
| advisory / S4          | `bg-gray-800/50`  | `text-gray-500`   | `border-gray-700/50`    |

**shadcn/ui dependency:** `Badge` from `@/components/ui/badge`

**Implementation pattern:**
```tsx
// Inline class-map — matches monitoring/page.tsx and autonomous/page.tsx exactly
const cls = {
  HEALTHY:     'bg-green-500/10 text-green-400 border-green-500/30',
  REGRESSIONS: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  ESCALATED:   'bg-red-500/10 text-red-400 border-red-500/30',
}[verdict] ?? 'bg-gray-500/20 text-gray-400 border-gray-500/30';
<Badge className={`${cls} border`}>{verdict}</Badge>
```

**Do not:** create new color variants outside this map. Verdicts and signals that
don't fit one of the five rows above are advisory and should use the `advisory` row.

---

## CycleTimeline

**What it is:** A reverse-chronological list of heal-cycle entries. Each row is a
clickable card showing timestamp, cycle#, verdict badge, regression chips, and healed
chips. Clicking a row opens a Dialog with the full cycle JSON.

**Canonical implementation:** `HealLogTimeline.tsx`
**Data source:** `AutonomyCockpitData.allCycles` (from `lib/autonomy/types.ts`)
**shadcn/ui dependencies:** `Card`, `CardContent`, `Badge`, `Dialog`, `DialogContent`,
  `DialogHeader`, `DialogTitle`, `DialogDescription`, `Tabs`, `TabsList`,
  `TabsTrigger`, `TabsContent`
**Chart dependency:** `ChartContainer`, `ChartTooltip`, `ChartTooltipContent` from
  `@/components/ui/chart` (recharts wrapper) — trend sparkline in the Trend tab

**Row anatomy:**
```
<div role="row" className="flex items-center gap-3 p-3 border-b border-gray-800 hover:bg-gray-900/50 cursor-pointer">
  <span className="text-xs text-gray-500 font-mono w-32 shrink-0">{formatTimestamp(ts)}</span>
  <span className="text-xs text-gray-500 font-mono w-16 shrink-0">#{cycle}</span>
  <SignalBadge verdict={verdict} />
  <div className="flex gap-1 flex-wrap">
    {regressions.map(r => <Badge key={r} className="bg-red-500/10 text-red-400 border-red-500/30 border text-xs">{r}</Badge>)}
    {healed.map(h => <Badge key={h} className="bg-green-500/10 text-green-400 border-green-500/30 border text-xs">{h}</Badge>)}
  </div>
</div>
```

**Sparkline anatomy (recharts via ui/chart.tsx):**
```tsx
<ChartContainer config={{ meanRecurrences: { color: ACCENT.roseGold } }} className="h-24">
  <LineChart data={knowledge.metric_recurrence_trend}>
    <Line type="monotone" dataKey="meanRecurrences" stroke="var(--color-meanRecurrences)" dot={false} />
    <ChartTooltip content={<ChartTooltipContent />} />
  </LineChart>
</ChartContainer>
```

**Empty state:** `<p className="text-gray-500 text-sm py-8 text-center">No cycles recorded yet.</p>`

**Performance note:** default to last 20 entries. For >100 entries, consider
`@tanstack/react-virtual` row virtualization — same pattern as the DataTable
reference in the Frontend Developer profile.

---

## KBTable

**What it is:** A two-panel layout for the knowledge base. Left panel: regression
signatures table. Right panel: prevention strings list.

**Canonical implementation:** `LearningKBPanel.tsx`
**Data source:** `AutonomyCockpitData.knowledge` (`HealKnowledge` type)

**Left panel — Signatures table columns:**
| Column | Source field | Display |
|--------|-------------|---------|
| Signature | `signature` | mono text, truncated to 40 chars |
| Surface | `surface` | text-gray-400 |
| Recurrences | `recurrences` | mono number, colored red if >1 |
| Last outcome | `lastOutcome` | SignalBadge |
| Prevention added | `preventionAdded` | green chip if non-null, dash if null |

**Right panel — Preventions list:**
Each prevention is a `<div className="text-sm text-gray-300 border-l-2 border-rose-gold pl-3 py-1">` block.
The rose-gold left border (`border-l-2 border-[#B76E79]`) marks it as a locked improvement.

**Realism requirement:** When `knowledge.cycles === 0` (fresh install or Vercel
mock-adapter), render mock data from `mock-adapter.ts` with `isLive={false}` prop
driving a `<p className="text-xs text-yellow-400">Simulated data — run locally for live KB</p>`
banner. The KB must never be blank from day one.

**shadcn/ui dependencies:** `Card`, `CardContent`, `CardHeader`, `CardTitle`, `Badge`, `Separator`

---

## KeyholeRow

**What it is:** A read-only panel row in the Deploy Keyhole section. Displays a
single deployable artifact's status — version delta or file count — with a label
and optional diff code block. Never contains a button that triggers a deploy.

**Canonical implementation:** `DeployKeyholePanel.tsx`
**Three variants:**

### Version delta row
```
Card
  CardHeader
    GitBranch icon
    CardTitle "Version Delta"
  CardContent
    <div className="flex gap-6 font-mono text-sm">
      <div>Live <span className="text-green-400">{liveVersion}</span></div>
      <div>Source <span className="text-yellow-400">{sourceVersion}</span></div>
    </div>
    <SignalBadge verdict={liveVersion === sourceVersion ? 'HEALTHY' : 'REGRESSIONS'} />
```

### Dry manifest row
```
Card
  CardHeader
    Server icon
    CardTitle "Dry Manifest"
  CardContent
    <pre className="bg-gray-950 text-gray-300 text-xs p-3 rounded overflow-x-auto font-mono">
      {JSON.stringify(dryManifest, null, 2)}
    </pre>
```

### AUTO_DEPLOY status row
```
Card
  CardContent (flex items-center gap-2)
    "AUTO_DEPLOY"
    <SignalBadge verdict={autoDeployEnabled ? 'HEALTHY' : 'inactive'}>
      {autoDeployEnabled ? 'enabled' : 'disabled'}
    </SignalBadge>
    <span className="text-xs text-gray-500">Toggle is host-side env var only — read-only in UI</span>
```

**Callout banner (always rendered):**
```tsx
<Alert className="bg-gray-900 border-gray-700">
  <ShieldCheck className="h-4 w-4 text-yellow-400" />
  <AlertDescription className="text-gray-400 text-sm">
    Deploys run from the local host via{' '}
    <code className="text-gray-300 bg-gray-800 px-1 rounded">deploy-theme.sh</code>.
    Review the manifest here, then approve in the terminal with{' '}
    <code className="text-gray-300 bg-gray-800 px-1 rounded">STOPSHOW_ACK=1</code>.
  </AlertDescription>
</Alert>
```

**shadcn/ui dependencies:** `Card`, `CardContent`, `CardHeader`, `CardTitle`, `Alert`,
  `AlertDescription`, `Badge`

---

## AutonomyCockpitSkeleton

**What it is:** The Suspense fallback and loading-state placeholder for the cockpit.
Server-safe — no hooks, no `'use client'`. Three Skeleton blocks matching the three
visual zones of the cockpit.

**Canonical implementation:** `AutonomyCockpitSkeleton.tsx`

```tsx
// No 'use client' needed
import { Skeleton } from '@/components/ui/skeleton';

export function AutonomyCockpitSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-10 w-full" />   {/* LoopStatusBar */}
      <Skeleton className="h-40 w-full" />   {/* StorefrontHealthPanel */}
      <Skeleton className="h-64 w-full" />   {/* HealLogTimeline + KB */}
    </div>
  );
}
```

**Usage:**
1. Suspense fallback in `page.tsx` (mandatory — Cache Components guard):
   ```tsx
   <Suspense fallback={<AutonomyCockpitSkeleton />}>
     <StorefrontAutonomyContent />
   </Suspense>
   ```
2. Loading state inside `StorefrontAutonomyContent` when `loading=true && data=null`.

**shadcn/ui dependency:** `Skeleton` from `@/components/ui/skeleton`

---

## Cross-cutting patterns

### Page shell split (Cache Components guard)

Every dashboard page uses the Server Component shell / `'use client'` Content split:

```
page.tsx (Server Component — no 'use client')
  exports default PageShell
  wraps <Suspense fallback={<XxxSkeleton />}><XxxContent /></Suspense>

XxxContent.tsx ('use client')
  uses polling hook (useAutonomyCockpit, useMonitoring, etc.)
  orchestrates section components
```

Source: `elite-studio/operations/[id]/page.tsx` (canonical). The Suspense boundary
is installed defensively — even if the Content component currently has no request-time
dynamic readers, it prevents build failures if a navigation hook is added later.

### Polling hook shape

All dashboard hooks mirror `hooks/useMonitoring.ts`:

```ts
interface UseXxxState { data: XxxData | null; loading: boolean; error: string | null }
// useCallback + useEffect + setInterval(load, intervalMs)
// returns { ...state, refresh: load }
```

`useAutonomyCockpit` polls `/api/autonomy` every 60s (heal-log writes every 6h).
`useMonitoring` polls `/api/v1/monitoring/health` every 30s.
`useAutonomous` polls `/api/autonomous` on mount (no interval; state changes are user-triggered).

### API endpoint module shape

All endpoint modules mirror `lib/api/endpoints/monitoring.ts`:

```ts
import { fetchWithTimeout, getAuthHeaders, handleResponse } from '../client';
import { XxxResponseSchema } from '../schemas';

export const xxx = {
  async methodName(): Promise<XxxResponse> {
    const res = await fetchWithTimeout('/api/xxx', { headers: await getAuthHeaders() });
    return handleResponse(res, XxxResponseSchema);
  },
};
```

`lib/api/endpoints/autonomy.ts` follows this shape exactly for the `/api/autonomy` route.

### formatTimestamp utility

Used by CycleTimeline rows and LoopStatusBar. Copy verbatim from `monitoring/page.tsx`:

```ts
function formatTimestamp(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return new Date(iso).toLocaleDateString();
}
```

Extract to `frontend/lib/utils.ts` when used in three or more files.

### motion.div page entry

Wrap the outermost content `<div>` only. Do not animate individual cards.

```tsx
import { motion } from 'framer-motion';
import { MOTION } from 'elite-theme-platform/adapters/nextjs/tokens';

<motion.div {...MOTION.pageEntry}>
  {/* page content */}
</motion.div>
```

Respect `prefers-reduced-motion` — framer-motion's `AnimatePresence` handles this
automatically when `motion.div` is used. For manual checks, use `MOTION.reducedMotionEntry`.

---

## Component dependency matrix

| Component            | shadcn/ui                        | lucide-react           | Other            |
|----------------------|----------------------------------|------------------------|------------------|
| StatCard             | Card, CardContent, CardHeader, CardTitle | Any (caller-supplied) | — |
| SignalBadge          | Badge                            | —                      | — |
| CycleTimeline        | Card, Badge, Dialog, Tabs        | Clock, RefreshCw       | recharts via ui/chart |
| KBTable              | Card, Badge, Separator           | ShieldCheck            | — |
| KeyholeRow           | Card, Alert, AlertDescription, Badge | GitBranch, Server, ShieldCheck | — |
| AutonomyCockpitSkeleton | Skeleton                      | —                      | — |
