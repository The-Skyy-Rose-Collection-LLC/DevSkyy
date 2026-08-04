#!/usr/bin/env bash
# Build a marketplace-installable archive from tracked theme files.
set -euo pipefail

theme_name="skyyrose-flagship-2"
theme_dir="wordpress-theme/${theme_name}"
repo_root="$(git rev-parse --show-toplevel)"
output_dir="${1:-${repo_root}/dist}"
stage_dir="$(mktemp -d)"

cleanup() {

	rm -rf "${stage_dir}"
}
trap cleanup EXIT

mkdir -p "${output_dir}"
mkdir -p "${stage_dir}/${theme_name}"

# Archive HEAD so ignored editor files, local dependencies, and uncommitted
# experiments cannot be accidentally shipped.
git -C "${repo_root}" archive HEAD:"${theme_dir}" | tar -x -C "${stage_dir}/${theme_name}"

archive_path="${output_dir}/${theme_name}.zip"
rm -f "${archive_path}"
(
	cd "${stage_dir}"
	zip -qr "${archive_path}" "${theme_name}"
)

printf 'Created %s\n' "${archive_path}"
