#!/usr/bin/env bash
# Build a marketplace-installable archive from tracked theme files.
set -euo pipefail

theme_name="skyyrose-flagship-2"
theme_dir="wordpress-theme/${theme_name}"
repo_root="$(git rev-parse --show-toplevel)"
output_dir="${1:-${repo_root}/dist}"
archive_path="${output_dir}/${theme_name}.zip"
temporary_archive="${archive_path}.tmp"

cleanup() {
	rm -f "${temporary_archive}"
}
trap cleanup EXIT

mkdir -p "${output_dir}"

# Archive HEAD so ignored editor files, local dependencies, and uncommitted
# experiments cannot be accidentally shipped. Git fixes archive member times to
# the commit time, so equivalent clean-HEAD builds are byte-for-byte identical.
git -C "${repo_root}" archive \
	--format=zip \
	--prefix="${theme_name}/" \
	--output="${temporary_archive}" \
	HEAD:"${theme_dir}"
mv -f "${temporary_archive}" "${archive_path}"

printf 'Created %s\n' "${archive_path}"
