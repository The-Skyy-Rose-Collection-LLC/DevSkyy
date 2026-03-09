#!/bin/bash
#
# Fix broken luxury cursor JS by restoring native cursors via WP Custom CSS.
# Run from any terminal with WP-CLI access to the site.
#
# Usage: bash scripts/fix-cursor.sh
#

set -euo pipefail

echo "Checking current custom CSS..."

wp eval '
$existing = wp_get_custom_css();

$fix = "
/* FIX: Restore native cursor — luxury cursor JS is broken */
body, html, body * { cursor: auto !important; }
a, button, [role=\"button\"], input[type=\"submit\"],
label, select, .hotspot-dot, .hotspot-dot * { cursor: pointer !important; }
input[type=\"text\"], input[type=\"email\"], input[type=\"search\"],
textarea, [contenteditable] { cursor: text !important; }
";

if (strpos($existing, "Restore native cursor") === false) {
    wp_update_custom_css_post($existing . $fix);
    echo "DONE — cursor fix applied";
} else {
    echo "ALREADY APPLIED — no changes made";
}
'

echo "Flushing cache..."
wp cache flush

echo "Complete."
