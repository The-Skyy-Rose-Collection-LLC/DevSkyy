/**
 * OAI render review data layer (server-only).
 *
 * Backs `/admin/renders/review` — the in-dashboard render approval queue. It
 * reads the same artifacts as the standalone board (`scripts/oai-render-review.py`,
 * the `:8944` server) and writes the SAME state file, so the two stay compatible:
 *
 *   renders/oai/<slug>/{ghost,ghost-back,on-model}.png   — the render images
 *   renders/oai/_review/review-state.json                — human annotations (TRACKED)
 *   renders/oai/_runs/*.jsonl                            — pipeline run logs (QC verdicts)
 *
 * Review (approve/flag/comment) is a REVERSIBLE annotation. It is NOT SOT
 * promotion — making an approved render the canonical product image is a separate,
 * irreversible CLI step (`stage_review.py` → `skyyrose.core.review.approve` →
 * `make sot-manifest`) surfaced read-only in the UI, never executed from here.
 *
 * Pure, unit-tested logic (segment guard, Python-parity serializer, verdict
 * parser) lives in `renders-pure.ts`; this module does the filesystem I/O.
 */
import 'server-only';

import fs from 'node:fs';
import path from 'node:path';

import { resolveRepoFile } from './catalog';
import {
  IMG_EXT,
  VIEW_ORDER,
  isSafeSegment,
  parseVerdicts,
  stableStringify,
  type ReviewEntry,
  type ReviewState,
  type VerdictRecord,
} from './renders-pure';

export { isSafeSegment };
export type { ReviewEntry, ReviewState, RenderVerdict } from './renders-pure';

const RENDERS_RELATIVE = path.join('renders', 'oai');

export interface RenderRecord {
  key: string; // `${slug}/${file}` — also the review-state.json key
  slug: string;
  file: string;
  view: string;
  sku: string | null;
  name: string | null;
  verdict: { passed: boolean; tags: string[]; reason: string } | null;
  review: ReviewEntry | null;
}

export interface RenderQueue {
  records: RenderRecord[];
  summary: {
    total: number;
    approved: number;
    flagged: number;
    pending: number;
    withVerdict: number;
  };
}

function rendersDir(): string {
  return resolveRepoFile(RENDERS_RELATIVE);
}

function reviewStatePath(): string {
  return path.join(rendersDir(), '_review', 'review-state.json');
}

/** Resolve a render image path under renders/oai, or null if unsafe/missing. */
export function resolveRenderImage(
  slug: string,
  file: string
): { path: string; contentType: string } | null {
  if (!isSafeSegment(slug) || !isSafeSegment(file)) return null;
  if (!IMG_EXT.test(file)) return null;

  const base = rendersDir();
  const lexical = path.resolve(base, slug, file);
  // Fast lexical containment pre-filter.
  if (lexical !== base && !lexical.startsWith(base + path.sep)) return null;

  // `path.resolve` is lexical and does NOT dereference symlinks, while statSync/
  // readFileSync DO — so a symlink under renders/oai could escape the base.
  // Canonicalize both the file and the base, then re-verify containment.
  let realBase: string;
  let real: string;
  let isFile: boolean;
  try {
    realBase = fs.realpathSync(base);
    real = fs.realpathSync(lexical);
    isFile = fs.statSync(real).isFile();
  } catch {
    return null;
  }
  if (real !== realBase && !real.startsWith(realBase + path.sep)) return null;
  if (!isFile) return null;

  const ext = path.extname(real).toLowerCase();
  const contentType =
    ext === '.png' ? 'image/png' : ext === '.webp' ? 'image/webp' : 'image/jpeg';
  return { path: real, contentType };
}

// ─── review-state.json (shared with the Python board) ────────────────────────

export function loadReviewState(): ReviewState {
  const p = reviewStatePath();
  if (!fs.existsSync(p)) return {};
  try {
    const value = JSON.parse(fs.readFileSync(p, 'utf-8')) as unknown;
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return value as ReviewState;
    }
    return {};
  } catch {
    return {};
  }
}

