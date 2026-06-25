/**
 * PURE render-review helpers — no `node:fs`, no `server-only`, no `@/` aliases.
 *
 * Holds the security-critical segment guard, the Python-parity JSON serializer,
 * and the QC-verdict log parser so each can be unit-tested under bare `tsx`.
 * The server module (`renders.ts`) does the filesystem I/O around these.
 */

export const IMG_EXT = /\.(png|webp|jpe?g)$/i;

export const VIEW_ORDER: Record<string, number> = {
  'ghost.png': 0,
  'ghost-back.png': 1,
  'on-model.png': 2,
};

export interface ReviewEntry {
  approved: boolean;
  comment: string;
  flagged: boolean;
  updated: string;
}

export type ReviewState = Record<string, ReviewEntry>;

export interface RenderVerdict {
  passed: boolean;
  tags: string[];
  reason: string;
}

export interface VerdictRecord extends RenderVerdict {
  sku: string | null;
  name: string | null;
  ts: number;
}

// ─── Path-safety ────────────────────────────────────────────────────────────
// A per-segment charclass alone is NOT a traversal guard: `..` matches
// /^[A-Za-z0-9_.-]+$/. Reject `.`/`..`/separators explicitly; the server side
// additionally verifies containment after resolving.

export function isSafeSegment(segment: string): boolean {
  if (segment === '' || segment === '.' || segment === '..') return false;
  if (segment.includes('/') || segment.includes('\\') || segment.includes('\0')) return false;
  return /^[A-Za-z0-9_.-]+$/.test(segment);
}

// ─── Python-parity JSON ──────────────────────────────────────────────────────

/**
 * Serialize exactly like Python's `json.dump(obj, indent=2, sort_keys=True,
 * ensure_ascii=True)` — sorted keys at every level, 2-space indent, `\uXXXX`
 * escaping for non-ASCII — so the tracked `review-state.json` does not
 * churn-diff when the Next dashboard and the `:8944` Python board alternate.
 */
export function stableStringify(value: unknown): string {
  return pyDump(value, 0);
}

function pyDump(value: unknown, level: number): string {
  const pad = '  '.repeat(level + 1);
  const padEnd = '  '.repeat(level);
  if (value === null || value === undefined) return 'null';
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : 'null';
  if (typeof value === 'string') return pyEscapeString(value);
  if (Array.isArray(value)) {
    if (value.length === 0) return '[]';
    const items = value.map((v) => pad + pyDump(v, level + 1));
    return `[\n${items.join(',\n')}\n${padEnd}]`;
  }
  if (typeof value === 'object') {
    const keys = Object.keys(value as Record<string, unknown>).sort();
    if (keys.length === 0) return '{}';
    const items = keys.map(
      (k) => `${pad}${pyEscapeString(k)}: ${pyDump((value as Record<string, unknown>)[k], level + 1)}`
    );
    return `{\n${items.join(',\n')}\n${padEnd}}`;
  }
  return 'null';
}

function pyEscapeString(s: string): string {
  let out = '"';
  for (const ch of s) {
    const code = ch.codePointAt(0) ?? 0;
    if (ch === '"') out += '\\"';
    else if (ch === '\\') out += '\\\\';
    else if (ch === '\n') out += '\\n';
    else if (ch === '\r') out += '\\r';
    else if (ch === '\t') out += '\\t';
    else if (ch === '\b') out += '\\b';
    else if (ch === '\f') out += '\\f';
    else if (code < 0x20 || code > 0x7e) {
      if (code > 0xffff) {
        const c = code - 0x10000;
        const hi = 0xd800 + (c >> 10);
        const lo = 0xdc00 + (c & 0x3ff);
        out += `\\u${hi.toString(16).padStart(4, '0')}\\u${lo.toString(16).padStart(4, '0')}`;
      } else {
        out += `\\u${code.toString(16).padStart(4, '0')}`;
      }
    } else {
      out += ch;
    }
  }
  return `${out}"`;
}

// ─── QC verdict log parsing ──────────────────────────────────────────────────

/**
 * Parse OAI run JSONL text into a `${slug}/${file}` → verdict map by correlating
 * the per-attempt event chain (`attempt` → `qc_verdict` → `accepted`). Latest ts
 * wins. Best-effort: a malformed line is skipped, never thrown. `mergeInto` lets
 * the caller accumulate across multiple run files.
 */
export function parseVerdicts(
  text: string,
  mergeInto: Record<string, VerdictRecord> = {}
): Record<string, VerdictRecord> {
  const map = mergeInto;
  const ctx: Record<string, Partial<VerdictRecord> & { ts?: number }> = {};
  // Attempt-agnostic fallback: latest verdict per (sku, slug). Used when the
  // `accepted` event's attempt index doesn't line up with the `qc_verdict`'s
  // (producer drift) so a real verdict still attaches instead of degrading to
  // "no QC record".
  const lastBySkuSlug: Record<string, Partial<VerdictRecord> & { ts?: number }> = {};

  for (const rawLine of text.split('\n')) {
    const line = rawLine.trim();
    if (!line) continue;
    let d: Record<string, unknown>;
    try {
      d = JSON.parse(line) as Record<string, unknown>;
    } catch {
      continue;
    }
    const event = d.event;
    const ctxKey = `${d.sku}|${d.slug}|${d.attempt}`;
    const skuSlug = `${d.sku}|${d.slug}`;

    if (event === 'attempt') {
      ctx[ctxKey] = {
        ...ctx[ctxKey],
        sku: typeof d.sku === 'string' ? d.sku : null,
        name: typeof d.name === 'string' ? d.name : null,
      };
    } else if (event === 'qc_verdict') {
      const verdict = {
        passed: Boolean(d.passed),
        tags: Array.isArray(d.tags) ? (d.tags as string[]) : [],
        reason: typeof d.reason === 'string' ? d.reason : '',
        ts: typeof d.ts === 'number' ? d.ts : 0,
      };
      ctx[ctxKey] = { ...ctx[ctxKey], ...verdict };
      lastBySkuSlug[skuSlug] = verdict;
    } else if (event === 'accepted') {
      const exact = ctx[ctxKey] ?? {};
      // Prefer the exact-attempt context; if it carries no verdict, fall back to
      // the latest verdict seen for this (sku, slug).
      const c = exact.passed !== undefined ? exact : { ...exact, ...(lastBySkuSlug[skuSlug] ?? {}) };
      const p = typeof d.path === 'string' ? d.path : '';
      const parts = p.split(/[/\\]/);
      const file = parts[parts.length - 1];
      const slug = parts[parts.length - 2];
      if (!file || !slug) continue;
      const mapKey = `${slug}/${file}`;
      const ts = typeof d.ts === 'number' ? d.ts : (c.ts ?? 0);
      if (!map[mapKey] || ts >= map[mapKey].ts) {
        map[mapKey] = {
          passed: c.passed ?? false,
          tags: c.tags ?? [],
          reason: c.reason ?? '',
          sku: c.sku ?? (typeof d.sku === 'string' ? d.sku : null),
          name: c.name ?? null,
          ts,
        };
      }
    }
  }
  return map;
}
