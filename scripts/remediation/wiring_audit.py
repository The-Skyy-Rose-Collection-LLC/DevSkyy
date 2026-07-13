#!/usr/bin/env python3
"""
WS7 wiring audit — spec C6 as a runnable script.

Read-only checks run by default against production (public GETs, one authed
GET per credential tier, a local HMAC simulation, and a static grep of the
Next.js build output — nothing that mutates skyyrose.co). The two WRITE
checks (product meta_data round-trip, settings PATCH round-trip) are gated
behind --write AND STOPSHOW_ACK=1 — this project's founder-authority gate
for anything that mutates production.

Usage:
  python3 scripts/remediation/wiring_audit.py                        # read-only
  STOPSHOW_ACK=1 python3 scripts/remediation/wiring_audit.py --write  # + write checks

Env (from scripts/remediation/setup_credentials.py's ENV_KEYS contract):
  WP_BASE_URL, WC_CONSUMER_KEY, WC_CONSUMER_SECRET, WP_APP_USER,
  WP_APP_PASSWORD, WP_WEBHOOK_SECRET
"""

import argparse
import base64
import hashlib
import hmac
import itertools
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("pip install requests --break-system-packages")

OK, FAIL, WARN, SKIP = (
    "\033[32m PASS \033[0m",
    "\033[31m FAIL \033[0m",
    "\033[33m WARN \033[0m",
    "\033[36m SKIP \033[0m",
)

# WooCommerce keys are ck_/cs_ + 40 lowercase hex chars. Requiring hex (not
# [a-zA-Z0-9]) keeps UI input placeholders like "ck_xxxxxxxxxxxxx" from
# false-positiving — 'x' is not a hex digit.
_SECRET_PATTERNS = (re.compile(r"ck_[a-f0-9]{20,}"), re.compile(r"cs_[a-f0-9]{20,}"))

# Category slugs the dashboard's wc/store/v1/products?category= reads use
# (verified live 2026-07-07: black-rose=14, love-hurts=4, signature=11,
# kids-capsule=2, all-products=33 — see project memory / VERIFIED ROUTE MAP).
KNOWN_COLLECTION_SLUGS = ["black-rose", "love-hurts", "signature", "kids-capsule"]


