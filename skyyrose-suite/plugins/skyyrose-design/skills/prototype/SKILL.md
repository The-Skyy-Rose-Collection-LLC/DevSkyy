---
name: prototype
description: Build a throwaway prototype to answer one question before committing — in ANY domain. Routes between three branches — a runnable terminal app for state/business-logic questions, several radically different UI variations toggleable from one route, or several variant generated artifacts (image, video, 3D, audio, copy) compared side-by-side. Use when the user wants to prototype, sanity-check a data model or state machine, mock up a UI, explore image/render/lookbook directions, compare engines, explore design options, or says "prototype this", "let me play with it", "try a few designs", "show me a couple variations".
---

# Prototype

A prototype is **a throwaway artifact that answers a question**. The invariant is always the same: **N throwaway variants answering one question, presented side-by-side, the winner absorbed and the rest deleted.** Only the *medium* changes with the domain — terminal, browser, image grid, audio reel. There is no domain in which a prototype cannot be produced; if you ever conclude "this isn't prototype-able," you've picked the wrong medium, not hit a real wall.

## Pick a branch

Identify which question is being answered — from the user's prompt, the surrounding code/assets, or by asking if the user is around — then pick the medium that fits:

- **"Does this logic / state model feel right?"** → [LOGIC.md](LOGIC.md). A tiny interactive terminal app that pushes the state machine through cases that are hard to reason about on paper.
- **"What should this *screen* look like?"** → [UI.md](UI.md). Several radically different UI variations on a single route, switchable via a URL search param and a floating bottom bar.
- **"Which produced *artifact* / approach is right?"** (image, render, lookbook, video, 3D, audio, copy — anything *generated* rather than a screen or a state model) → [GENERATIVE.md](GENERATIVE.md). Several variant artifacts generated along one axis (engine / method / direction), presented as one side-by-side comparison, with a cost gate before any paid generation.

The three branches produce very different artifacts — getting this wrong wastes the whole prototype. Match the medium to the question, not to habit: a backend module → logic; a page or component → UI; a generated asset → generative.

**No matter the domain, a prototype is producible.** If the question fits none of the three cleanly, do not refuse — fall back to the invariant directly: produce N (default 3) throwaway variants of the smallest real version of the artifact, in whatever medium is native to it, present them in one comparable view, capture the verdict, delete the rest. The branch files are worked examples of this one shape, not an exhaustive list of allowed domains.

If the question is genuinely ambiguous and the user isn't reachable, default to whichever branch best matches what's in front of you (backend module → logic; page/component → UI; image/render/media asset → generative) and state the assumption at the top of the prototype.

## Rules that apply to all branches

1. **Throwaway from day one, and clearly marked as such.** Locate the prototype close to where it will actually be used (next to the module, page, or pipeline it's prototyping for) so context is obvious — but name it so a casual reader can see it's a prototype, not production. For throwaway UI routes, obey whatever routing convention the project already uses; for generated artifacts, write into a clearly-marked `_prototype/` / scratch dir, never a production asset path.
2. **One command to run.** Whatever the project's existing task runner supports — `pnpm <name>`, `python <path>`, `bun <path>`, etc. The user must be able to start it without thinking.
3. **No persistence by default.** State / outputs live in memory or a scratch location, not production stores. Persistence is the thing the prototype is _checking_, not something it should depend on. If the question explicitly involves a database, hit a scratch DB or a local file with a clear "PROTOTYPE — wipe me" name.
4. **Gate any real-world cost.** If a branch spends money or metered compute (paid generators, third-party APIs), STOP-AND-SHOW the exact cost manifest and wait for explicit `y` before the spend; a free dry-run / `plan` first is the correct opening move. (Logic/UI prototypes are usually free; generative ones usually aren't.)
5. **Skip the polish.** No tests, no error handling beyond what makes the prototype _runnable_, no abstractions. The point is to learn something fast and then delete it.
6. **Surface the result.** After every action (logic), on every variant switch (UI), or as one side-by-side comparison (generative), present the full relevant state/output so the user can see and judge what differs.
7. **Delete or absorb when done.** When the prototype has answered its question, fold the validated decision into the real code/pipeline and delete the throwaway — don't leave it rotting in the repo.

## Verify before you hand over (authoritative)

A prototype you haven't verified is not done — it's a claim. Before telling the user it's ready, run a check **that can return "no."** Invoke the project's `verification-before-completion` discipline: evidence before assertion, always. A checklist you eyeball is not verification; a command whose output you read is.

Every branch must pass these, with proof you actually ran:

1. **It exists / runs.** Logic → the command launches and the first frame renders. UI → the route loads and returns 200 for each `?variant=`. Generative → every expected output file exists and **decodes** (`identify <file>` / open it), none zero-byte.
2. **The variants genuinely differ.** UI → each variant renders a structurally different tree (not the same component). Generative → the outputs are not byte-identical re-rolls — `shasum <files>` must show distinct hashes, and on inspection they differ along the stated axis. Logic → each action visibly mutates state.
3. **It answers the stated question.** Re-read the one-line question from the top of the prototype; confirm the artifact actually lets the user decide it. If it doesn't, the prototype is wrong even if it runs.
4. **It didn't leak into production.** Outputs/code live in the throwaway location; `git status` / a path check shows nothing written to a real asset path, route, or store.
5. **Cost gate honored** (paid branches). The STOP-AND-SHOW manifest was shown and `y` received before any spend; no paid call fired during a dry-run.

State the result as evidence ("3 files, distinct hashes, all 1536×1024, decoded OK"), not as "looks good." If any check fails, fix it before handing over — never report a prototype ready on an unverified assumption.

## When done

The _answer_ is the only thing worth keeping from a prototype. Capture it somewhere durable (commit message, ADR, issue, or a `NOTES.md` next to the prototype) along with the question it was answering. If the user is around, that capture is a quick conversation; if not, leave the placeholder so they (or you, on the next pass) can fill in the verdict before deleting the prototype.

## Worked examples by branch

Each branch file ends with concrete **do / don't** examples and a branch-specific verification recipe — see the *Anti-patterns* and, in [GENERATIVE.md](GENERATIVE.md), the *Worked example* and *Verify before hand-over* sections. Read the matching branch file before building; the examples are the fastest way to avoid the common failure of that medium.
