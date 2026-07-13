---
description: Rewrite a rough prompt into a high-signal prompt before sending. Mirrors Augment Code's enhance-prompt feature.
argument-hint: "[--send | --compare] <rough prompt>"
---

# /enhance — Prompt Enhancement

Turn a rough, half-formed thought into a precise prompt that gets a better answer. Three modes — pick the one that matches the stakes.

## Invocation

| Mode | Syntax | Behavior |
|------|--------|----------|
| Review (default) | `/enhance <rough prompt>` | Rewrite, show the result + change summary, WAIT for "send" before answering |
| One-shot | `/enhance --send <rough prompt>` | Rewrite silently, then answer the enhanced prompt in the same turn |
| Compare | `/enhance --compare <rough prompt>` | Show original, enhanced, and a bulleted diff — do NOT answer |

The raw input is:

$ARGUMENTS

## The Enhancement Pass

Execute these steps in order. Do not skip.

1. **Parse intent.** What is the user actually trying to get? (Code? An explanation? A decision? A plan?) State it in one mental line before rewriting.
2. **Identify missing context.** What would Claude need to do this well — file paths, constraints, success criteria, desired output format? Add what is truly missing; do NOT invent new requirements.
3. **Strip noise.** Remove hedging ("I was wondering if maybe"), filler ("just", "really", "kind of"), and apology patterns. Keep the signal.
4. **Add structure.** If the ask has multiple parts, enumerate them. If it's a decision, surface the constraints. If it's a task, state the done condition.
5. **Preserve voice.** Do not add formality the user didn't use. Casual in → casual out. Make it *clearer*, never fancier.

## Output Format — Review Mode (default)

Print exactly this block, then stop. Do not answer the prompt yet.

```
━━━ ENHANCED PROMPT ━━━
<the rewritten prompt — can be 1 line or a short paragraph, proportional to the input>
━━━━━━━━━━━━━━━━━━━━━━

Changes:
- <one-line change>
- <one-line change>
- <note any assumption you made — mark with "ASSUMED:">

Reply "send" to answer this, or tell me what to change.
```

## Output Format — `--send` Mode

No review block. Start your reply with a single quoted line so the user sees what you actually answered:

```
> <enhanced prompt on one line>

<your real answer>
```

Then answer normally.

## Output Format — `--compare` Mode

```
ORIGINAL:
<raw input>

ENHANCED:
<rewritten>

DIFF:
- removed: <what you cut>
- added: <what you added>
- tightened: <what you rephrased>
```

Do not answer the prompt in this mode. User is inspecting the rewrite, not asking a question.

## Enhancement Philosophy

<!--
TODO(user): Replace the placeholders below with your own rules. These are the guardrails that
shape every rewrite — the enhancer only has taste if you give it taste. Aim for 4–6 bullets.

Examples of useful rules:
- Terse over thorough. Never add preamble or "great question" energy.
- Any codebase reference must include a concrete file path.
- Never add features, scope, or requirements the user did not write.
- Keep slang and voice. This is a command line, not a cover letter.
- For code requests, always end with a one-line success criterion.
- If the input is ambiguous in a load-bearing way, DO NOT guess — add an "ASSUMED:" note in Changes.
-->

- [describe your default tone here]
- [describe what the enhancer must never add]
- [describe what must always be present for codebase-touching prompts]
- [describe how to handle ambiguity]

## Anti-Patterns (hard no)

- **Don't invent requirements.** Ambiguous inputs → surface the ambiguity in Changes, don't silently resolve it.
- **Don't over-expand.** One-line input → one-line or short-paragraph output. Five paragraphs for a casual question is failure.
- **Don't add pleasantries.** No "please", no "thanks", no "I'd appreciate it". Operational tone only.
- **Don't answer in review mode.** Waiting for "send" is the entire point.
- **Don't rewrite the philosophy.** The user-supplied bullets above are the contract — follow them, don't second-guess them.

## Examples

**Input:**
```
/enhance fix the thing with the cart where sometimes it doesnt update
```

**Output (review mode):**
```
━━━ ENHANCED PROMPT ━━━
Debug the WooCommerce cart update flow — the cart item count sometimes fails to refresh after add-to-cart. Reproduce the bug, identify the root cause (likely in the Store API call or the UI listener), and propose the minimal fix. Success = cart count updates on every add-to-cart without a page reload.
━━━━━━━━━━━━━━━━━━━━━━

Changes:
- Named the specific system (WooCommerce cart) — inferred from project context
- Added a reproduce-then-diagnose structure
- ASSUMED: "the thing with the cart" = item count refresh. If it's stock validation or totals, say so.
- Defined a success criterion

Reply "send" to answer this, or tell me what to change.
```
