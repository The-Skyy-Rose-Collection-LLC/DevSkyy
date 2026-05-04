---
name: Cost-Cap Policy (Skyyrose V2 Build)
specified_by: [v2: §1.3], [claude_md: STOP-AND-SHOW], [grill: Branch 1 Option C]
phase: 0
last_updated: 2026-05-03
last_updated_by: eval-harness (Phase 0 grill resolution)
authority: This file supersedes both `CLAUDE.md` §STOP-AND-SHOW and `docs/SKYYROSE_V2_MASTER_PLAN.md` §1.3 when they conflict. Both source rules remain valid as inputs; the synthesis below is the binding contract.
---

# Cost-Cap Policy (Skyyrose V2 Build)

**Status:** Active. Supersedes both `CLAUDE.md` § "STOP AND SHOW" and `SKYYROSE_V2_MASTER_PLAN.md` §1.3 in isolation. The two rules conflicted; this document is the synthesis.

**Decision context:** Phase 0 grill, Branch 1, Option C (hybrid stance). Approved by Corey on 2026-05-03.

---

## The rule (in one sentence)

> **Any single paid API call estimated to cost > $1 → STOP-AND-SHOW (manifest + cost preview + explicit "y"). Any call ≤ $1 → autonomous up to per-service threshold from V2 §1.3.**

---

## Why both halves are needed

`CLAUDE.md` STOP-AND-SHOW exists because of a specific class of mistake: a wrong source file gets dispatched to FASHN, FLUX, or AIDesigner and burns a real dollar silently. The user can't get that money back, and worse, the wrong output may then be uploaded somewhere, embedded in a render, or used as input to another paid call. STOP-AND-SHOW catches the mistake before the dollar leaves.

V2 §1.3 thresholds exist because Phase 4 thinking passes (8-12 sessions of luxury reference triangulation, 5-pass thinking-pass synthesis, persona walkthroughs) shouldn't fragment Corey's day with 50-100 approval prompts. Anthropic synthesis at $0.10-0.50 per pass doesn't have the same blast radius as a $1.20 FASHN tryon — getting it wrong wastes a few cents, not a few dollars.

This policy honors both motivations by drawing the line at $1 per call.

---

## Per-API enumeration

Every paid endpoint touched in this V2 build, with measured/estimated per-call cost and policy side.

### STOP-AND-SHOW (>$1 per call OR high blast radius)

| API / endpoint | Per-call cost | Policy | Notes |
|----------------|---------------|--------|-------|
| **FASHN /tryon** | $0.30–$1.20 (varies with model count + sample count) | STOP-AND-SHOW | Multi-model runs aggregate; safer to treat all FASHN dispatches as STOP-AND-SHOW. Multi-model (4 models × 4 samples × $0.075) hits $1.20. |
| **FASHN /product-to-model** | ~$0.30 | STOP-AND-SHOW | Same reasoning — wrong source image burns silently. |
| **FASHN /edit, /model-create, /image-to-video** | varies, treat as ≥$1 | STOP-AND-SHOW | Same. |
| **AIDesigner generations** | varies (credits-based) | STOP-AND-SHOW | Each generation consumes a credit; daily cap is 50 per V2 §1.3. |
| **Gemini 3 Pro image generation** (`gemini-3-pro-image-preview`) | ~$0.04 per image but typically batched 4–10 → $0.40–$1.00 | STOP-AND-SHOW for batches; ≤$1 single-image autonomous | Compositor 6-stage uses this in stage 4 + 6. |
| **GPT-Image-1.5** | ~$0.07–$0.20 per image, often batched | STOP-AND-SHOW for batches | |
| **FLUX 2 Pro / FLUX 1.1 Pro / FLUX Kontext** | ~$0.05–$0.16 per image | STOP-AND-SHOW for batches; autonomous singles | |
| **HuggingFace paid Spaces** (FLUX upscaler, etc.) | varies | STOP-AND-SHOW | Compute cost depends on Space; manifest should include estimated GPU time. |
| **WC/WP write to live skyyrose.co** | $0 monetary, but high blast radius | STOP-AND-SHOW | Modifying live products, orders, posts requires manifest + confirmation. Read-only is autonomous. |
| **WordPress Media Library upload** | $0 monetary, high blast radius | STOP-AND-SHOW | Uploads land in production; STOP-AND-SHOW per CLAUDE.md retains. |

