# Autonomous Control Plane

## Action authority

| Class | Actions |
| --- | --- |
| `AUTO` | Read-only discovery, planning, ledger updates, local analysis |
| `AUTO_WITH_LOG` | Local worktrees/branches, checkpoint commits, cherry-picks, deterministic builds/tests, local browser runs, screenshots, evidence artifacts |
| `ASK` | New dependencies, credentials, paid APIs, external writes, uploads, pushes, protected-branch merges, destructive actions, staging mutation, deployment |
| `FORBIDDEN` | Secret disclosure, fabricated evidence, gate waiver, unauthorized production/customer/catalog mutation |

The lead batches approval requests. A blocked phase does not stop independent
runnable phases.

## Durable ledger

Store a repository-local ledger outside distributable theme files. Each phase
records `id`, `state`, `dependencies`, `owner`, `worktree`, `owned_paths`,
`baseline_id`, `candidate_id`, `attempt`, timestamps, outputs, evidence,
blockers, and `next_authority`. Update it before dispatch, handoff, integration,
review, replacement, and close. Resume from the ledger.

## Recovery

Classify failures as `TRANSIENT`, `IMPLEMENTATION`, `BASELINE`, `ENVIRONMENT`,
`AUTHORITY`, `EVIDENCE`, or `INTEGRATION_CONFLICT`. Retry only transient failures,
at most twice, with bounded backoff. Quarantine partial handoffs. Return semantic
conflicts to their owner. Roll back integration to the last checkpoint. Preserve
all failed evidence and increment attempts. Any mutation after review requires a
new candidate ID and fresh reviewer.

## Candidate identity

Identify source candidates from commit, tracked patch, untracked inventory,
dependency locks, theme version, and generated-asset hashes. Identify built and
packaged candidates separately and link their hashes. Evidence against a prior
identity becomes stale automatically.
