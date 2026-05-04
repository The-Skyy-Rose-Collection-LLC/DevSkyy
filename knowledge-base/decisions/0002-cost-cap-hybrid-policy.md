---
adr_id: "0002"
title: "Cost-Cap Hybrid Policy — When to STOP-AND-SHOW vs Proceed Autonomously"
status: accepted
date: 2026-05-03
deciders: "Corey Foster (founder), DevSkyy engineering agent"
context: |
  The V2 build involves multiple paid AI APIs (FASHN virtual try-on, Gemini image generation, Anthropic
  synthesis, AIDesigner, Pinecone, Voyage). Without a clear policy, the engineering agent faces two failure
  modes:

  1. Over-asking: pausing before every API call, even trivial ones, destroying autonomy and flow.
  2. Under-asking: running batch generation jobs autonomously, producing unexpected charges.

  The V2 Master Plan §1.3 defined per-API cost thresholds, but these were subsequently superseded by a
  more detailed policy document at eval/cost-cap-policy.md. That document is the operative specification.
  This ADR explains why Option C (hybrid: threshold-based stop vs autonomous) was chosen over the two
  alternatives.
decision: |
  Option C (hybrid threshold policy) is adopted. The single operative rule is:

    Any single API call estimated >$1 → STOP-AND-SHOW with manifest and wait for "y" or "yes".
    Any single API call estimated ≤$1 → autonomous, up to per-session thresholds.

  The per-session autonomous thresholds are:
    - Anthropic inference: $25 total
    - AIDesigner generations: 50 total
    - FASHN calls: 30 total
    - Pinecone operations: $10 total

  When a threshold is approached (>80% consumed), the engineering agent logs a warning and asks before
  the next call in that category. When a threshold is exceeded, all further calls in that category require
  explicit confirmation regardless of individual call cost.

  The operative document is eval/cost-cap-policy.md. This ADR is a pointer and rationale record only —
  if eval/cost-cap-policy.md and this ADR conflict, eval/cost-cap-policy.md wins.
consequences:
  positive:
    - Eliminates surprise charges for batch runs (the highest-risk failure mode)
    - Preserves autonomy for the majority of API calls (Anthropic synthesis, Pinecone queries, Voyage embeddings)
    - Provides a clear, mechanical rule — no judgment calls required
    - STOP-AND-SHOW manifest format makes cost visible and auditable
  negative:
    - Any FASHN call, Gemini image batch, or FLUX run requires a manual confirmation step
    - The $1 threshold may feel low for experienced users — but the asymmetry is intentional (false positives are cheap, false negatives are expensive)
  neutral:
    - Silent paid MCP calls (tools that internally call paid APIs without surfacing cost) are treated as if they were >$1 — confirm before use
    - Unknown-cost calls are treated as >$1 until the actual cost is determined
alternatives_considered:
  - title: "Option A — Always autonomous, post-hoc reporting"
    rejected_because: "Produced unexpected charges in earlier sessions. A single misfire on a 33-SKU FASHN batch is $40+ with no recourse."
  - title: "Option B — Always confirm, every API call"
    rejected_because: "Destroys flow for the majority of calls (Anthropic synthesis, Pinecone, Voyage) that cost fractions of a cent. Creates confirmation fatigue that leads to rubber-stamping."
related_decisions:
  - "[adr: 0001]"
cross_refs:
  - "[v2: §1.3]"
  - "[serena: user_expectations]"
  - "[serena: production_audit_findings]"
---

# Cost-Cap Hybrid Policy

## The Rule (Single Sentence)

If a single API call costs more than $1, stop and show the manifest before proceeding.

## Operative Document

`/Users/theceo/DevSkyy/eval/cost-cap-policy.md` — read this before any batch generation work. This ADR
is a rationale record; that file is the implementation spec.

## STOP-AND-SHOW Manifest Format

```
STOP — Confirm before proceeding:

Action   : <API name + operation>
SKU(s)   : <list or "all 33">
Source   : /path/to/exact/input/file  (<size>, <date>)
Est. cost: ~$<N.NN>  (<breakdown: N calls × $X each>)

Proceed? [y/N]
```

The manifest must show the exact file path, exact cost estimate, and exact action — not a summary. The
word "approximately" is not sufficient; show the arithmetic.

## Per-API Classification

| API | Classification | Threshold note |
|-----|---------------|----------------|
| FASHN tryon / product-to-model | STOP-AND-SHOW (always) | Even a single call is ~$0.075; batches cross $1 at 14+ calls |
| AIDesigner generations | STOP-AND-SHOW (always) | Per-gen cost unknown — treat as >$1 until confirmed |
| Gemini image generation batches | STOP-AND-SHOW (always) | Batch cost varies; individual calls may be <$1 but batches are not |
| FLUX (any variant) | STOP-AND-SHOW (always) | GPU cost per image is variable and can spike |
| GPT-Image-1 / DALL-E | STOP-AND-SHOW (always) | $0.04–$0.12 per image; 33-SKU batch = $1.32–$3.96 |
| Anthropic synthesis (claude-*) | Autonomous ≤$25/session | Token cost is predictable; typical synthesis call is $0.01–$0.10 |
| Pinecone operations | Autonomous ≤$10/session | Query/upsert cost is near-zero at catalog scale |
| Voyage embeddings | Autonomous ≤$5/session | Per-token cost is negligible at catalog scale |
| Context7 / MCP lookup tools | Autonomous (no cost) | These are free read operations |

## Edge Cases

**Batched calls:** A loop that makes 10 calls at $0.08 each = $0.80 total. This is below the $1 per-call
threshold. However, if the loop is parameterized by the full SKU list (33 SKUs), the total is $2.64 and
requires a STOP-AND-SHOW before the loop starts — evaluate the batch, not the individual call.

**Unknown cost:** If the cost of an API call cannot be determined (new provider, unpublished pricing, or
a silent MCP tool), treat it as >$1 and require confirmation. "I don't know" is not a reason to proceed
autonomously.

**Threshold approach:** At 80% of a per-session threshold (e.g., $20 of the $25 Anthropic budget), log a
warning in the task output. At 100%, halt and confirm before any further calls in that category.

**Silent paid MCP calls:** Some MCP tools internally invoke paid APIs without surfacing the cost in the
tool call. Until a tool's cost behavior is confirmed, treat it as STOP-AND-SHOW.

## Why Option C Over the Alternatives

**Option A (always autonomous):** The failure mode is a 33-SKU FASHN batch firing without confirmation —
$40+ charge, no undo. This happened at least once before this policy was adopted. The asymmetry of harms
makes full autonomy unacceptable for paid generation APIs.

**Option B (always confirm):** Destroys the value of autonomous operation. A Pinecone query costs $0.0001.
Requiring confirmation for every such call creates confirmation fatigue that leads to rubber-stamping — the
opposite of a useful safeguard. The policy must be discriminating to be respected.

**Option C (hybrid):** The $1 threshold is deliberately conservative. A STOP-AND-SHOW for a $1.20 FASHN
batch costs one prompt. Skipping the confirmation on a $45 batch costs real money. The asymmetry is
intentional — the policy trades occasional unnecessary confirmations for reliable protection against
large unexpected charges.