### Autonomous (≤$1 per call, low individual blast radius)

| API / endpoint | Per-call cost | Policy | Threshold (V2 §1.3) |
|----------------|---------------|--------|---------------------|
| **Anthropic Sonnet 4.6** synthesis (thinking-pass) | ~$0.10–$0.50 | Autonomous | Build-cap **$25 total** → G3 escalation at threshold |
| **Anthropic Opus 4.7** synthesis (deep reasoning) | ~$0.50–$2.00 (depends on context size) | Autonomous if estimated <$1; STOP-AND-SHOW if estimated ≥$1 | Counts against the same $25 build-cap |
| **Anthropic Haiku 4.5** synthesis (cheap drafts) | ~$0.01–$0.10 | Autonomous | $25 build-cap |
| **Pinecone** single-vector embedding | cents | Autonomous | **$10 total** → G3 escalation |
| **Pinecone** query | fractions of a cent | Autonomous | $10 total |
| **OpenAI text-embedding-3-large/small** (if used) | cents per 1K tokens | Autonomous | Counts as part of the embedding budget |
| **Voyage AI embedding** (text + image) | cents per 1K tokens | Autonomous | Counts as part of the embedding budget |
| **Stripe API** (read-only verification, account lookups) | $0 | Autonomous | N/A |
| **GitHub API** (PRs, branches, issue queries) | $0 | Autonomous | N/A |
| **Vercel API** (deploy, env, logs read) | $0 | Autonomous (read-only); STOP-AND-SHOW for deploy to prod | N/A |
| **WordPress.com MCP** (read-only — site editor context, theme presets) | $0 | Autonomous | N/A |
| **WordPress.com MCP** (write — content authoring, media upload) | $0 monetary, high blast radius | STOP-AND-SHOW | Anything that lands on live skyyrose.co |
| **Klaviyo MCP** (read — flows, lists, profiles) | $0 | Autonomous | N/A |
| **Klaviyo MCP** (write — campaigns, profile updates) | $0 monetary, high blast radius | STOP-AND-SHOW | Sending an email to subscribers is irreversible |
| **Sentry MCP** (read — issues, replays) | $0 | Autonomous | N/A |
| **Context7 MCP** (doc queries) | $0 | Autonomous | N/A — used as primary reference in `verify-impl.js` Step 2 |
| **claude-in-chrome MCP** (browse public pages) | $0 | Autonomous (no admin actions; no dialogs per system reminder) | N/A |
| **Apify scrapers** (RAG web browser, etc.) | varies — typically <$0.05 per page | Autonomous in batches up to $5; STOP-AND-SHOW for jobs >$5 | Used in Phase 4 luxury reference triangulation; Phase 6.7 SEO |
| **Hugging Face Spaces** (free Spaces) | $0 | Autonomous | Authenticated as `damBruh` |
| **Pusher** (drop queue WebSocket) | included in Pusher subscription | Autonomous | N/A |

---

## V2 §1.3 thresholds (autonomous-tier ceilings)

These remain in force as the autonomous-tier ceiling. Breach → G3 escalation, not silent continuation.

| Service | Threshold per V2 build | Action on breach |
|---------|------------------------|------------------|
| Anthropic API (build-time) | $25 cumulative | G3 escalate before continuing |
| AIDesigner credits | 50 generations cumulative | G3 escalate before continuing |
| FASHN test calls | 30 cumulative | G3 escalate before continuing |
| Pinecone embedding API | $10 cumulative | G3 escalate before continuing |

