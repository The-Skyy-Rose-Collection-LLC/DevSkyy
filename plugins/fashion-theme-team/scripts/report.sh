#!/usr/bin/env bash
# shellcheck disable=SC2016
set -euo pipefail

candidate_root="${1:-${PWD}}"

if [[ ! -d "${candidate_root}" ]]; then
  printf 'FAIL: candidate path does not exist: %s\n' "${candidate_root}" >&2
  exit 1
fi

candidate_id=""
if git -C "${candidate_root}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  commit_id="$(git -C "${candidate_root}" rev-parse HEAD)"
  candidate_material="$(
    printf 'commit=%s\n' "${commit_id}"
    git -C "${candidate_root}" diff --binary HEAD
    git -C "${candidate_root}" ls-files --others --exclude-standard | LC_ALL=C sort
    find "${candidate_root}" -maxdepth 3 -type f \
      \( -name 'package-lock.json' -o -name 'pnpm-lock.yaml' -o -name 'yarn.lock' -o -name 'composer.lock' -o -name 'style.css' \) \
      -print0 | LC_ALL=C sort -z | xargs -0 shasum 2>/dev/null || true
  )"
  candidate_id="$(printf '%s' "${candidate_material}" | shasum -a 256 | awk '{print $1}')"
else
  printf 'FAIL: candidate is not a git worktree\n' >&2
  exit 1
fi

printf '# Fashion Theme Candidate Report\n\n'
printf -- '- Candidate: `%s`\n' "${candidate_id}"
printf -- '- Commit: `%s`\n' "${commit_id}"
printf -- '- Repository: `%s`\n' "${candidate_root}"
printf -- '- Status: `BLOCKED` pending attached gate evidence\n\n'
printf '## Required evidence\n\n'
printf -- '- Fashion Theme Brain routes, source freshness, and claim classifications\n'
printf -- '- Page-by-page HTML visual contract and schema-valid JSON/evidence parity\n'
printf -- '- Merchandising, fit, service, and experiment contracts\n'
printf -- '- Design-system contract and adoption\n'
printf -- '- Build and source/generated parity\n'
printf -- '- WooCommerce customer journeys\n'
printf -- '- Responsive visual screenshots\n'
printf -- '- Accessibility and performance review\n'
printf -- '- Security, package integrity, deployment, and rollback approval\n'
printf '\nCandidate identity changes whenever tracked patch, untracked inventory, locks, or theme metadata changes.\n'