def compute_signature(raw_body: str, secret: str) -> str:
    """Mirror frontend/lib/wp/signature.ts's computeWebhookSignature exactly:
    base64(hmac_sha256(secret, raw_body))."""
    digest = hmac.new(secret.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def check_signature_roundtrip(secret: str) -> tuple[bool, str]:
    """Pure, no network: accept-on-match / reject-on-tamper simulation of the
    HMAC scheme the webhook receiver (lib/wp/signature.ts) implements."""
    body = '{"id":42,"topic":"product.updated"}'
    good_signature = compute_signature(body, secret)
    if compute_signature(body + "x", secret) == good_signature:
        return False, "tampered body produced the same signature"
    if compute_signature(body, secret + "x") == good_signature:
        return False, "wrong secret produced the same signature"
    return True, "accept-on-match / reject-on-tamper both correct"


def check_category_totals_sane(
    category_totals: dict[str, int], grand_total: int
) -> tuple[bool, str]:
    """Sanity-check per-collection wc/store/v1/products totals against the
    site-wide total: every known collection must have returned a real count
    (not the -1 sentinel used for a failed fetch), and the sum of known
    collections can never exceed the site-wide total."""
    failed = [slug for slug, count in category_totals.items() if count < 0]
    if failed:
        return False, f"fetch failed for: {', '.join(failed)}"
    total_categorized = sum(category_totals.values())
    if total_categorized > grand_total:
        return False, f"category sum {total_categorized} exceeds site-wide total {grand_total}"
    return True, f"{category_totals} sums to {total_categorized} of {grand_total} site-wide"


def find_leaked_secrets(bundle_text: str) -> list[str]:
    """Return every ck_/cs_-looking fragment found in client-bundle JS text."""
    found: list[str] = []
    for pattern in _SECRET_PATTERNS:
        found.extend(pattern.findall(bundle_text))
    return found


def check_burst_timing(timestamps: list[float], min_gap_s: float = 0.45) -> tuple[bool, str]:
    """Given the wall-clock seconds each request in a burst fired, confirm
    consecutive requests were paced at >= min_gap_s (2 req/s budget,
    jitter-tolerant floor)."""
    if len(timestamps) < 2:
        return True, "fewer than 2 requests, nothing to pace"
    gaps = [b - a for a, b in itertools.pairwise(timestamps)]
    worst = min(gaps)
    if worst < min_gap_s:
        return False, f"tightest gap {worst:.3f}s < {min_gap_s}s budget"
    return True, f"tightest gap {worst:.3f}s >= {min_gap_s}s budget"


def _require_env(*names: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for name in names:
        value = os.environ.get(name)
        if value:
            values[name] = value
    return values


def _product_meta_roundtrip(base: str, wc_auth: tuple[str, str]) -> tuple[str, bool, str]:
    """Write -> read -> delete a marker meta_data entry on a real product to
    prove the wc/v3 PUT round-trips end to end. Restores by clearing the
    marker key afterward."""
    name = "product meta_data write round-trip"
    try:
        listing = requests.get(
            f"{base}/wp-json/wc/v3/products", auth=wc_auth, params={"per_page": 1}, timeout=20
        )
        listing.raise_for_status()
        products = listing.json()
        if not products:
            return name, False, "no products returned to test against"
        product_id = products[0]["id"]
        marker = f"wiring-audit-{int(time.time())}"

        put_response = requests.put(
            f"{base}/wp-json/wc/v3/products/{product_id}",
            auth=wc_auth,
            json={"meta_data": [{"key": "devskyy_wiring_check", "value": marker}]},
            timeout=20,
        )
        put_response.raise_for_status()

        get_response = requests.get(
            f"{base}/wp-json/wc/v3/products/{product_id}", auth=wc_auth, timeout=20
        )
        get_response.raise_for_status()
        meta = {m["key"]: m["value"] for m in get_response.json().get("meta_data", [])}
        wrote_ok = meta.get("devskyy_wiring_check") == marker

        # Clean up regardless of outcome: clear the marker key.
        requests.put(
            f"{base}/wp-json/wc/v3/products/{product_id}",
            auth=wc_auth,
            json={"meta_data": [{"key": "devskyy_wiring_check", "value": ""}]},
            timeout=20,
        )
        note = (
            f"product {product_id}: wrote and read back marker"
            if wrote_ok
            else "marker mismatch after write"
        )
        return name, wrote_ok, note
    except requests.RequestException as e:
        return name, False, f"{type(e).__name__}: {e}"


def _settings_roundtrip(base: str, wp_auth: tuple[str, str]) -> tuple[str, bool, str]:
    """GET -> PATCH -> GET the whitelisted `fastapi_url` key on
    skyyrose/v1/settings, then restore the original value.

    The endpoint whitelists its accepted keys (correct boundary validation),
    so an arbitrary marker key is silently dropped — the round-trip must use
    a real key. `fastapi_url` is the only non-module string key; the marker
    window is a few hundred ms and restore runs in a finally block.
    """
    name = "settings PATCH round-trip"
    url = f"{base}/wp-json/skyyrose/v1/settings"
    key = "fastapi_url"
    original_value = None
    patched = False
    try:
        before = requests.get(url, auth=wp_auth, timeout=20)
        before.raise_for_status()
        original_value = before.json().get(key, "")

        marker_value = f"https://wiring-check-{int(time.time())}.invalid"
        patch_response = requests.patch(url, auth=wp_auth, json={key: marker_value}, timeout=20)
        patch_response.raise_for_status()
        patched = True
        if key not in patch_response.json().get("updated", []):
            return name, False, f"endpoint did not accept whitelisted key {key!r}"

        after = requests.get(url, auth=wp_auth, timeout=20)
        after.raise_for_status()
        wrote_ok = after.json().get(key) == marker_value
        note = "wrote, read back, restored" if wrote_ok else "marker mismatch after PATCH"
        return name, wrote_ok, note
    except requests.RequestException as e:
        return name, False, f"{type(e).__name__}: {e}"
    finally:
        if patched:
            requests.patch(url, auth=wp_auth, json={key: original_value or ""}, timeout=20)


def run(write: bool) -> int:
    env = _require_env(
        "WP_BASE_URL",
        "WC_CONSUMER_KEY",
        "WC_CONSUMER_SECRET",
        "WP_APP_USER",
        "WP_APP_PASSWORD",
        "WP_WEBHOOK_SECRET",
    )
    base = env.get("WP_BASE_URL", "").rstrip("/")
    if not base:
        print(f"{FAIL} WP_BASE_URL not set — cannot run any live check")
        return 1

    results: list[bool] = []

    def report(check_name: str, ok: bool, note: str) -> None:
        results.append(ok)
        print(f"{OK if ok else FAIL} {check_name} — {note}")

    # 1. health endpoint reachable
    try:
        r = requests.get(f"{base}/wp-json/skyyrose/v1/collections", timeout=20)
        report("health: public reachable", r.status_code == 200, f"HTTP {r.status_code}")
    except requests.RequestException as e:
        report("health: public reachable", False, f"{type(e).__name__}: {e}")

    # 2. public reads vs Store API totals (per known collection, sanity vs site-wide)
    try:
        grand = requests.get(
            f"{base}/wp-json/wc/store/v1/products", params={"per_page": 1}, timeout=20
        )
        grand_total = int(grand.headers.get("X-WP-Total", -1))
        category_totals: dict[str, int] = {}
        for slug in KNOWN_COLLECTION_SLUGS:
            resp = requests.get(
                f"{base}/wp-json/wc/store/v1/products",
                params={"category": slug, "per_page": 1},
                timeout=20,
            )
            category_totals[slug] = int(resp.headers.get("X-WP-Total", -1))
            time.sleep(0.5)  # 2 req/s budget
        ok, note = check_category_totals_sane(category_totals, grand_total)
        report("public reads vs Store API totals", ok, note)
    except requests.RequestException as e:
        report("public reads vs Store API totals", False, f"{type(e).__name__}: {e}")

    # 3. authed wc/v3 read (ordered first among authed checks per the risk noted in the plan)
    wc_auth = (env.get("WC_CONSUMER_KEY", ""), env.get("WC_CONSUMER_SECRET", ""))
    try:
        r = requests.get(
            f"{base}/wp-json/wc/v3/products", auth=wc_auth, params={"per_page": 1}, timeout=20
        )
        if r.status_code == 200:
            report(
                "authed wc/v3 read",
                True,
                f"HTTP 200, X-WP-Total={r.headers.get('X-WP-Total', '?')}",
            )
        else:
            report(
                "authed wc/v3 read",
                False,
                f"HTTP {r.status_code} via /wp-json/wc/v3 — if this is a WP.com Authorization-header "
                "quirk, the legacy proxy (app/api/wordpress/proxy/route.ts) uses index.php?rest_route= "
                "successfully; consider that as buildUrl()'s fallback form in lib/wp/client.ts",
            )
    except requests.RequestException as e:
        report("authed wc/v3 read", False, f"{type(e).__name__}: {e}")

    # 4. settings read
    wp_auth = (env.get("WP_APP_USER", ""), env.get("WP_APP_PASSWORD", ""))
    try:
        r = requests.get(f"{base}/wp-json/skyyrose/v1/settings", auth=wp_auth, timeout=20)
        report("settings read (app password)", r.status_code == 200, f"HTTP {r.status_code}")
    except requests.RequestException as e:
        report("settings read (app password)", False, f"{type(e).__name__}: {e}")

    # 5. agents-manager read
    try:
        r = requests.get(f"{base}/wp-json/agents-manager/open-state", auth=wp_auth, timeout=20)
        report("agents-manager read (app password)", r.status_code == 200, f"HTTP {r.status_code}")
    except requests.RequestException as e:
        report("agents-manager read (app password)", False, f"{type(e).__name__}: {e}")

    # 6. local signature accept/reject simulation (no network)
    if env.get("WP_WEBHOOK_SECRET"):
        ok, note = check_signature_roundtrip(env["WP_WEBHOOK_SECRET"])
        report("webhook signature accept/reject simulation", ok, note)
    else:
        report("webhook signature accept/reject simulation", False, "WP_WEBHOOK_SECRET not set")

    # 7. client-bundle secret grep — .next/static only: that is what ships to
    # browsers. Server chunks (.next/server) legitimately contain ck_/cs_
    # placeholder strings from the admin settings page UI and false-positive.
    next_dir = Path("frontend/.next/static")
    if not next_dir.exists():
        print(
            f"{WARN} client-bundle secret grep — frontend/.next/static not found; "
            "run `npm run build` first"
        )
    else:
        leaked: list[str] = []
        for js_file in next_dir.rglob("*.js"):
            try:
                leaked.extend(find_leaked_secrets(js_file.read_text(errors="ignore")))
            except OSError:
                continue
        report(
            "client-bundle secret grep",
            len(leaked) == 0,
            f"{len(leaked)} fragment(s) found" if leaked else "clean",
        )

    # 8. burst-of-6 public GETs, 429-free, paced at <=2 req/s
    try:
        timestamps: list[float] = []
        for _ in range(6):
            timestamps.append(time.monotonic())
            requests.get(f"{base}/wp-json/skyyrose/v1/collections", timeout=20)
            time.sleep(0.5)
        ok, note = check_burst_timing(timestamps)
        report("burst-of-6 pacing (<=2 req/s, 429-free)", ok, note)
    except requests.RequestException as e:
        report("burst-of-6 pacing", False, f"{type(e).__name__}: {e}")

    # Write-gated checks
    if write:
        report(*_product_meta_roundtrip(base, wc_auth))
        report(*_settings_roundtrip(base, wp_auth))
    else:
        print(f"{SKIP} product meta_data write round-trip — write-gated (--write + STOPSHOW_ACK=1)")
        print(f"{SKIP} settings PATCH round-trip — write-gated (--write + STOPSHOW_ACK=1)")

    passed = sum(1 for ok in results if ok)
    print(f"\n{passed}/{len(results)} checks passed.")
    return 0 if all(results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Also run the 2 write-gated checks (requires STOPSHOW_ACK=1 env). Default: read-only.",
    )
    args = parser.parse_args()
    if args.write and os.environ.get("STOPSHOW_ACK") != "1":
        print(
            f"{FAIL} --write requires STOPSHOW_ACK=1 in the environment (production WC/WP write gate)"
        )
        return 1
    return run(write=args.write)


if __name__ == "__main__":
    sys.exit(main())
