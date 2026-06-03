# Phase 17 — Review & Approval CLI

## Goal
The user can approve or reject each generated ghost-mannequin image from the command line, and approved images are atomically committed back to the catalog CSV with zero risk of data corruption.

## Requirements
- **REV-01** — `approve-ghost {sku}` moves the reviewed image to `renders/ghost-mannequin/approved/{sku}-ghost-front.webp`, sets `front_model_image` in the CSV, and appends to `approvals.json` with an ISO-8601 timestamp.
- **REV-02** — If the review file does not exist, `approve-ghost` exits 1 with a clear error and makes no CSV mutation.
- **REV-03** — `reject-ghost {sku} "{reason}"` appends `{sku, reason, timestamp}` to `rejections.json`; leaves the image file in place; makes no CSV change.
- **REV-04** — The CSV write is atomic: `tempfile.mkstemp(dir=catalog_dir)` + `os.replace()`. SIGINT or crash between the temp write and the replace leaves the original CSV byte-identical.

## Depends On
- **Phase 14** — Catalog adapter (`skyyrose.core.catalog_loader`) and CSV schema (`front_model_image` column verified at position 8).
- **Phase 15** — Only conceptually. The CLI does not require the agent's outputs to exist for unit testing; tests stub the review file directly.

## Out of Scope
- Generating the review images (Phase 15).
- Uploading approved images to WooCommerce (Phase 18).
- A multi-image batch approval UI. Phase 17 is one-SKU-at-a-time on purpose.

## Architecture

```
skyyrose/core/review.py             ← Pure library — approve(), reject(), atomic_csv_write()
                                       ReviewError, ApprovalResult, RejectionResult
scripts/approve_ghost.py            ← Thin argparse CLI → skyyrose.core.review.approve()
scripts/reject_ghost.py             ← Thin argparse CLI → skyyrose.core.review.reject()
renders/ghost-mannequin/
    approved/                       ← Destination dir (created on first approval)
    approvals.json                  ← Audit log: [{sku, approved_path, csv_field, csv_value, timestamp}, ...]
    rejections.json                 ← Audit log: [{sku, reason, file, timestamp}, ...]
tests/test_review.py                ← Unit + subprocess CLI tests
```

### Atomic CSV write — design contract

```python
fd, tmp = tempfile.mkstemp(dir=catalog_path.parent, prefix=".tmp_review_", suffix=".csv")
with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
os.replace(tmp, catalog_path)   # ← single inode swap, POSIX-atomic on same FS
```

- `dir=catalog_path.parent` ensures the temp file is on the same filesystem → `os.replace()` is a rename, not a copy → atomic.
- `BaseException` (not just `Exception`) cleanup catches `KeyboardInterrupt` and `SystemExit` so we never strand a `.tmp_review_*` file.

### File-move + CSV-write ordering

```
1. validate review file exists           (REV-02 gate)
2. validate sku is in catalog
3. validate approved/ destination free   (idempotency gate)
4. shutil.move(review → approved)
5. atomic_csv_write(modified rows)
6. on failure between 4 and 5: rollback shutil.move(approved → review)
7. write to approvals.json (best-effort; failure logged but does not roll back)
```

The file move precedes the CSV write so a failure after the rename does not corrupt the catalog. The rollback in step 6 ensures the review queue is not silently emptied.

## Plans

### 17-01 — `skyyrose/core/review.py` core library

**Surface area**
- `ReviewError(Exception)` — recoverable failure; CLI prints message and exits 1.
- `@dataclass(frozen=True) ApprovalResult` — `sku, approved_path, csv_path, timestamp`.
- `@dataclass(frozen=True) RejectionResult` — `sku, reason, file_path, timestamp`.
- `approve(sku: str, *, root: Path|str|None = None) -> ApprovalResult`
- `reject(sku: str, reason: str, *, root: Path|str|None = None) -> RejectionResult`
- `atomic_csv_write(rows, fieldnames, csv_path) -> None`

**Module constants** (kept exported for tests to introspect)
- `CATALOG_REL = "wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv"`
- `GHOST_REL = "renders/ghost-mannequin"`
- `APPROVED_SUBDIR = "approved"`
- `FRONT_MODEL_COL = "front_model_image"`
- `GHOST_FILENAME_FMT = "{sku}-ghost-front.webp"`
- `APPROVALS_JSON = "approvals.json"`
- `REJECTIONS_JSON = "rejections.json"`

