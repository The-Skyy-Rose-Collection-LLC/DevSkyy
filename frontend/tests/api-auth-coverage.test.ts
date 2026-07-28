/**
 * Fail-closed coverage gate for dashboard API authentication.
 *
 * The removed proxy.ts gated /api/* with an exclusion matcher, so a new route
 * was protected the moment it existed. Per-handler auth loses that property:
 * a new route is open until someone remembers to wrap it. This test restores
 * it by enumerating the filesystem rather than a hand-maintained list — adding
 * an unwrapped handler fails the suite instead of shipping an open endpoint.
 *
 * Deliberately source-level, not runtime: a runtime probe needs a server, a
 * session, and env, and it skips (green) when any of those are missing. That
 * is the fail-open shape this file exists to prevent.
 */

import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

import { describe, expect, it } from 'vitest';

import { PUBLIC_API_ROUTES } from '@/lib/api-auth';

const API_ROOT = join(__dirname, '..', 'app', 'api');

/** Next.js App Router recognises exactly these as route handlers. */
const HTTP_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'] as const;

function findRouteFiles(dir: string): string[] {
  const found: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      found.push(...findRouteFiles(full));
    } else if (entry === 'route.ts' || entry === 'route.tsx') {
      found.push(full);
    }
  }
  return found;
}

/** app/api/social-media/publish/route.ts -> 'social-media/publish' */
function routePath(file: string): string {
  return relative(API_ROOT, file).split(sep).slice(0, -1).join('/');
}

/**
 * Strip comments before scanning. A commented-out `export async function GET`
 * is not a route, and a line-oriented grep would count it — the same defect
 * that made the theme's img-alt gate report 72 phantom failures. Block
 * comments go first: a `//` inside one is not a line comment.
 */
function stripComments(src: string): string {
  return src.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/^[ \t]*\/\/.*$/gm, ' ');
}

/** Exported HTTP handlers, and whether each is wrapped in withAuth(). */
function exportedHandlers(src: string): Array<{ method: string; wrapped: boolean }> {
  const clean = stripComments(src);
  const handlers: Array<{ method: string; wrapped: boolean }> = [];

  for (const method of HTTP_METHODS) {
    // export const GET = withAuth(...)  — the only accepted gated form.
    if (new RegExp(`export\\s+const\\s+${method}\\s*=\\s*withAuth\\s*\\(`).test(clean)) {
      handlers.push({ method, wrapped: true });
      continue;
    }
    // Any other export of this name: bare function, bare const, or re-export.
    const bare = new RegExp(
      `export\\s+(?:async\\s+)?function\\s+${method}\\b` +
        `|export\\s+const\\s+${method}\\s*[:=]` +
        `|export\\s*\\{[^}]*\\bas\\s+${method}\\b`,
    );
    if (bare.test(clean)) {
      handlers.push({ method, wrapped: false });
    }
  }

  return handlers;
}

const routeFiles = findRouteFiles(API_ROOT);

describe('dashboard API auth coverage', () => {
  it('finds route handlers to check', () => {
    // Guards against a silent pass if API_ROOT is ever wrong or moved.
    expect(routeFiles.length).toBeGreaterThan(20);
  });

  it.each(routeFiles.map((f) => [routePath(f), f]))(
    '/api/%s gates every exported handler',
    (route, file) => {
      const src = readFileSync(file, 'utf-8');
      const handlers = exportedHandlers(src);

      expect(handlers.length, `no exported HTTP handler found in ${route}/route.ts`).toBeGreaterThan(
        0,
      );

      if (PUBLIC_API_ROUTES.includes(route)) {
        return; // Deliberately public — rationale lives in lib/api-auth.ts.
      }

      const open = handlers.filter((h) => !h.wrapped).map((h) => h.method);
      expect(
        open,
        `/api/${route} exports ${open.join(', ')} without withAuth(). ` +
          'Wrap it, or add the route to PUBLIC_API_ROUTES with a written reason.',
      ).toEqual([]);
    },
  );

  it('every PUBLIC_API_ROUTES entry names a real route', () => {
    const actual = new Set(routeFiles.map(routePath));
    const stale = PUBLIC_API_ROUTES.filter((r) => !actual.has(r));
    // A stale exemption is how a deleted-and-recreated route silently returns
    // ungated: the name still matches, but nobody re-reviewed the reason.
    expect(stale, `PUBLIC_API_ROUTES lists routes that do not exist: ${stale.join(', ')}`).toEqual(
      [],
    );
  });
});
