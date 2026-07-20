#!/bin/bash
# Baseline Lighthouse sweep — every distinct skyyrose.co template, mobile + desktop.
# Output: tasks/wp-commercial-theme/baseline/<slug>.<form>.json + summary.csv
set -u
cd "$(dirname "$0")" || exit 1
OUT=round3
CSV=$OUT/summary.csv
echo "url,form,perf,a11y,bp,seo,lcp_ms,cls,tbt_ms" > "$CSV"

slugify() {
  echo "$1" | sed -e 's|https://skyyrose.co/||' -e 's|/$||' -e 's|/|_|g' -e 's|^$|home|'
}

while IFS= read -r url; do
  slug=$(slugify "$url")
  for form in mobile desktop; do
    preset=""
    [ "$form" = "desktop" ] && preset="--preset=desktop"
    json="$OUT/${slug}.${form}.json"
    npx --yes lighthouse "$url" $preset \
      --output=json --output-path="$json" \
      --chrome-flags="--headless=new" --quiet \
      --max-wait-for-load=45000 >/dev/null 2>&1
    if [ -s "$json" ]; then
      python3 - "$url" "$form" "$json" >> "$CSV" <<'PY'
import json, sys
url, form, path = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(path))
c = d.get("categories", {})
a = d.get("audits", {})
def score(k):
    v = c.get(k, {}).get("score")
    return round(v * 100) if v is not None else ""
def num(k):
    v = a.get(k, {}).get("numericValue")
    return round(v, 3) if v is not None else ""
print(f"{url},{form},{score('performance')},{score('accessibility')},{score('best-practices')},{score('seo')},{num('largest-contentful-paint')},{num('cumulative-layout-shift')},{num('total-blocking-time')}")
PY
    else
      echo "$url,$form,ERR,,,,,," >> "$CSV"
    fi
  done
done < pages.txt
echo "BASELINE_DONE $(wc -l < "$CSV") rows"
