# Task — Regenerate-guard for `collections/*/sot.json`

Mirror the v7-cards single-source fix (commit `6d0e3849a`) for the per-collection SOT view.
Run in isolated worktree `feat/collection-sot-guard` (parallel-session collision was what
wiped work last time).

## Problem
`collections/<slug>/sot.json` is a GENERATED view (`build-collection-sot.py`, canon =
`identity.json`) but **no guard byte-compared it against a fresh build**. `verify-collection-sot.py`
checks SKU coverage + path resolution + `design-tokens.css` staleness, so a *field-level*
hand-edit (e.g. `is_preorder: false→true`) passed clean. v7-cards and sot-images both have a
byte-compare guard; the collection SOT did not. Proof: the CSV `is_preorder` flip from
`6d0e3849a` (br-014/br-015) had propagated to v7-cards but left `sot.json` + hub `index.html`
stale on HEAD.

## Plan
- [x] Refactor `build-collection-sot.py` → pure seam: `serialize()` (single byte-authority),
      `build_documents()` (pure, no disk write, **no asset-tree scan** → CI-deterministic),
      `build_orphans()`, `_load_masters()`. `main()` = thin writer.
- [x] Add `check_collection_sot_current` to `validate_catalog_consistency.py` (CI-gated home of
      the regenerate-and-compare guards) + path constants + ALL_CHECKS + docstring.
- [x] Add `jsonschema` to `catalog-validate.yml` minimal install (generator validates identity).
- [x] Regenerate + commit the stale committed views (black-rose `sot.json` + `index.html`
      is_preorder catch-up; `_orphans.json` refresh).
- [x] Tests `tests/test_collection_sot_guard.py` mirroring `test_v7_cards_generator.py`.

## Key decisions
- **Guard scopes the 4 `sot.json` files only, NOT `_orphans.json`.** `_orphans` = `scan_tree()`
  minus registered → sensitive to any file in the broad image tree → not CI-deterministic.
  Left to `freshness-guard.sh`. `build_documents()` deliberately never calls `scan_tree()`.
- **Home = `validate_catalog_consistency.py`** (GitHub-Actions-gated on `data/**`), not
  `verify-collection-sot.py` (pre-commit only). Faithful mirror of `v7_cards_current`.
- **`index.html` included** despite coming from a different generator (`gen-collection-hub.py`):
  the br-014/br-015 `($100)`→`($100 · PRE-ORDER)` caption change is the SAME CSV catch-up;
  leaving it stale = hub contradicting `sot.json` (split-brain). Coherence over surgical scope.

## Verification (this session)
- Refactor byte-faithful: pre-refactor regen bytes == post-refactor regen bytes (empty diff).
- Guard fails on planted drift (exit 1, names the file), passes after regen (exit 0).
- `validate_catalog_consistency.py`: 17/17 checks pass.
- `pytest test_collection_sot_guard.py + test_v7_cards_generator.py + tests/collections/`: 46/46.
- ruff / black / isort / mypy: clean on the 3 changed Python files.
- Minimal-deps import chain proven: `build_documents()` pulls only `jsonschema` + its closure
  (`idna`/`jsonpointer` are jsonschema's optional, skipped-when-absent format checkers).
