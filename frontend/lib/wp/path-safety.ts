/**
 * Framework-free path guards for the WP client. Kept out of client.ts (which is
 * `server-only`) so they are unit-testable in isolation, mirroring auth-policy.ts.
 */

/**
 * Reject a path containing a `..` (or `\..`) segment. fetch() collapses `..` per
 * WHATWG URL rules AFTER the auth tier is chosen from the raw path, so a
 * traversal could carry one tier's credentials to a different endpoint. Guarding
 * the shared primitive stops every caller — present and future — from smuggling
 * one through.
 */
export function assertNoTraversal(path: string): void {
  if (path.split(/[/\\]/).some((segment) => segment === '..')) {
    throw new Error(`buildUrl: path traversal segment rejected in "${path}"`);
  }
}

/**
 * Coerce a resource id to a strict non-negative integer. TS `number` typing is
 * erased at runtime; a dynamic route param arrives as a string and would flow
 * straight into the path, so callers that interpolate an id must validate it.
 */
export function requireInt(value: number | string, label: string): number {
  const n = typeof value === 'number' ? value : Number(value);
  if (!Number.isInteger(n) || n < 0) {
    throw new Error(`Invalid ${label}: expected a non-negative integer`);
  }
  return n;
}
