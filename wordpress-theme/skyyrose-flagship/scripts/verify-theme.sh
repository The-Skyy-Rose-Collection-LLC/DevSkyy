#!/usr/bin/env bash
# verify-theme.sh — executable, per-aspect quality gate for the SkyyRose fashion theme.
#
# Purpose: give an agent (or CI, or a human) a way to VERIFY each aspect it can
# execute — a check that can actually FAIL — instead of asserting a green it never
# observed. Each aspect is an addressable check id. CLI-verifiable aspects run for
# real; aspects that need a browser or human vision are marked SKIP with the reason,
# so a passing run can never fake coverage it doesn't have.
#
# Usage:
#   bash scripts/verify-theme.sh                 # run every aspect, table output
#   bash scripts/verify-theme.sh --only min-sync # run one aspect
#   bash scripts/verify-theme.sh --list          # list aspect ids + what they prove
#   bash scripts/verify-theme.sh --json          # machine-readable (for a build report)
#   bash scripts/verify-theme.sh --url URL        # also run Lighthouse CWV against URL
#
# Exit code: 0 if no FAIL, 1 if any aspect FAILs. WARN/SKIP never fail the run.
#
# Run from the theme root (wordpress-theme/skyyrose-flagship) or pass --theme DIR.
set -uo pipefail

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEME="$(cd "$SCRIPT_DIR/.." && pwd)"   # default: parent of scripts/
ONLY=""; JSON=0; URL=""; LIST=0
while [ $# -gt 0 ]; do
  case "$1" in
    --theme) THEME="$(cd "$2" && pwd)"; shift 2;;
    --only)  ONLY="$2"; shift 2;;
    --url)   URL="$2"; shift 2;;
    --json)  JSON=1; shift;;
    --list)  LIST=1; shift;;
    -h|--help) sed -n '2,20p' "$0"; exit 0;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done
cd "$THEME" || { echo "theme dir not found: $THEME" >&2; exit 2; }

# Find delivered PHP (excludes vendor/node_modules/test coverage).
find_php() { find . -name '*.php' -not -path './vendor/*' -not -path './node_modules/*' -not -path '*/tests/coverage/*'; }

FAILS=0; WARNS=0; ROWS=()
# record STATUS ID DETAIL
record() {
  local st="$1" id="$2"; shift 2; local detail="$*"
  [ "$st" = FAIL ] && FAILS=$((FAILS+1))
  [ "$st" = WARN ] && WARNS=$((WARNS+1))
  ROWS+=("$st|$id|$detail")
  if [ "$JSON" = 0 ]; then
    local c=""; local r=$'\033[0m'
    case "$st" in PASS) c=$'\033[32m';; FAIL) c=$'\033[31m';; WARN) c=$'\033[33m';; SKIP) c=$'\033[2m';; esac
    printf "%b[%-4s]%b %-22s %s\n" "$c" "$st" "$r" "$id" "$detail"
  fi
}
# should this aspect run given --only?
want() { [ -z "$ONLY" ] || [ "$ONLY" = "$1" ]; }

# ---------------------------------------------------------------------------
# --list
# ---------------------------------------------------------------------------
if [ "$LIST" = 1 ]; then
  cat <<'EOF'