/**
 * Merge one annotation into review-state.json and persist atomically.
 * SYNCHRONOUS by design (no `await` between read and rename) so the single
 * threaded event loop runs it to completion without interleaving concurrent
 * requests; the unique temp name additionally guards cross-process collisions.
 */
export function saveReviewEntry(key: string, entry: ReviewEntry): ReviewState {
  const statePath = reviewStatePath();
  const dir = path.dirname(statePath);
  const state = loadReviewState();
  const next: ReviewState = { ...state, [key]: entry };
  const text = stableStringify(next); // Python json.dump adds no trailing newline

  fs.mkdirSync(dir, { recursive: true });
  const tmp = path.join(
    dir,
    `.review-state.${process.pid}.${Date.now()}.${Math.random().toString(36).slice(2)}.tmp`
  );
  try {
    fs.writeFileSync(tmp, text, 'utf-8');
    fs.renameSync(tmp, statePath);
  } catch (err) {
    try {
      if (fs.existsSync(tmp)) fs.unlinkSync(tmp);
    } catch {
      /* ignore cleanup failure */
    }
    throw err;
  }
  return next;
}

// ─── QC verdicts (best-effort parse of run logs) ─────────────────────────────

function loadVerdicts(): Record<string, VerdictRecord> {
  const runsDir = path.join(rendersDir(), '_runs');
  let files: string[];
  try {
    files = fs.readdirSync(runsDir).filter((f) => f.endsWith('.jsonl'));
  } catch {
    return {};
  }
  const map: Record<string, VerdictRecord> = {};
  for (const fileName of files) {
    try {
      const text = fs.readFileSync(path.join(runsDir, fileName), 'utf-8');
      parseVerdicts(text, map);
    } catch {
      /* skip an unreadable run file */
    }
  }
  return map;
}

// ─── Listing + join ──────────────────────────────────────────────────────────

function listRenderFiles(): Array<{ slug: string; file: string }> {
  const base = rendersDir();
  const out: Array<{ slug: string; file: string }> = [];
  let slugs: string[];
  try {
    slugs = fs.readdirSync(base);
  } catch {
    return out;
  }
  for (const slug of slugs) {
    if (slug.startsWith('_')) continue;
    const dir = path.join(base, slug);
    try {
      if (!fs.statSync(dir).isDirectory()) continue;
      for (const file of fs.readdirSync(dir)) {
        if (!IMG_EXT.test(file)) continue;
        if (fs.statSync(path.join(dir, file)).isFile()) out.push({ slug, file });
      }
    } catch {
      /* skip an unreadable slug dir */
    }
  }
  return out;
}

export function getRenderQueue(): RenderQueue {
  const state = loadReviewState();
  const verdicts = loadVerdicts();

  const records: RenderRecord[] = listRenderFiles().map(({ slug, file }) => {
    const key = `${slug}/${file}`;
    const v = verdicts[key] ?? null;
    return {
      key,
      slug,
      file,
      view: file.replace(IMG_EXT, ''),
      sku: v?.sku ?? null,
      name: v?.name ?? null,
      verdict: v ? { passed: v.passed, tags: v.tags, reason: v.reason } : null,
      review: state[key] ?? null,
    };
  });

  records.sort(
    (a, b) =>
      a.slug.localeCompare(b.slug) ||
      (VIEW_ORDER[a.file] ?? 9) - (VIEW_ORDER[b.file] ?? 9) ||
      a.file.localeCompare(b.file)
  );

  return {
    records,
    summary: {
      total: records.length,
      approved: records.filter((r) => r.review?.approved).length,
      flagged: records.filter((r) => r.review?.flagged).length,
      pending: records.filter((r) => !r.review || (!r.review.approved && !r.review.flagged)).length,
      withVerdict: records.filter((r) => r.verdict).length,
    },
  };
}
