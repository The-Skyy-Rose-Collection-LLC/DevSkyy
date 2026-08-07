#!/usr/bin/env bash
set -euo pipefail

repo_root="${1:-${PWD}}"
requested_theme="${2:-}"

if [[ ! -d "${repo_root}" ]]; then
  printf 'FAIL: repository path does not exist: %s\n' "${repo_root}" >&2
  exit 1
fi

if [[ ! -d "${repo_root}/.git" ]] && [[ ! -f "${repo_root}/.git" ]]; then
  printf 'FAIL: not a git repository or worktree: %s\n' "${repo_root}" >&2
  exit 1
fi

theme_count=0
if [[ -d "${repo_root}/wordpress-theme" ]]; then
  while IFS= read -r style_file; do
    theme_count=$((theme_count + 1))
    printf 'theme: %s\n' "${style_file%/style.css}"
  done < <(find "${repo_root}/wordpress-theme" -mindepth 2 -maxdepth 2 -type f -name style.css -print)
elif [[ -f "${repo_root}/style.css" ]]; then
  theme_count=1
  printf 'theme: %s\n' "${repo_root}"
fi

if [[ -n "${requested_theme}" ]] && [[ ! -f "${requested_theme}/style.css" ]]; then
  printf 'FAIL: requested theme has no style.css: %s\n' "${requested_theme}" >&2
  exit 1
fi

if [[ "${theme_count}" -eq 0 ]]; then
  printf 'FAIL: no WordPress theme style.css found\n' >&2
  exit 1
fi

for command_name in git bash jq shasum; do
  command -v "${command_name}" >/dev/null 2>&1 || {
    printf 'FAIL: required command unavailable: %s\n' "${command_name}" >&2
    exit 1
  }
done

printf 'capabilities:\n'
for command_name in php node npm pnpm yarn composer wp playwright npx shellcheck; do
  if command -v "${command_name}" >/dev/null 2>&1; then
    printf '  %s: available\n' "${command_name}"
  else
    printf '  %s: unavailable\n' "${command_name}"
  fi
done

if [[ -n "$(git -C "${repo_root}" status --porcelain 2>/dev/null)" ]]; then
  printf 'WARN: repository has existing changes; isolate ownership before edits\n'
fi

for source_name in AGENTS.md SOT.md .wolf/memory.md package.json composer.json; do
  [[ -e "${repo_root}/${source_name}" ]] && printf 'source: %s\n' "${repo_root}/${source_name}"
done

printf 'PASS: operational preflight found %d theme candidate(s)\n' "${theme_count}"