Aspect ids (CLI = agent executes it · BROWSER/VISION = agent flags for caller):

  php-syntax        CLI      php -l on every delivered .php — zero parse errors
  phpcs             CLI      WordPress+WooCommerce coding standards (.phpcs.xml)
  phpstan           CLI      static analysis at the configured level
  style-header      CLI      style.css has Name/Version/License/Text Domain/Tags
  screenshot        CLI      screenshot.png present, >= 1200x900
  templates         CLI      required templates + WooCommerce overrides exist
  wc-support        CLI      add_theme_support(woocommerce) + gallery zoom/lightbox/slider
  min-sync          CLI      every source css/js has a .min sibling, none stale
  no-placeholders   CLI      no TODO/FIXME/lorem/"Coming soon"/PLACEHOLDER in delivered code
  no-secrets        CLI      no hard-coded api keys / passwords / consumer keys
  i18n-domain       CLI      translation calls use the 'skyyrose' text domain
  pot               CLI      languages/*.pot translation template present
  file-size         CLI      no delivered .php over 800 lines
  json-manifests    CLI      asset-manifest.json / theme.json parse as valid JSON
  escaping          CLI      advisory: raw `echo $var` in templates without esc_* (WARN)
  a11y-static       CLI      advisory: <img> missing alt, missing lang attr, skip-link (WARN)
  cwv               BROWSER  Lighthouse LCP/CLS/TBT — runs only with --url + lighthouse CLI
  responsive        BROWSER  390px + desktop render — caller runs Playwright/Chrome DevTools
  a11y-interactive  BROWSER  keyboard/focus/contrast — caller runs axe + manual
  product-fidelity  VISION   garment ↔ SKU pixel match — caller/agent reads pixels vs catalog
EOF
  exit 0
fi

# ===========================================================================
# CLI-EXECUTABLE ASPECTS
# ===========================================================================

if want php-syntax; then
  errs=0; n=0
  while IFS= read -r f; do
    n=$((n+1))
    php -l "$f" >/dev/null 2>&1 || { errs=$((errs+1)); [ "$JSON" = 0 ] && php -l "$f" 2>&1 | grep -i 'error' | head -1; }
  done < <(find_php)
  if [ "$errs" -eq 0 ]; then record PASS php-syntax "$n files, 0 parse errors"
  else record FAIL php-syntax "$errs of $n files have PHP parse errors"; fi
fi

if want phpcs; then
  if [ -x vendor/bin/phpcs ] && [ -f .phpcs.xml ]; then
    # phpcs exits non-zero for warnings too, so exit status alone cannot tell
    # "7 errors" from "0 errors, 7 warnings" — reporting the latter as FAIL
    # with "(0 ERROR)" is incoherent and trains people to ignore the gate.
    # Parse the totals line and grade errors and warnings separately.
    vendor/bin/phpcs --standard=.phpcs.xml -q --report=summary . >/tmp/vt_phpcs.txt 2>&1
    totals=$(grep -oE 'A TOTAL OF [0-9]+ ERRORS? AND [0-9]+ WARNINGS?' /tmp/vt_phpcs.txt | head -1)
    if [ -z "$totals" ]; then
      # No totals line = phpcs found nothing at all.
      record PASS phpcs "no coding-standard violations"
    else
      pe=$(printf '%s' "$totals" | awk '{print $4}')
      pw=$(printf '%s' "$totals" | awk '{print $7}')
      if [ "${pe:-0}" -gt 0 ]; then
        record FAIL phpcs "$pe error(s), ${pw:-0} warning(s) — run: vendor/bin/phpcs --standard=.phpcs.xml -s . (phpcbf fixes most)"
      elif [ "${pw:-0}" -gt 0 ]; then
        record WARN phpcs "0 errors, $pw warning(s) — vendor/bin/phpcbf --standard=.phpcs.xml <file>"
      else
        record PASS phpcs "no coding-standard violations"
      fi
    fi
  else
    record SKIP phpcs "phpcs not installed — cd $THEME && composer install"
  fi
fi

if want phpstan; then
  cfg=""; [ -f phpstan.neon ] && cfg="phpstan.neon"; [ -f phpstan.neon.dist ] && cfg="phpstan.neon.dist"
  if [ -x vendor/bin/phpstan ] && [ -n "$cfg" ]; then
    # XDEBUG_MODE=off: Xdebug inflates PHPStan's memory an order of magnitude.
    # --memory-limit: php.ini defaults to 128M here; the WordPress + WooCommerce
    # stub files alone are ~8.6MB of source, so a default run dies mid-analysis.
    # A crash is NOT a clean run and NOT a findings list — report it separately,
    # otherwise a broken config reads as "code has errors" and gets ignored.
    if XDEBUG_MODE=off vendor/bin/phpstan analyse -c "$cfg" --no-progress \
         --memory-limit="${PHPSTAN_MEMORY_LIMIT:-2G}" >/tmp/vt_phpstan.txt 2>&1; then
      record PASS phpstan "static analysis clean ($cfg)"
    elif grep -qE 'memory limit|Child process error|Invalid entry in|not a directory, nor a file' /tmp/vt_phpstan.txt; then
      why=$(grep -oE 'Invalid entry in [a-zA-Z]+|reached configured PHP memory limit: [0-9]+[MG]' /tmp/vt_phpstan.txt | head -1)
      record FAIL phpstan "phpstan COULD NOT RUN (${why:-see /tmp/vt_phpstan.txt}) — config/env problem, not a findings list"
    else
      n=$(grep -oE '\[ERROR\] Found [0-9]+ error' /tmp/vt_phpstan.txt | grep -oE '[0-9]+' | head -1)
      record FAIL phpstan "${n:-?} static-analysis errors — run: XDEBUG_MODE=off vendor/bin/phpstan analyse -c $cfg --memory-limit=2G"
    fi
  else
    record SKIP phpstan "phpstan not installed or no config"
  fi
fi

if want style-header; then
  miss=""
  for field in "Theme Name" "Version" "License" "Text Domain" "Tags"; do
    grep -qiE "^${field}:" style.css 2>/dev/null || miss="$miss $field"
  done
  if [ -z "$miss" ]; then
    ver=$(grep -iE '^Version:' style.css | head -1 | sed -E 's/^[^:]*:[[:space:]]*//')
    record PASS style-header "all required fields present (Version $ver)"
  else record FAIL style-header "style.css missing:$miss"; fi
