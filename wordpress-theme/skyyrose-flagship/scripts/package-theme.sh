#!/usr/bin/env bash

set -euo pipefail

THEME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THEME_PARENT="$(dirname "$THEME_DIR")"
REPO_ROOT="$(cd "$THEME_DIR/../.." && pwd)"
VERSION="$(sed -n 's/^Version:[[:space:]]*//p' "$THEME_DIR/style.css" | head -1)"
OUTPUT_DIR="$REPO_ROOT/output/releases"
OUTPUT_FILE="$OUTPUT_DIR/skyyrose-$VERSION.zip"

if [[ -z "$VERSION" ]]; then
	echo "Theme version missing from style.css." >&2
	exit 1
fi

if [[ -e "$OUTPUT_FILE" ]]; then
	echo "Release already exists: $OUTPUT_FILE" >&2
	exit 1
fi

mkdir -p "$OUTPUT_DIR"

(
	cd "$THEME_PARENT"
	zip -q -r "$OUTPUT_FILE" skyyrose-flagship \
		-x '*/.DS_Store' \
		-x '*/.gitignore' \
		-x '*/AGENTS.md' \
		-x '*/CLAUDE*.md' \
		-x '*/DELETION_LOG.md' \
		-x '*/VERIFICATION_LOG.md' \
		-x '*/node_modules/*' \
		-x '*/vendor/*' \
		-x '*/tests/*' \
		-x '*/test-results/*' \
		-x '*/phpstan/*' \
		-x '*/phpstan.neon' \
		-x '*/phpstan-baseline.neon' \
		-x '*/phpunit.xml.dist' \
		-x '*/.phpcs.xml' \
		-x '*/.phpunit.result.cache' \
		-x '*/*.map' \
		-x '*/*.bak-*'
)

echo "$OUTPUT_FILE"
