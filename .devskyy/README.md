# `.devskyy/` — Repo-Level Tooling Config

Project-internal tooling configuration (not consumed by users, deploy, or runtime).

## `scopes.toml` — file-to-branch routing

Declarative map: path globs → logical work scope → branch prefix.

Used by `scripts/scope.py` to:

- Group dirty working-tree files into the PRs they belong to (`scope status`)
- Reject cross-scope commits at pre-commit time (`scope check-staged`)
- Plan branch splits (`scope split --plan`)
- Surface uncategorized files so the config grows with the codebase

**Adding a new scope** — append a `[scope.NAME]` block in priority order
(specific before general; `ignore` first, `meta` last). Re-run
`python3 scripts/scope.py status` until uncategorized count is zero.

**Adding a path to an existing scope** — append a glob to that scope's `paths`
array. Glob syntax: `*` (one segment), `**` (recursive), `?`, `[seq]`,
`{a,b,c}` (brace expansion).

## Pre-commit integration

Add to `.pre-commit-config.yaml` to enforce one-scope-per-commit:

```yaml
- repo: local
  hooks:
    - id: scope-check
      name: scope check-staged
      entry: python3 scripts/scope.py check-staged
      language: system
      stages: [pre-commit]
      pass_filenames: false
```

This rejects commits that mix scopes or include files from the `ignore` scope
(regenerable outputs that should be in `.gitignore`).
