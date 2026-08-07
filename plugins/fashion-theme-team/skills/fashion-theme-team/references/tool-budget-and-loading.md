# Tool Budget and Lazy Loading

## Contract

- All platform tools remain callable on demand for the motherbase team.
- Do not preload the full toolset into every role context.
- Start each wave with role-scoped active tools; expand only for explicit evidence
  requirements and revert after completion.
- Default profile is `Read`, `Grep`, `Glob`, `Bash`.
- Builder profiles add `Edit` and `Write`.
- Lead and lead-automation workflows may use `TaskCreate`, `TaskUpdate`,
  `TaskList`, and `Agent` as handoff operators.
- The optional `elite-builder-runtime` is not imported, initialized, or exposed
  in ordinary role contexts. Load it only for an explicit runtime request.
- A design-system wave loads the architect plus only the specialists whose
  dependencies are ready; never all eight pod charters at once.

## Validation requirement

Each role handoff must include one of:

- Deterministic artifact + eyes-on verification review.
- Deterministic artifact + current authoritative documentation + executable local evidence.

A claim that cannot be proven by either path is `BLOCKED`.

## Runtime notes

- If a role needs a tool outside its default active profile, the lead
  documents the temporary expansion in the ledger before the call.
- Temporary expansion is not permanent; return to the profile once the artifact is
  checkpointed.
