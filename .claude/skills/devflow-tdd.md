---
name: devflow-tdd
description: TDD gate — enforces RED (test fails first) → GREEN (test passes) → coverage via pytest, with hard exit-code gates. Use when writing a new feature or fixing a bug test-first.
---

# Devflow TDD

Deterministic RED/GREEN enforcement. The script inverts pytest's exit code for the RED phase so "I wrote the test and it genuinely fails" is provable, not asserted.

## The cycle

```bash
# RED — write the test, run this. It MUST fail (no implementation yet).
bash scripts/devworkflows/tdd.sh --red tests/path/test_feature.py

# (now write the minimal implementation)

# GREEN — same test must now pass.
bash scripts/devworkflows/tdd.sh --green tests/path/test_feature.py

# Coverage — full suite + threshold (project rule: 85%)
bash scripts/devworkflows/tdd.sh --cov          # >= 85
bash scripts/devworkflows/tdd.sh --cov 80       # transitional override

# Full suite gate (no coverage)
bash scripts/devworkflows/tdd.sh

# Passthrough extra pytest args (always last, after --)
bash scripts/devworkflows/tdd.sh --green tests/x.py -- -x -k auth
```

## Exit-code contract (this is the whole point)

| Mode | pytest exit | Gate result |
|------|-------------|-------------|
| `--red` | 1 (failures) | **exit 0** — RED confirmed, write impl |
| `--red` | 0 (passes) | **exit 1** — test asserts nothing, or code already exists |
| `--red` | 5 (no tests) | **exit 1** — you didn't write the test; "no test" ≠ "RED" |
| `--red` | 2/3/4 | **exit 1** — harness error, not a real failure |
| `--green` | 0 | **exit 0** — GREEN confirmed |
| `--green` | ≠0 | **exit 1** — implementation incomplete |
| `--cov` | 0 | **exit 0** — coverage ≥ threshold |
| `--cov` | ≠0 | **exit 1** — under threshold or failures |
| `full` | 0 | **exit 0** |
| `full` | 5 | **exit 1** — collected nothing |

The exit-5-on-`--red` rule is non-negotiable: a missing test must never masquerade as a passing RED phase.

## Loop until green

```bash
# RED must pass (exit 0) before you write any implementation.
bash scripts/devworkflows/tdd.sh --red tests/path/test_x.py     # exit 0 required

# Write impl. Then:
bash scripts/devworkflows/tdd.sh --green tests/path/test_x.py    # exit 0 required
```

If GREEN exits 1: read the pytest failure, fix the **implementation** (not the test, unless the test itself is wrong), re-run. Repeat until exit 0. Then run `--cov` to confirm the 85% gate still holds.

## Hard rules

- No implementation until `--red` returns exit 0. Test-first is enforced, not encouraged.
- Fix the implementation to satisfy the test. Only edit the test if the test is provably wrong — and say why.
- `--cov` default is 85 (project standard). Lowering it needs an explicit number and a reason.
- Pairs with `devflow-review` (lint) and `devflow-security`. All three compose into `devflow-ship`.
