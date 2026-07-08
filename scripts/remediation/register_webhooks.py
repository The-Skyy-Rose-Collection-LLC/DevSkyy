#!/usr/bin/env python3
"""
Idempotent WooCommerce webhook registration for the WS7 wiring core.

Registers the topics the dashboard needs (product + order changes) pointing
at the dashboard's HMAC-verified receiver
(frontend/app/api/webhooks/woocommerce/route.ts). Diffs against whatever
webhooks already exist so re-running never creates duplicates.

Usage:
  python3 scripts/remediation/register_webhooks.py                          # dry-run (default), prints the plan
  STOPSHOW_ACK=1 python3 scripts/remediation/register_webhooks.py --execute  # live write

Env (from scripts/remediation/setup_credentials.py's ENV_KEYS contract):
  WP_BASE_URL, WC_CONSUMER_KEY, WC_CONSUMER_SECRET, WP_WEBHOOK_SECRET
"""

import argparse
import os
import sys

try:
    import requests
except ImportError:
    sys.exit("pip install requests --break-system-packages")

DELIVERY_URL = "https://www.devskyy.app/api/webhooks/woocommerce"
TOPICS = [
    "product.created",
    "product.updated",
    "product.deleted",
    "order.created",
    "order.updated",
]


def diff_webhooks(existing: list[dict], desired: dict[str, str]) -> tuple[list[dict], list[dict]]:
    """Split `desired` {topic: delivery_url} into (to_create, already_ok).

    A desired (topic, delivery_url) pair counts as already registered only if
    an *active* existing webhook matches both fields exactly — an inactive
    webhook, or one pointed at a different URL, does not block a create.
    """
    active_pairs = {
        (w.get("topic"), w.get("delivery_url")) for w in existing if w.get("status") == "active"
    }
    to_create, already_ok = [], []
    for topic, delivery_url in desired.items():
        entry = {"topic": topic, "delivery_url": delivery_url}
        if (topic, delivery_url) in active_pairs:
            already_ok.append(entry)
        else:
            to_create.append(entry)
    return to_create, already_ok


def _require_env(*names: str) -> dict[str, str]:
    values: dict[str, str] = {}
    missing = []
    for name in names:
        value = os.environ.get(name)
        if value:
            values[name] = value
        else:
            missing.append(name)
    if missing:
        sys.exit(f"Missing required env var(s): {', '.join(missing)}")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Perform the live write (also requires STOPSHOW_ACK=1 env). Default is dry-run.",
    )
    args = parser.parse_args()

    env = _require_env("WP_BASE_URL", "WC_CONSUMER_KEY", "WC_CONSUMER_SECRET", "WP_WEBHOOK_SECRET")
    base = env["WP_BASE_URL"].rstrip("/")
    auth = (env["WC_CONSUMER_KEY"], env["WC_CONSUMER_SECRET"])

    response = requests.get(
        f"{base}/wp-json/wc/v3/webhooks", auth=auth, params={"per_page": 100}, timeout=20
    )
    response.raise_for_status()
    existing = response.json()

    desired = dict.fromkeys(TOPICS, DELIVERY_URL)
    to_create, already_ok = diff_webhooks(existing, desired)

    print(f"Existing webhooks (any status): {len(existing)}")
    print(f"Already registered ({len(already_ok)}): {[w['topic'] for w in already_ok]}")
    print(f"To create ({len(to_create)}): {[w['topic'] for w in to_create]}")

    if not to_create:
        print("Nothing to do — all desired webhooks are already active.")
        return 0

    if not args.execute or os.environ.get("STOPSHOW_ACK") != "1":
        print(
            "\nSTOPSHOW: pass --execute and set STOPSHOW_ACK=1 to register these live "
            "(production WooCommerce write)."
        )
        return 1

    payload = {
        "create": [
            {
                "name": f"DevSkyy dashboard — {entry['topic']}",
                "topic": entry["topic"],
                "delivery_url": entry["delivery_url"],
                "secret": env["WP_WEBHOOK_SECRET"],
            }
            for entry in to_create
        ]
    }
    batch_response = requests.post(
        f"{base}/wp-json/wc/v3/webhooks/batch", auth=auth, json=payload, timeout=20
    )
    batch_response.raise_for_status()
    result = batch_response.json()
    created = result.get("create", [])
    print(f"Created {len(created)} webhook(s): {[w.get('topic') for w in created]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
