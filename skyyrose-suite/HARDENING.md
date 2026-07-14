# SkyyRose Suite — Hardening Skills

17 skills added to strengthen the suite and close gaps that map directly to this
project's recurring buglog patterns and hard-won lessons. Skills **auto-discover** from
each plugin's `skills/` dir. Every new skill follows one standard so the team produces
production-quality work in any prompt scheme:

- **Loop** — a bounded do → check → fix cycle (≤5, stop on repeat), the [[drive-to-green]] shape.
- **Verify from an authoritative source** — a check that can actually FAIL (run+read, source
  `file:line`, eyes-on pixels, `pip check`, cache-busted curl) — never "looks correct".
- **Adversarial pass** — [[adversarial-planning]] before, [[adversarial-verification]] after.

## New skills by pod

### skyyrose-qa — quality & verification
| Skill | Fills gap / grounded in |
|-------|-------------------------|
| `fail-closed-audit` | bug-230 (×6) fail-open gates — absent input must BLOCK, never pass |
| `mutation-testing` | test falsifiability — a test that survives a mutation tested nothing |
| `test-isolation` | bug-231 (×4) shared state + bug-257 sparse-worktree gating |
| `self-healing` | detect → root-cause → fix → **independent** re-verify (theme-heal-verifier pattern) |
| `adversarial-verification` | imported — refute "the fix worked" before trusting it |

### skyyrose-core — engineering
| Skill | Fills gap / grounded in |
|-------|-------------------------|
| `dependency-hygiene` | bug-254 undeclared litellm + silent `openai` major drift; `pip check` clean |
| `worktree-git-discipline` | shared-worktree: never amend/reset/rebase another session's HEAD |
| `lsp-code-intelligence` | use the wired pyright/vtsls/bash LSP servers over grep guessing |
| `prompt-engineering` | technique matrix subordinate to anti-hallucination + verification |
| `memory-system` | read OpenWolf + claude-mem before acting, write lessons after |
| `self-learning` | every correction/fix → durable cerebrum + buglog entry |
| `boris-mind` | parallelize (worktrees/subagents), plan-first, verify-always posture |
| `source-of-truth` | resolve product/imagery/brand facts from SOT.md canon, never memory (lh-005) |
| `adversarial-planning` | imported — a different model (Codex) challenges the plan first |

### skyyrose-design — design & storefront
| Skill | Fills gap / grounded in |
|-------|-------------------------|
| `product-image-fidelity-gate` | #1 recurring defect — eyes-on SKU↔garment pixel check |
| `theme-min-build` | prod serves `.min`; every CSS/JS edit rebuilds + re-verifies both |

### skyyrose (orchestrator)
| Skill | Fills gap / grounded in |
|-------|-------------------------|
| `cost-governance-gate` | STOP-AND-SHOW before money / production / irreversible actions |

## Composes with existing suite skills

`drive-to-green`, `verification-loop`, `verification-before-completion`, `critique`,
`continuous-learning` / `continuous-learning-v2`, `efficient-production`,
`token-aware-behavior`, `strategic-compact`, and the per-pod `*-dispatch` handoff routers —
referenced via `[[name]]` links so the hardening layer plugs into what was already here.
