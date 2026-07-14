---
name: lsp-code-intelligence
description: Use for symbol-precise code navigation on the monorepo — go-to-definition, find-references, rename, hover-types via the installed LSP servers instead of grep guessing. Answers from the real symbol graph, not text matching.
origin: SkyyRose
---

# LSP Code Intelligence

`grep` matches TEXT. An LSP answers from the SYMBOL GRAPH. On a large Python/TS/PHP
monorepo, "who calls this / where is this defined / what's this type" should come from
the language server, which knows scope, imports, and shadowing that grep cannot —
grep will find every string that looks like a match, not every reference that IS one.

> **Boot first:** check `.wolf/anatomy.md` before reading any file it already describes
> → confirm the server binary for the target language is actually on PATH (`pyright`,
> `vtsls`, `bash-language-server`, `vscode-langservers`) → then query. A server only
> works for a language whose binary is installed; `pyright` without `pyright` present
> silently no-ops rather than erroring — verify presence, don't assume it.

## When to Use

- **Before deleting or renaming a symbol** — run find-references first; pairs with the
  Deletion policy census in `CLAUDE.md` (repoint-first / census-gated: zero live
  consumers must be *proven*, not guessed from a grep that missed an aliased import).
- **Go-to-definition instead of grep** — "where is this class/function actually defined"
  when multiple files share a name (common across `api/`, `agents/`, `skyyrose/`).
- **Type-checking a change** — hover-types on a call site before editing its signature,
  to see every inferred type grep cannot show.
- **Cross-file call graphs** — "what calls this" across Python/TS/PHP boundaries where a
  text search would miss a re-export or a dynamically dispatched call.

## Method

1. **Anatomy for orientation** — `.wolf/anatomy.md` gives the 2-3 line file description;
   use it to narrow scope before touching the LSP, per the OpenWolf token-discipline rule
   (don't full-read what anatomy already answers).
2. **LSP for symbol precision** — go-to-definition / find-references / hover / rename on
   the actual symbol, once scope is narrowed. This is the authoritative step, not a
   convenience layer over grep.
3. **Grep only as fallback or cross-check** — when the server for that language isn't
   running (binary absent from PATH), or as an independent second signal on a
   deletion-critical find-references (see Verify, below).

## Loop until the symbol graph is consistent

Bounded — never more than 5 turns, stop if the same result repeats twice (that's
guessing, not querying):

```
1. Query the LSP for the symbol (def / refs / hover).
2. No result? Verify the server binary exists on PATH and is actually running for that
   language — a missing binary yields a false "0 references", not a real answer.
3. Still no server → fall back to Grep, and NOTE the gap (which language, which file)
   so it isn't silently treated as an LSP-confirmed answer.
4. Repeat for the next symbol in scope. Stop when every symbol in the change has a
   result you can attribute to a running server, not an absent one.
```

## Verify from an authoritative source

The LSP result IS the authoritative symbol answer — but only if the server is actually
running. A missing binary returns "no references" that looks identical to a real zero:

- **Confirm the server is live** before trusting a "0 references" — check the binary is
  on PATH for that language, not just that the plugin is installed.
- **Cross-check a deletion-critical find-references against a Grep** — an unindexed file
  (outside the LSP's workspace root, or a language the server doesn't cover) can hide a
  live consumer that only Grep catches.
- **NEVER delete a symbol on an LSP "0 references" alone without the Grep cross-check** —
  this is the same fail-open shape as `bug-230`: an absent/misconfigured server
  "passing" a check it never actually ran.

## Adversarial pass

- Assume the index is stale or the server is silently down — [[adversarial-verification]]
  before trusting a clean find-references on anything deletion-critical or
  security-sensitive; have an independent check try to REFUTE "no references" rather
  than accept it at face value.

## Guardrails · Handoff · Log

- An LSP answer backed by a server that isn't actually running is not an answer — treat
  it as unverified and fall back per Method step 3.
- Deletion/rename decisions follow the census rule in `CLAUDE.md`: LSP find-references +
  Grep cross-check + tests/downstream/cross-language string refs, before any removal.
- Cross-plugin handoff (backend symbol change affecting theme PHP, or vice versa) per
  `CROSS-PLUGIN.md` — re-verify on the receiving side, don't assume the LSP result
  transfers across language servers.
- Log a new server-absence or false-negative pattern via [[continuous-learning]] so the
  next session doesn't re-discover the same PATH gap.
