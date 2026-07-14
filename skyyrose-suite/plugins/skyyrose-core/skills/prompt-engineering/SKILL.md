---
name: prompt-engineering
description: Use when structuring how you approach any task — select the reasoning technique that fits the task type (chain-of-thought, ReAct, few-shot, tree-of-thoughts, self-consistency, structured output) to produce production-quality work, always subordinate to verification.
origin: SkyyRose
---

# Prompt Engineering

A technique structures **how** you reason. It never licenses **what** you claim. Chain-of-Thought
does not mean inventing plausible steps about code you have not read. Role-Based does not mean
roleplaying expertise instead of reading the source. Few-Shot does not mean generating examples
from imagination instead of real codebase or catalog patterns. RAG means you actually retrieved
context — Read/Grep/Glob — before responding. Picking the right technique makes reasoning
sharper; it does not make an unverified claim any more true.

> **Boot first:** read `.claude/rules/prompt-techniques.md` — the auto-selection matrix and hard
> rule this skill operationalizes — and the Anti-Hallucination Protocol in `CLAUDE.md`: every
> claim traces to a tool call or user confirmation from THIS session. Do not pick a technique
> before you know what you are grounding it in.

## When to Use

- Any task with more than one plausible reasoning strategy — debugging vs. research vs. creative
  vs. structured-data all want different scaffolding.
- Before starting non-trivial work — technique selection happens BEFORE code or content, not
  discovered mid-stream.
- When a task feels like "just start typing" — that instinct is the signal to pick a technique
  deliberately, not a reason to skip picking one.
- Production-critical work — pair with [[adversarial-planning]] and stack techniques (Ensemble).

## Technique selection

The auto-selection matrix from `.claude/rules/prompt-techniques.md`, restated as an invocable
lookup. Each technique carries required pre-work — skipping the pre-work and running the
technique anyway is exactly the failure mode this skill exists to prevent.

| Task type | Technique | Required pre-work |
|---|---|---|
| Code writing / debugging | Chain-of-Thought | Read existing code. Understand current state. |
| Architecture / system design | Tree of Thoughts | Read entry points, dependency flow, existing patterns. |
| Creative content / brand copy | Constitutional + Role-Based | Read brand rules from canon. Verify product data. |
| Product descriptions | Few-Shot + Role-Based | Read real product data — catalog CSV, not imagined examples. |
| SEO / meta / structured data | Structured Output | Read existing templates/schemas. |
| Research / investigation | ReAct | Real tool calls only — no invented tool results. |
| Bug investigation | ReAct | Hypothesis → test → observe → refine, each step a real run. |
| Q&A about codebase | RAG | Read the relevant files first. Quote `file:line`. |
| Complex analysis | Chain-of-Thought | Each step anchored to a verified data point. |
| Ambiguous requirements | Self-Consistency | Try 2-3 interpretations. Pick the one with the most evidence. |
| Production-critical work | Ensemble | Stack 3 techniques. Each independently verified. |
| Planning / roadmapping | Tree of Thoughts | Explore options against real constraints. |

If the task doesn't match a row, pick the nearest analog — never skip the pre-work because the
row is missing.

## Loop until production-grade

Bounded, like [[drive-to-green]] — never more than 5 turns, stop if the same result repeats
twice (that is guessing, not reasoning):

```
1. Pick the technique from the table above (or the nearest analog).
2. Do the required pre-work — Read/Grep/Glob, never from memory.
3. Draft using the technique.
4. Verify every claim in the draft against an authoritative source (see below).
5. Refute adversarially — try to find what's wrong before showing it to anyone else.
6. Refine. Repeat 3-5 until nothing new surfaces, or 5 turns are used.
```

## Verify from an authoritative source

A technique never changes the Verification Protocol — it only structures the reasoning that
leads to the claim being verified. The claim still needs a check that can FAIL:

- **Chain-of-Thought** — each step anchors to code actually read, cited as `file:line`, not a
  plausible-sounding paraphrase.
- **Few-Shot** — examples come from the catalog CSV / real codebase patterns, never generated
  from imagination.
- **RAG** — every answer quotes line numbers from files actually opened this session.
- **ReAct** — an "action" means a real tool call with a real result; a hypothesis that was never
  tested is not a finding.
- **Role-Based** — the role is read, not roleplayed: brand canon, product data, or domain docs
  come from source, not from acting the part.

If the technique produced a claim nothing can falsify, the technique yielded before the claim
did — go back and verify before continuing.

## Adversarial pass

- **Before** building: [[adversarial-planning]] — have a genuinely different model challenge the
  reasoning, not the prose, before tokens go into the wrong technique.
- **After** verifying: [[adversarial-verification]] — try to REFUTE the draft's claims; default
  to "unverified" until independently proven otherwise.

## Guardrails · Handoff · Log

- Technique serves quality, not ritual — drop it the moment it stops helping.
- Never announce which technique you're using unless the user asks; show the reasoning
  (Chain-of-Thought / Tree of Thoughts), not a label.
- Anti-Hallucination always wins: if a technique would produce ungrounded output, the technique
  yields — verify first, resume the technique second.
- A technique that produces an unverified claim is a fail-open defect wearing a different
  costume — cross-ref [[fail-closed-audit]].
- Log the pattern via [[continuous-learning]] when a technique choice actually changed the
  outcome — caught a defect, avoided a wrong turn, or a task type needs a new row in the table.