> Note: AIDesigner and FASHN are STOP-AND-SHOW per-call AND threshold-capped cumulatively. The two layers compound: per-call requires confirmation, and even with confirmation, cumulative beyond threshold requires G3 sign-off.

---

## STOP-AND-SHOW manifest format

When a call requires confirmation, output exactly this:

```
STOP — Confirm before proceeding:

Action  : <API + endpoint, e.g., FASHN tryon>
Source  : <exact file path or input data, with size/timestamp>
Target  : <where output goes, e.g., renders/output/<sku>-tryon-<ts>.webp>
Cost    : ~$<estimated dollar amount>  (<break-down: e.g., 4 models × 4 samples × $0.075>)
Cum     : $<cumulative this build> / $<threshold>  (<percentage>%)
Reason  : <one-line why this call is needed>

Proceed? [y/N]
```

Show the **exact** file path, **exact** estimated cost, and **exact** action — not summaries, the literal values. Then wait for "y" or "yes" before dispatching.

---

## Edge cases

**1. Batched calls.** If a single logical operation dispatches multiple paid sub-calls (e.g., one Compositor pipeline run = 6 stages = 6 paid calls), STOP-AND-SHOW once at the start with the aggregated cost preview, not 6 times. The manifest must enumerate each sub-call and its per-call cost.

**2. Unknown cost.** If you don't know the cost, treat as STOP-AND-SHOW. Estimate from API documentation if available; otherwise mark "unknown — need user input" in the manifest. Do not autonomously dispatch on unknown cost even if the call seems trivial.

**3. Silent paid calls inside MCP servers.** If an MCP tool internally dispatches a paid call (e.g., aidesigner/generate-screen-from-text), the MCP call is STOP-AND-SHOW even if the tool's interface looks free.

**4. Threshold approached.** When cumulative spend crosses 80% of any V2 §1.3 threshold, log a warning to `eval/cost-tracker.md` (created on first paid call). At 100%, G3 escalate before any further call against that threshold.

**5. Free tier in production.** If a normally-free tier (e.g., Hugging Face free Space) becomes paid (e.g., the Space owner enabled paid compute), treat as STOP-AND-SHOW from the first call onward. Cost shouldn't surprise.

---

## Tracking

`eval/cost-tracker.md` (auto-maintained from Phase 0.5 onward):

```markdown
# V2 Build Cost Tracker

Updated: <ISO timestamp>

## Cumulative

| Service | Used | Threshold | % | Status |
|---------|------|-----------|---|--------|
| Anthropic API | $X.XX | $25 | XX% | OK / WARN / BREACHED |
| AIDesigner | N gens | 50 | XX% | OK / WARN / BREACHED |
| FASHN | N calls | 30 | XX% | OK / WARN / BREACHED |
| Pinecone | $X.XX | $10 | XX% | OK / WARN / BREACHED |

## Recent calls (last 30)

| Timestamp | Service | Action | Cost | Confirmed by |
|-----------|---------|--------|------|--------------|
| ... | ... | ... | ... | autonomous / Corey |
```

The tracker is written by a wrapper around each paid API call (added in Phase 0.5 as part of the per-edit toolchain extension). Until then, manual logging suffices.

---

## CLAUDE.md amendment

A note is added to `CLAUDE.md` § "STOP AND SHOW" pointing at this file:

> **AMENDED for V2 build (2026-05-03):** See `eval/cost-cap-policy.md` for the hybrid policy. Calls ≤$1 may proceed autonomously up to V2 §1.3 thresholds. Calls >$1 still STOP-AND-SHOW. CLAUDE.md original behavior is the conservative fallback for any call not enumerated in the policy doc.

This amendment is added in a separate task (Task 4 — WP foundation deliverables / commercial protocols) so it lands with the rest of the policy documentation.