### 17-02 — `scripts/approve_ghost.py` CLI

```
usage: approve-ghost [-h] [--root ROOT] sku
```

- `sys.path.insert(0, REPO_ROOT)` so the script runs without `pip install -e .`.
- `ReviewError` → exit 1 with message to stderr.
- Unhandled exception → exit 1 with `ClassName: msg` to stderr.
- Success → exit 0, prints `approved: {sku}` + moved/csv/timestamp.

### 17-03 — `scripts/reject_ghost.py` CLI

```
usage: reject-ghost [-h] [--root ROOT] sku reason
```

- Same `sys.path` shim, same error-handling shape as approve.
- Success → exit 0, prints `rejected: {sku}` + reason/file/timestamp.

### 17-04 — `tests/test_review.py`

Test classes (each maps to a requirement):

- `TestApprove` (REV-01) — six tests: file move, CSV column update, row count preserved, other rows untouched, approvals.json appended, ApprovalResult struct.
- `TestApproveStructuralGate` (REV-02) — four tests: missing review file no-op, sku-not-in-catalog rollback, idempotency (already-approved), CLI exit-1.
- `TestReject` (REV-03) — six tests: rejections.json appended, file in place, no CSV change, empty-reason rejected, multi-rejection appends, CLI exit-0.
- `TestAtomicWrite` (REV-04) — three tests: `os.replace` raises `KeyboardInterrupt`, original CSV byte-identical, no `.tmp_review_*` leftovers; round-trip read/write; overwrites garbage.

Total: 19 tests across 4 classes.

## Success Criteria → Test Mapping

| Success Criterion | Test |
|---|---|
| 1. approve moves file + updates CSV + preserves row count | `TestApprove::test_moves_file_into_approved_dir`, `test_updates_front_model_image_column`, `test_preserves_csv_row_count` |
| 2. missing file → exit 1, no CSV change | `TestApproveStructuralGate::test_missing_review_file_raises_no_csv_change`, `test_cli_exit_code_1_on_missing_file` |
| 3. reject leaves file, writes rejections.json, no CSV change | `TestReject::test_writes_rejection_entry`, `test_leaves_file_in_review_dir`, `test_makes_no_csv_change` |
| 4. SIGINT mid-write leaves original CSV intact | `TestAtomicWrite::test_os_replace_keeps_original_on_keyboard_interrupt` |

## Verification Commands

```bash
# Unit + integration tests (RED first, then GREEN)
pytest tests/test_review.py -v

# Coverage check (target 85%+)
pytest tests/test_review.py --cov=skyyrose.core.review --cov-report=term-missing

# CLI smoke test (writes to /tmp, never touches real catalog)
python scripts/approve_ghost.py --help
python scripts/reject_ghost.py --help

# Type check
mypy skyyrose/core/review.py scripts/approve_ghost.py scripts/reject_ghost.py

# Lint
ruff check skyyrose/core/review.py scripts/approve_ghost.py scripts/reject_ghost.py tests/test_review.py
```

## Risk Register

| Risk | Mitigation |
|---|---|
| CSV column name drift breaks `front_model_image` lookup | `_read_catalog()` raises `ReviewError` if column missing — test will catch any future rename in Phase 14 |
| Concurrent approval of same SKU corrupts log | JSON write is also atomic via `tempfile + os.replace`; CSV `os.replace()` is the single source of truth |
| Tmp file leaks on crash | `BaseException` handler unlinks `.tmp_review_*` before re-raising |
| Approved file accidentally re-approved (overwrites prior) | `approve()` raises if `approved/{sku}-ghost-front.webp` exists; explicit re-approval requires deleting destination |
| Reject called twice on same SKU | Allowed — `rejections.json` appends; review queue tracks reason history |

## Definition of Done

- [x] `skyyrose/core/review.py` exists with 8 public symbols + 3 dataclasses
- [x] `scripts/approve_ghost.py` and `scripts/reject_ghost.py` exist and import cleanly
- [x] `renders/ghost-mannequin/approved/.gitkeep` created
- [x] `tests/test_review.py` exists with 19 tests across 4 classes
- [ ] `pytest tests/test_review.py -v` → all green
- [ ] `pytest --cov=skyyrose.core.review` → ≥85%
- [ ] `ruff check` + `mypy` clean on all four files
- [ ] No `TODO`/`FIXME`/`pass`/`raise NotImplementedError` in delivered code
- [ ] Single `feat:` commit for Phase 17
