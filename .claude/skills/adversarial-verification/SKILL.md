---
name: adversarial-verification
description: Have an independent agent skeptically re-verify a fix, claim, or result instead of trusting the builder's self-assessment. Use when a subagent or Workflow stage produces a fix/result and you need to know if it actually worked — code fixes, content claims, data pipeline output, generated assets, or any "did this actually work" question — especially when multiple independent attempts are built in parallel and need honest, comparable grading.
---

# Adversarial Verification

## The problem

An agent that builds a fix and then grades its own fix will round up. "Looks better to
me" is not evidence — it's the builder's incentive to report success talking. This is
the same failure mode `verification-before-completion` names for a single agent's own
work; adversarial verification is the version for orchestrated/multi-agent work, where
the fix is a **separate artifact** another agent can independently inspect.

## The pattern

1. **Builder produces an artifact**, not just a claim: an exported file, a diff, a
   rendered image, a test run, a query result. Something a second agent can inspect
   without re-reading the builder's prose.
2. **Verifier is a fresh agent** with no memory of building it. Give it the artifact
   and the original problem statement — not the builder's self-assessment. If the
   builder's notes are useful context, hand them over labeled as *unverified claims to
   check*, not as fact.
3. **Verifier defaults to skeptical.** Instruct it explicitly: assume still-broken
   unless the evidence clearly proves otherwise. A partial improvement is
   `partially-improved`, not `clean`. Ties go to "not fixed."
4. **Verifier re-derives evidence itself** — re-renders, re-runs the test, re-executes
   the query, re-reads the diff — rather than summarizing what the builder already
   said. If it can't independently reproduce the check, it can't confirm the claim.
5. **Verdict is structured**, not prose-only: a fixed enum (`clean` /
   `partially-improved` / `no-improvement` / `regressed`) plus a boolean like
   `recommend_ship`. Structured verdicts are what make step 6 possible.
6. **Synthesis compares verdicts**, not builder claims. Only artifacts with a
   verifier-confirmed clean/acceptable verdict move forward (deploy, merge, ship).

## Two-model debate loop (hard-capped at 3 rounds)

For higher-stakes verification, use two **different models** as builder and verifier,
not two instances of the same model. A fresh instance of the same model can still share
the same blind spot the builder had — different weights are a real, not cosmetic,
source of independence. Pick the pairing per task (e.g. builder on the fast/cheap tier,
verifier on the deeper-reasoning tier, or vice versa) via `agent()`'s `model` option.

Debate runs at most 3 rounds. Rounds 1-2 are argument; round 3 is not — it's a forcing
function that ends debate by making both sides touch ground truth:

1. **Round 1 — proposal + challenge.** Builder (model A) proposes the fix. Verifier
   (model B) challenges skeptically and must state specifically what evidence would
   change its verdict.
2. **Round 2 — rebuttal + recheck.** Builder addresses that specific challenge (not a
   full re-argument). Verifier rechecks against the rebuttal. If the verifier is now
   satisfied, stop here — don't burn a third round on agreement.
3. **Round 3 — mandatory execution, no more argument.** If rounds 1-2 didn't converge,
   both sides must stop arguing and **actually execute the verifiable task themselves**
   right now — run the test, re-render the asset, re-run the query — and the verdict
   is decided from that raw output, not from further reasoning. This is the loop's exit
   condition regardless of whether the two models agree: empirical execution outranks
   continued debate. Never let round 3 be "argue again, harder."

```js
const MODELS = { builder: 'sonnet', verifier: 'opus' } // deliberately different

let verdict = null
let transcript = []
for (let round = 1; round <= 3; round++) {
  const finalRound = round === 3
  if (verdict?.overall_verdict === 'clean') break // converged early, don't force round 3

  const builderTurn = await agent(
    finalRound
      ? `Final round. No more argument. Execute the verifiable check yourself right
         now (run the command/test/render) and report the raw output.
         Debate so far: ${JSON.stringify(transcript)}`
      : `Round ${round}. Defend or refine against this challenge (if any):
         ${JSON.stringify(verdict) || 'none yet — initial proposal'}.`,
    { label: `builder-r${round}`, model: MODELS.builder, schema: BUILD_SCHEMA }
  )

  const verifierTurn = await agent(
    finalRound
      ? `Final round. Do not argue further — independently execute the same
         verifiable check yourself and report raw output. Compare against the
         builder's round-3 execution: ${JSON.stringify(builderTurn)}`
      : `Round ${round}. Skeptically challenge this artifact. Default to "not fixed"
         unless proven. State specifically what would change your mind next round.
         Artifact: ${JSON.stringify(builderTurn)}`,
    { label: `verifier-r${round}`, model: MODELS.verifier, schema: VERIFY_SCHEMA }
  )

  transcript.push({ round, builderTurn, verifierTurn })
  verdict = verifierTurn
}
```

Fan this whole loop out per candidate with `pipeline()` when multiple independent
builders are competing — each candidate gets its own debate, own model pairing, own
verdict; only synthesis needs a barrier (`parallel()` or a plain `await` over the
collected verdicts) since it must compare all candidates at once.

`VERIFY_SCHEMA` should force an enum verdict field (`clean` / `partially-improved` /
`no-improvement` / `regressed`) and a boolean ship/merge/deploy recommendation — never
let the verifier return free-form prose only, or synthesis has nothing reliable to
compare.

## Standalone (non-Workflow) use

The same discipline applies to a single subagent dispatch: after `Agent()` returns a
"fixed it" report, dispatch a **second, independent** `Agent()` call with the artifact
and told to verify skeptically, before you relay "done" to the user. Don't let the
same agent that wrote the code also be the last word on whether it works.
