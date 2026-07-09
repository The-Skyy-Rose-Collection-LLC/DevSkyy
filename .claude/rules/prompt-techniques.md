# Prompt Technique Enhancement (Always Active)

> Techniques ENHANCE reasoning structure — they NEVER override the Anti-Hallucination Protocol.

## Hard Rule: Verification First, Technique Second

**A technique structures HOW you think. It does not license WHAT you claim.**

- Chain-of-Thought does NOT mean inventing plausible reasoning steps about code you haven't read
- Role-Based does NOT mean roleplaying expertise you don't have — read the source first
- Few-Shot does NOT mean generating examples from imagination — use real codebase patterns
- RAG means you MUST actually retrieve context (Read/Grep/Glob) before responding

If a technique would cause you to state something you haven't verified: **skip the technique and verify first.**

---

## Auto-Selection Matrix

| Task Type | Technique | Required Verification Before Execution |
|-----------|-----------|---------------------------------------|
| Code writing / debugging | Chain-of-Thought | Read existing code. Understand current state. |
| Architecture / system design | Tree of Thoughts | Read entry points, dependency flow, existing patterns. |
| Creative content / brand copy | Constitutional + Role-Based | Read brand rules from memory. Verify product data. |
| Product descriptions | Few-Shot + Role-Based | Read actual product data from verified sources. |
| SEO / meta / structured data | Structured Output | Read existing templates/schemas. |
| Research / investigation | ReAct | Real tool calls only. |
| Bug investigation | ReAct | Hypothesis → test → observe → refine. |
| Q&A about codebase | RAG | Read the relevant files first. Quote line numbers. |
| Complex analysis | Chain-of-Thought | Each step anchored to a verified data point. |
| Ambiguous requirements | Self-Consistency | Try 2-3 interpretations. Pick the one with most evidence. |
| Production-critical work | Ensemble | Stack 3 techniques. Each independently verified. |
| Planning / roadmapping | Tree of Thoughts | Explore options against real constraints. |

---

## Anti-Hallucination Interaction

**Anti-Hallucination always wins.** If a technique would produce ungrounded output, the technique yields.

## Transparency

- Do NOT announce technique selection unless the user asks
- DO show reasoning when using Chain-of-Thought or Tree of Thoughts
- If the user says "use X technique": override auto-selection
- If a technique isn't helping: drop it. Techniques serve quality, not ritual.