fi

if want screenshot; then
  if [ -f screenshot.png ]; then
    w=0; h=0
    if command -v sips >/dev/null 2>&1; then
      w=$(sips -g pixelWidth screenshot.png 2>/dev/null | awk '/pixelWidth/{print $2}')
      h=$(sips -g pixelHeight screenshot.png 2>/dev/null | awk '/pixelHeight/{print $2}')
    elif command -v identify >/dev/null 2>&1; then
      read -r w h < <(identify -format '%w %h' screenshot.png 2>/dev/null)
    fi
    if [ "${w:-0}" -ge 1200 ] && [ "${h:-0}" -ge 900 ]; then
      record PASS screenshot "screenshot.png ${w}x${h}"
    else
      record FAIL screenshot "screenshot.png ${w:-?}x${h:-?} — need >= 1200x900"
    fi
  else record FAIL screenshot "screenshot.png missing"; fi
fi

if want templates; then
  miss=""
  for t in index.php front-page.php 404.php header.php footer.php page.php archive.php \
           woocommerce/single-product.php woocommerce/archive-product.php; do
    [ -f "$t" ] || miss="$miss $t"
  done
  # cart + checkout may be dirs (block templates) or files
  for base in woocommerce/cart woocommerce/checkout; do
    { [ -e "$base" ] || [ -e "$base.php" ]; } || miss="$miss $base"
  done
  if [ -z "$miss" ]; then record PASS templates "funnel templates + WC overrides present"
  else record FAIL templates "missing:$miss"; fi
fi

if want wc-support; then
  ok=1; d=""
  grep -rql "add_theme_support( 'woocommerce'" --include='*.php' inc functions.php 2>/dev/null || { ok=0; d="$d no woocommerce support;"; }
  for g in wc-product-gallery-zoom wc-product-gallery-lightbox wc-product-gallery-slider; do
    grep -rql "$g" --include='*.php' inc functions.php 2>/dev/null || { ok=0; d="$d no $g;"; }
  done
  if [ "$ok" = 1 ]; then record PASS wc-support "woocommerce + gallery zoom/lightbox/slider declared"
  else record FAIL wc-support "$d"; fi
fi

