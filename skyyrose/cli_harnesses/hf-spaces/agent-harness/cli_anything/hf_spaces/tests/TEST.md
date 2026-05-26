# Test Suite — cli-anything-hf-spaces

## Running tests

```bash
# Unit tests only (no live HF calls, no env gate needed)
pytest cli_anything/hf_spaces/tests/test_core.py -v

# All tests including e2e (requires HF_SPACES_E2E=1 AND a valid HF_TOKEN)
HF_SPACES_E2E=1 HF_TOKEN=hf_... pytest cli_anything/hf_spaces/tests/ -v

# With coverage
pytest cli_anything/hf_spaces/tests/test_core.py -v --cov=cli_anything.hf_spaces --cov-report=term-missing
```

## Gate behaviour

- `HF_SPACES_E2E=0` (default): live HF tests are **skipped** cleanly.
- `HF_SPACES_E2E=1` and HfApi unreachable: live tests **FAIL** (not skip).
  This enforces that the gate is an intentional opt-in, not a silent fallback.

## Test files

| File | Coverage |
|------|----------|
| `test_core.py` | 40+ unit tests — hardware, space parsing, secrets, session, manifest, hf_backend auth |
| `test_full_e2e.py` | Subprocess e2e against real HF API (gated by HF_SPACES_E2E=1) |

## HF account for live tests

Account: `damBruh` — set `HF_TEST_SPACE` env var to the test Space repo_id.
