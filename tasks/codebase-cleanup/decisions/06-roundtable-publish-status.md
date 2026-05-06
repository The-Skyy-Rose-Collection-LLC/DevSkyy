# Finding #6 — Round Table Auto-Publishes WordPress Posts Without Review Gate

**Date:** 2026-05-06
**Severity:** HIGH (data integrity / unintended publication)
**Status:** INVESTIGATE ONLY — no code change made

---

## Location

`frontend/lib/autonomous/round-table-auto-trigger.ts` line 99–101

```typescript
// CRITICAL: Deploy as PUBLISHED post (not draft)
const response = await syncService.syncRoundTableResult(result, {
  status: 'publish', // Auto-publish winner
```

---

## Current Behavior

`deployWinnerToWordPressWithRetry()` unconditionally passes `status: 'publish'` to the WordPress
sync service. Every LLM Round Table competition winner is immediately live on the production
WordPress site (`skyyrose.co`) without any human review step. The in-code comment "CRITICAL: Deploy
as PUBLISHED post (not draft)" indicates this was an explicit intentional decision at the time of
writing, not an accident.

The trigger is wired into the autonomous pipeline: once the round table competition concludes and a
winner is scored, deployment is automatic and fires without user confirmation.

---

## Risk Assessment

- **Content risk:** AI-generated copy goes live before brand review. A hallucinated product detail
  or off-brand phrasing becomes customer-visible immediately.
- **WooCommerce coupling:** If `syncRoundTableResult` also creates/updates WooCommerce products
  (not confirmed — would require reading `lib/wordpress/sync-service.ts`), a bad run could corrupt
  live product listings.
- **No rollback gate:** Retry logic (`maxRetries`) retries the publish call on failure. A transient
  network error followed by a successful retry means the post exists in WordPress but may not be
  captured in `localStorage` sync history, making it harder to find and unpublish.

---

## Recommendation

Change `status: 'publish'` to `status: 'draft'` and add an explicit approval step before
promotion.

Suggested minimal change:

```typescript
const response = await syncService.syncRoundTableResult(result, {
  status: 'draft', // Human review required before publish
  title: `LLM Round Table Winner: ${result.prompt_preview.substring(0, 60)}`,
})
```

If the owner requires auto-publish for operational reasons, a middle-ground is to add a
configurable flag:

```typescript
const publishStatus = process.env.NEXT_PUBLIC_ROUNDTABLE_AUTO_PUBLISH === 'true'
  ? 'publish'
  : 'draft'
```

This keeps the current behavior when the env var is explicitly set and defaults to safe (draft)
in all other environments.

---

## Open Question for Owner

**Was the `status: 'publish'` intentional for production, or was it set for testing and never
reverted?**

The comment "CRITICAL: Deploy as PUBLISHED post (not draft)" implies an intentional design choice,
possibly driven by a workflow requirement (e.g., round table results feed a social content
calendar and must be live before a scheduled share). If that is the case, the risk is accepted and
this finding can be closed as WONTFIX with a comment explaining the operational reason.

If the intent was to auto-draft for later review, the fix is a one-line change.

---

## Files Examined

- `frontend/lib/autonomous/round-table-auto-trigger.ts` — confirmed `status: 'publish'` at line 101
- `frontend/lib/autonomous/CLAUDE.md` — no additional context
- Did NOT read `frontend/lib/wordpress/sync-service.ts` — WooCommerce coupling is unconfirmed;
  recommend reading it before implementing any fix.