if want min-sync; then
  # Compare CONTENT, not mtime, by re-running the real build in --check mode
  # (writes nothing). mtime is not evidence: a git checkout or `touch` reorders
  # mtimes without changing a byte. The old mtime check was wrong in BOTH
  # directions — it FAILed a design-tokens.min.css that was perfectly in sync,
  # and PASSed a style.min.css that still shipped Version 1.12.7 against a
  # 1.12.8 source. Delegating to the build scripts also keeps the CleanCSS /
  # terser options in one place; a copy here would drift and false-report.
  if ! command -v node >/dev/null 2>&1; then
    record SKIP min-sync "node not available — cannot re-derive minified output"
  else
    # Deliberately no scraped asset count in the PASS detail: parsing a number
    # out of the child's log means a reworded log line yields "0 assets" and
    # still PASSes — a fail-open path, the exact defect this aspect exists to
    # prevent. The child's exit status is the signal; nothing else is trusted.
    bad=""; ran=0
    for s in scripts/build-css.js scripts/build-js.js; do
      [ -f "$s" ] || continue
      ran=1
      if ! out=$(node "$s" --check 2>&1); then
        bad="$bad"$'\n'"$(printf '%s' "$out" | grep -vE '^\[build:(css|js) --check\] Run:')"
      fi
    done
    if [ "$ran" = 0 ]; then record FAIL min-sync "no build scripts found — cannot verify .min freshness"
    elif [ -z "$bad" ]; then record PASS min-sync "every .min css/js byte-identical to a fresh build"
    else record FAIL min-sync "${bad} — run: npm run build"; fi
  fi
fi

if want no-placeholders; then
  # Two tiers, because "placeholder" means two different things:
  #
  #  1. developer markers — unfinished work. Fail anywhere, no exemptions.
  #  2. content placeholders — only a defect in UNSHIPPED copy. A string wrapped
  #     in a translation call is shipped copy by construction (a maintenance
  #     page legitimately reads "Coming soon"), so those are excluded here
  #     rather than via a path allowlist, which would rot.
  #
  # Note "XXX" is deliberately NOT a marker: this is a fashion theme where XXL /
  # XXXL are real size labels.
  # Intentional empty states are a design question a grep cannot settle — that
  # stays with the caller (see the responsive / product-fidelity SKIP aspects).
  scan_args=(--include='*.php' --include='*.css' --include='*.js'
             --exclude='*.min.css' --exclude='*.min.js'
             --exclude-dir=vendor --exclude-dir=node_modules --exclude-dir=lib --exclude-dir=tests)
  dev_hits=$(grep -rInE "\b(TODO|FIXME|HACK)\b|@stub|NotImplemented|dummy data" "${scan_args[@]}" . 2>/dev/null | wc -l | tr -d ' ')
  content_hits=$(grep -rInE "lorem ipsum|PLACEHOLDER|Coming soon" "${scan_args[@]}" . 2>/dev/null \
                 | grep -cvE "(__|_e|_x|_n|esc_html__|esc_html_e|esc_attr__|esc_attr_e)\(")
  total=$(( ${dev_hits:-0} + ${content_hits:-0} ))
  if [ "$total" -eq 0 ]; then
    record PASS no-placeholders "no dev markers; no untranslated placeholder copy"
  else
    record FAIL no-placeholders "${dev_hits} dev marker(s) (TODO/FIXME/HACK/@stub), ${content_hits} untranslated placeholder string(s)"
  fi
fi

if want no-secrets; then
  # strong heuristics only, to avoid false positives
  hits=$(grep -rInE "(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ck_[a-f0-9]{30,}|cs_[a-f0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)" \
         --include='*.php' --include='*.js' --include='*.json' \
         --exclude-dir=vendor --exclude-dir=node_modules . 2>/dev/null | wc -l | tr -d ' ')
  if [ "${hits:-0}" -eq 0 ]; then record PASS no-secrets "no hard-coded key/secret literals detected"
  else record FAIL no-secrets "$hits possible hard-coded secret(s) — rotate + move to env"; fi
fi

if want i18n-domain; then
  # translation calls whose domain arg is a quoted string other than 'skyyrose'
  wrong=$(grep -rhoE "(__|_e|_x|_n|esc_html__|esc_html_e|esc_attr__|esc_attr_e)\([^)]*,[[:space:]]*'[^']+'[[:space:]]*\)" \
          --include='*.php' --exclude-dir=vendor --exclude-dir=node_modules inc . 2>/dev/null \
          | grep -oE "'[^']+'[[:space:]]*\)$" | grep -cvE "'skyyrose'")
  has_load=$(grep -rl "load_theme_textdomain\|load_textdomain" --include='*.php' . 2>/dev/null | head -1)
  if [ "${wrong:-0}" -eq 0 ] && [ -n "$has_load" ]; then
    record PASS i18n-domain "translation calls use 'skyyrose'; textdomain loaded"
  elif [ -z "$has_load" ]; then record WARN i18n-domain "no load_theme_textdomain() found"
  else record WARN i18n-domain "$wrong translation call(s) use a non-skyyrose domain"; fi
