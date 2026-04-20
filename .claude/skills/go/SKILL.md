---
name: go
description: Run workspace-aware verification, simplify, then open a PR. Detects which workspace (Python / frontend / WordPress) changed and runs the right verify loop. Produces tasks/.last-verify-passed which the Stop hook requires before a turn can end.
---

# /go — Verify, Simplify, Ship

One command to carry a change from "edited" to "merged". Detects the workspace, runs the right verify loop, auto-regenerates codemaps if source changed, runs /simplify, then opens a PR.

## When to run

Any turn that edits code. The verify-gate Stop hook refuses to end turns with uncommitted source changes until `tasks/.last-verify-passed` is fresh — running /go is how you create that marker.

## Inputs

None. Infers workspace from `git diff --name-only HEAD` and staged changes.

## Workspace detection

Based on files changed:

- `*.py`, `main_enterprise.py`, `agents/**`, `api/**`, `services/**`, `orchestration/**`, `core/**` → **Python API**
- `frontend/**` → **Next.js dashboard**
- `wordpress-theme/**` → **WordPress theme**
- Any mix → run every applicable loop in order (Python → frontend → WordPress)

If no source files changed (docs-only, settings-only), skip verification loops and go straight to the commit step. The verify-gate accepts a manual marker touch for those cases.

## Python API loop

```bash
make format                  # isort + ruff --fix + black
make lint                    # abort on error
make test-fast               # pytest -x --timeout=10
```

If any API route file changed (anything under `api/v1/` or `api/graphql/`):
```bash
uvicorn main_enterprise:app --port 8765 &
UVI_PID=$!
sleep 3
curl -fsS http://localhost:8765/health
kill $UVI_PID
```

## Frontend loop

```bash
cd frontend
npm run type-check           # abort on error
npm run lint                 # abort on error
npm run build                # abort on error
```

## WordPress loop

```bash
cd wordpress-theme/skyyrose-flagship
vendor/bin/phpcs --standard=.phpcs.xml -s .      # PHPCS WordPress standard
cd ..
npm run lint:php                                 # all-files PHP syntax
npm run deploy:dry                               # preview deploy (no remote writes)
```

Do **not** run the real deploy here — `/deploy-wp` does that, not `/go`.

## After all applicable loops pass

1. **Codemaps**: check for `tasks/.codemaps-dirty:*` markers.
   - `:backend` present → run `/update-codemaps` for backend scope → stage `docs/CODEMAPS/backend.md`, delete marker
   - `:frontend` present → same for frontend
   - `:wordpress` present → same for wordpress (new scope)
2. **Learnings promotion**: if `tasks/learnings-staging.jsonl` has entries, run `/promote-learnings` and stage any CLAUDE.md / archive updates
3. **Simplify**: run `/simplify` on changed files. If it edits anything, re-run the matching workspace loop.
4. **Changelog** (release-tagged commits only): if the current commit is being tagged `vX.Y.Z`, run `scripts/gen-changelog.sh <workspace>` and stage the resulting CHANGELOG.md
5. **Marker**: `touch tasks/.last-verify-passed` — this unblocks the Stop hook
6. **Commit** with conventional-commits message. Include scope when known (e.g. `fix(wordpress-theme): ...`).
7. **Push** to current branch with `git push -u origin <branch>`. On network failure retry with backoff (2s, 4s, 8s, 16s).
8. **PR** (only if explicitly asked): use `mcp__github__create_pull_request` with a summary drawn from the commit log and a test plan drawn from the verify output.

## Abort criteria

Stop on the first red. Write `tasks/.last-verify-failed` with the error. Do **not** commit, push, or touch the pass marker. Report what broke and where.

## Override for docs-only or config-only edits

If you genuinely did not touch code (docs, comments, config) and the loops aren't meaningful, `touch tasks/.last-verify-passed` is legitimate. The marker is informational, not cryptographic — it exists so the Stop hook has a signal that a thoughtful verification pass happened, not that specific tests passed.
