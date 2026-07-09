---
name: autonomous-issue-diagnose-fix
description: Diagnose and fix a WordPress/theme issue that resists a single-shot patch, by running parallel independent fix hypotheses through adversarial verification instead of trusting one agent's self-graded "fixed it." Use for regressions escalated by self-healing-theme-loop (recurrences >= 2, or root cause genuinely uncertain), or any skyyrose.co bug where a first fix attempt didn't hold up under independent re-check. Not for routine, known-signature regressions -- theme-heal-doctor's single-shot path handles those; this is the harder-issue tier.
---

# Autonomous Issue Diagnose-Fix (Escalation Tier)

Generalizes the diagnose → parallel-fix-attempts → adversarial-verify → revise pattern
proven on the mascot skin-weight investigation (bug-198, 2026-07-09) into a reusable
template for any hard skyyrose.co web/theme issue. Composes with
[adversarial-verification](../../../../../.claude/skills/adversarial-verification/SKILL.md)
(the general pattern) and slots into the existing
[self-healing-theme-loop contract](../../../../../docs/superpowers/specs/self-healing-theme-loop.html)
as the response to escalation, replacing "give up and surface to founder" with "try
harder, with a fundamentally different method, before giving up."

## When to use this vs. theme-heal-doctor's single-shot path

| Situation | Use |
|---|---|
| Known regression signature in `heal-knowledge.json`, proven `fixPattern` exists | `theme-heal-doctor` single-shot, per the existing loop |
| First fix attempt healed + passed the two-axis gate | Done, no escalation needed |
| Regression recurred (`recurrences >= 2`) -- symptom-patching, not root-caused | **This skill** |
| Root cause genuinely uncertain -- more than one plausible explanation, single-agent diagnosis keeps guessing wrong | **This skill** |
| A fix "looks right" on self-report but you don't fully trust it | **This skill**'s verify stage alone (see below), even without the parallel-build fan-out |

## The pattern (Workflow shape)

```
Diagnose  (one agent, thorough -- re-derive root cause with hard evidence, not
           the prior cycle's guess. Cache-busted curl + source grep + PHPCS/php -l
           as applicable, per theme-heal-doctor's existing verification methods)
   |
Fix Attempts  (N independent agents, each a genuinely DIFFERENT hypothesis/approach
               -- not the same fix with different code style. pipeline(), not a
               barrier, so each verifies as soon as it's built)
   |
Verify  (a SEPARATE agent per candidate, independently re-derives evidence --
         re-curl, re-grep, re-run phpcs/php -l, re-screenshot via Playwright if
         visual -- never trusts the builder's self-report. Skeptical default:
         "still broken" unless clearly proven otherwise. Structured verdict enum.)
   |
Synthesis  (barrier: compare all verdicts, pick the one that's actually clean,
            or say none qualify and hand back to the founder with what was
            tried and why each failed -- per bug-198's honest "none shipped"
            outcome, this is a legitimate, valuable result, not a failure of
            the process)
   |
[optional] Revise  (only if nothing passed: one more attempt per the winning
                     verifier's SPECIFIC feedback, then re-verify once more.
                     Cap at 1 revision round -- if that also fails, stop and
                     report, don't spiral)
```

## Adapting for WordPress/theme issues specifically (not the 3D-specific details)

Reuse the project's existing web-verification idioms, not generic ones:

- **Reproduce against live + source**, exactly as `theme-heal-doctor` already does:
  cache-busted curl (`?cb=$(date +%s)`), never `WebFetch` for `<script>`/JSON-LD/inline
  JS (it strips them). Grep the worktree for the expected pattern.
- **Isolation**: each fix-attempt agent works in its own git worktree (or at minimum its
  own branch) so N parallel attempts never collide on the same files -- same principle as
  this session's `mascot-skin-weight-fix` worktree, applied to theme code.
  `isolation: 'worktree'` on `agent()` calls handles this if fan-out attempts touch the
  same files; skip it if attempts are naturally non-colliding (e.g. read-only diagnosis).
- **Gates are non-negotiable per candidate, before verify even starts**: `php -l` on
  touched PHP, PHPCS (`--standard=.phpcs.xml --error-severity=5`), and — if the fix
  touches CSS/JS — a rebuilt `.min` (`node scripts/build-css.js && build-js.js`). A
  candidate that fails these doesn't reach the verify stage; that's wasted verifier work.
- **Visual regressions**: verify stage uses Playwright/chrome-devtools MCP for
  screenshot + pixel comparison, the same rigor this session used for the mascot's
  render-and-pixel-diff checks — never "looks fine" from a single screenshot glance.
- **Bounded scope, same as `theme-heal-doctor`**: every fix-attempt agent gets the same
  "no sprawling refactors, touch only the implicated surface" constraint. Parallel
  hypotheses about ROOT CAUSE are the point of fanning out — parallel scope creep is not.
- **STOP-AND-SHOW still applies**: this skill produces a healed worktree + verified
  report. It does NOT deploy, commit, bump `SKYYROSE_VERSION`, or touch
  `.claude/settings.json` — identical boundary to `theme-heal-doctor`'s own safety rules.
  Package/compress if applicable; deploy is always a separate, explicitly-confirmed step.

## Verdict schema (forces honesty, mirrors adversarial-verification's requirement)

```js
const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    overall_verdict: { type: 'string', enum: ['clean', 'partially-improved', 'no-improvement', 'regressed'] },
    axis_heals: { type: 'boolean' },        // does it resolve the detected regression?
    axis_net_improvement: { type: 'boolean' }, // root cause removed, not just patched?
    gate_php_lint: { type: 'boolean' },
    gate_phpcs: { type: 'boolean' },
    recommend_ship: { type: 'boolean' },
    specific_feedback_for_revision: { type: 'string' },
  },
  required: ['overall_verdict', 'axis_heals', 'axis_net_improvement', 'recommend_ship'],
}
```

Both `axis_heals` and `axis_net_improvement` must be true for `recommend_ship: true` --
this is the existing spec's "Heal vs Improve — Two-Axis Review Gate" made concrete and
independently checked, instead of self-graded by the same agent that wrote the fix.

## Honest "none shipped" is a valid, valuable outcome

The mascot investigation's real result was proving three plausible approaches all failed,
converging independently on a precise, evidence-backed root cause (LBS candy-wrapper
collapse) and a specific recommended next technique -- not a shipped fix. Don't force
synthesis to pick a loser just to have a deliverable. Report which hypotheses were
disproven, why (with evidence), and what to try next. That's a complete, honest cycle,
and it's exactly what prevents the same wrong hypothesis from being re-tried next cycle
(the whole point of `heal-knowledge.json`'s learning model).

## Relationship to the (currently unbuilt) self-healing-theme-loop engine

The loop's spec already calls for a "Two-Axis Review Gate" after `theme-heal-doctor`
produces a candidate, and an escalation path after 2 failed cycles. When the engine
(`self-healing-theme-loop.js`, not yet built as of 2026-07-09) is implemented, wire it so:

- Every `theme-heal-doctor` candidate goes through an **independent** verifier (see the
  companion `theme-heal-verifier` agent), not self-grading -- this alone strengthens every
  routine cycle, no fan-out needed.
- On escalation (`recurrences >= 2`) or explicit hard-issue flagging, invoke this skill's
  parallel-hypothesis pattern **once** before setting `lastOutcome: "escalated"` and
  surfacing to the founder. If this also fails to produce a clean, independently-verified
  candidate, escalate as the spec already defines -- don't loop forever.