fi

if want pot; then
  if ls languages/*.pot >/dev/null 2>&1; then record PASS pot "$(ls languages/*.pot | head -1) present"
  else record FAIL pot "no languages/*.pot — generate with wp i18n make-pot"; fi
fi

if want file-size; then
  big=$(find_php | while IFS= read -r f; do
          n=$(wc -l < "$f"); [ "$n" -gt 800 ] && echo "  $f ($n lines)"; done)
  if [ -z "$big" ]; then record PASS file-size "no delivered .php over 800 lines"
  else record FAIL file-size "over 800-line limit:$(printf "\n%s" "$big")"; fi
fi

if want json-manifests; then
  bad=""
  for j in asset-manifest.json theme.json; do
    [ -f "$j" ] || continue
    if command -v python3 >/dev/null 2>&1; then
      python3 -c "import json,sys;json.load(open('$j'))" 2>/dev/null || bad="$bad $j"
    fi
  done
  if [ -z "$bad" ]; then record PASS json-manifests "manifests parse as valid JSON"
  else record FAIL json-manifests "invalid JSON:$bad"; fi
fi

if want escaping; then
  # advisory: echo of a bare variable in a template without an esc_* wrapper
  hits=$(grep -rInE "echo[[:space:]]+\\\$[A-Za-z_]" \
         --include='*.php' --exclude-dir=vendor --exclude-dir=node_modules \
         woocommerce parts template-parts patterns . 2>/dev/null \
         | grep -cvE "esc_html|esc_attr|esc_url|wp_kses|esc_textarea|absint|intval|(int)")
  if [ "${hits:-0}" -eq 0 ]; then record PASS escaping "no obvious unescaped echo in templates"
  else record WARN escaping "$hits possible unescaped 'echo \$var' — review for esc_*()"; fi
fi

if want a11y-static; then
  d=""
  # <img ... > without alt= in delivered php templates.
  #
  # The former line-based grep was wrong in BOTH directions and reported a fixed 72
  # forever: it counted <img> inside comments/docblocks and multi-line tags whose alt=
  # sat on the following line (false positives), while missing tags whose opening line
  # contained no '>' at all (false negatives). Audited 2026-07-27: all 72 were false,
  # zero real missing-alt defects.
  #
  # Parsing, not line-matching. Order matters: PHP blocks are stripped FIRST, because
  # `<img src="<?php echo esc_url( $u ); ?>" alt="x">` has its first '>' inside `?>`,
  # which is what truncated the tag and hid the alt.
  if command -v php >/dev/null 2>&1; then
    # token_get_all() distinguishes real inline HTML from PHP string/regex
    # literals. Regex-stripping PHP cannot do that reliably when a PHP string
    # itself contains tag-like text or `?>`.
    noalt=$(php <<'PHPEOF'
<?php
$iterator = new RecursiveIteratorIterator(
	new RecursiveCallbackFilterIterator(
		new RecursiveDirectoryIterator( '.', FilesystemIterator::SKIP_DOTS ),
		static function ( SplFileInfo $current ): bool {
			return ! $current->isDir() || ! in_array( $current->getFilename(), array( 'vendor', 'node_modules' ), true );
		}
	)
);
$count = 0;
foreach ( $iterator as $file ) {
	if ( 'php' !== strtolower( $file->getExtension() ) ) {
		continue;
	}
	$html = '';
	foreach ( token_get_all( (string) file_get_contents( $file->getPathname() ) ) as $token ) {
		if ( is_array( $token ) && T_INLINE_HTML === $token[0] ) {
			$html .= $token[1];
		}
	}
	$html = preg_replace( '/<!--.*?-->/s', ' ', $html );
	preg_match_all( '/<img\b[^>]*>/is', (string) $html, $tags );
	foreach ( $tags[0] as $tag ) {
		if ( ! preg_match( '/\balt\s*=/i', $tag ) ) {
			++$count;
		}
	}
}
echo $count;
PHPEOF
)
  else
    noalt=$(grep -rInE "<img[^>]*>" --include='*.php' --exclude-dir=vendor --exclude-dir=node_modules . 2>/dev/null \
            | grep -civE "alt=")
  fi
  [ "${noalt:-0}" -gt 0 ] && d="$d ${noalt} <img> without alt;"
  grep -rq "language_attributes\|<html[^>]*lang=" header.php 2>/dev/null || d="$d no lang attr in header;"
  grep -rq "skip-link\|skip-to-content\|screen-reader-shortcut" --include='*.php' . 2>/dev/null || d="$d no skip-link;"
  if [ -z "$d" ]; then record PASS a11y-static "img alt / lang attr / skip-link present"
  else record WARN a11y-static "$d (interactive a11y still needs a browser)"; fi
fi

# ===========================================================================
# BROWSER / VISION ASPECTS
# cwv runs IF a --url + lighthouse are available (agent can drive it via Bash);
# otherwise SKIP. responsive / a11y-interactive / product-fidelity always SKIP —
# they need a browser MCP or human vision the agent's toolset can't execute.
# ===========================================================================

if want cwv; then
  if [ -n "$URL" ] && command -v npx >/dev/null 2>&1 && npx --no-install lighthouse --version >/dev/null 2>&1; then
    out=/tmp/vt_lh.json
    if npx --no-install lighthouse "$URL" --quiet --only-categories=performance \
         --chrome-flags="--headless --no-sandbox" --output=json --output-path="$out" >/dev/null 2>&1; then
      score=$(python3 -c "import json;print(round(json.load(open('$out'))['categories']['performance']['score']*100))" 2>/dev/null)
      lcp=$(python3 -c "import json;print(json.load(open('$out'))['audits']['largest-contentful-paint']['displayValue'])" 2>/dev/null)
      cls=$(python3 -c "import json;print(json.load(open('$out'))['audits']['cumulative-layout-shift']['displayValue'])" 2>/dev/null)
      if [ "${score:-0}" -ge 80 ]; then record PASS cwv "perf $score/100 · LCP $lcp · CLS $cls"
      else record FAIL cwv "perf $score/100 (<80) · LCP $lcp · CLS $cls"; fi
    else record SKIP cwv "lighthouse run failed (chrome headless unavailable?)"; fi
  else
    record SKIP cwv "needs --url + lighthouse CLI (npx lighthouse); caller runs Chrome DevTools lighthouse_audit"
  fi
fi

want responsive       && record SKIP responsive       "needs-browser — caller: Playwright/Chrome DevTools screenshot at 390px + desktop, read console"
want a11y-interactive  && record SKIP a11y-interactive  "needs-browser — caller: axe-core + keyboard/focus/contrast pass"
want product-fidelity  && record SKIP product-fidelity  "needs-vision — read pixels vs catalog/dossier per SKU (SOT), never the filename"

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
if [ "$JSON" = 1 ]; then
  printf '{'
  printf '"theme":"%s","fails":%d,"warns":%d,"checks":[' "$(basename "$THEME")" "$FAILS" "$WARNS"
  first=1
  for row in "${ROWS[@]}"; do
    IFS='|' read -r st id detail <<<"$row"
    detail=${detail//\\/\\\\}; detail=${detail//\"/\\\"}; detail=${detail//$'\n'/ }
    [ $first = 1 ] || printf ','; first=0
    printf '{"id":"%s","status":"%s","detail":"%s"}' "$id" "$st" "$detail"
  done
  printf ']}\n'
else
  echo "------------------------------------------------------------"
  if [ "$FAILS" -eq 0 ]; then
    printf "\033[32mVERIFY PASS\033[0m — 0 fail, %d warn. (SKIP = needs browser/vision; verify those separately.)\n" "$WARNS"
  else
    printf "\033[31mVERIFY FAIL\033[0m — %d fail, %d warn. Fix the FAILs above.\n" "$FAILS" "$WARNS"
  fi
fi
[ "$FAILS" -eq 0 ]
