#!/usr/bin/env python3
"""
HG-7 closer — SkyyRose dashboard<->WordPress credential setup + live validation.

What it does (idempotent, safe to re-run):
  1. Loads or interactively collects credentials into .env (chmod 600, never echoed).
  2. Generates WP_WEBHOOK_SECRET / REVALIDATE_SECRET if absent.
  3. LIVE-validates every credential against production endpoints (real calls, no mocks).
  4. Syncs validated vars to Vercel project env (via `vercel env`), or prints exact
     commands if the CLI isn't linked.
  5. Exit 0 == HG-7 closed. Non-zero == prints exactly what to fix.

What it will NEVER do: print/log secret values, transmit them anywhere except
skyyrose.co (validation) and Vercel CLI (env sync), or create credentials for you —
WordPress requires a logged-in human for that (~3 min, URLs printed below).

Usage:
  python3 scripts/remediation/setup_credentials.py            # interactive
  python3 scripts/remediation/setup_credentials.py --validate # non-interactive, CI-safe
  python3 scripts/remediation/setup_credentials.py --no-vercel
"""

import argparse
import getpass
import os
import re
import secrets as pysecrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("pip install requests --break-system-packages")

WP = "https://skyyrose.co"
ENV_KEYS = [
    "WP_BASE_URL",
    "WP_APP_USER",
    "WP_APP_PASSWORD",
    "WC_CONSUMER_KEY",
    "WC_CONSUMER_SECRET",
    "WP_WEBHOOK_SECRET",
    "REVALIDATE_SECRET",
]
GENERATED = {"WP_WEBHOOK_SECRET", "REVALIDATE_SECRET"}
CREATE_URLS = {
    "WooCommerce REST key (Read/Write)": f"{WP}/wp-admin/admin.php?page=wc-settings&tab=advanced&section=keys&create-key=1",
    "Application Password (on service user profile)": f"{WP}/wp-admin/profile.php#application-passwords-section",
}
OK, FAIL, WARN = "\033[32m PASS \033[0m", "\033[31m FAIL \033[0m", "\033[33m WARN \033[0m"


def redact(v):
    return f"{v[:4]}…({len(v)} chars)" if v else "<empty>"


def load_env(path: Path) -> dict:
    env = {}
    if path.exists():
        for line in path.read_text().splitlines():
            m = re.match(r"^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    for k in ENV_KEYS:  # process env overrides file
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def write_env(path: Path, env: dict):
    lines, seen = [], set()
    if path.exists():
        for line in path.read_text().splitlines():
            m = re.match(r"^\s*([A-Z0-9_]+)\s*=", line)
            if m and m.group(1) in env:
                lines.append(f"{m.group(1)}={env[m.group(1)]}")
                seen.add(m.group(1))
            else:
                lines.append(line)
    for k in ENV_KEYS:
        if k in env and k not in seen:
            lines.append(f"{k}={env[k]}")
    path.write_text("\n".join(lines) + "\n")
    path.chmod(0o600)


def req(method, url, auth=None, tries=3, **kw):
    for i in range(tries):
        r = requests.request(
            method, url, auth=auth, timeout=20, headers={"User-Agent": "DevSkyy-HG7-Setup"}, **kw
        )
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 2 ** (i + 1)))
            print(f"    rate-limited, backing off {wait}s")
            time.sleep(wait)
            continue
        return r
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env-file", default=".env")
    ap.add_argument("--validate", action="store_true", help="no prompts; validate what exists")
    ap.add_argument("--no-vercel", action="store_true")
    a = ap.parse_args()
    envp = Path(a.env_file)
    env = load_env(envp)
    env.setdefault("WP_BASE_URL", WP)

    # ---- 1. Collect ---------------------------------------------------------
    missing = [k for k in ENV_KEYS if not env.get(k)]
    need_input = [k for k in missing if k not in GENERATED]
    if need_input and a.validate:
        # Report what's missing but still live-validate whatever IS present —
        # partial wiring progress is visible instead of an all-or-nothing gate.
        print(f"{FAIL} missing (non-interactive): {', '.join(need_input)}")
    if need_input and not a.validate:
        print("== HG-7: create these in wp-admin (one browser tab each), then paste ==")
        for label, url in CREATE_URLS.items():
            print(f"  • {label}\n    {url}")
        print("  Service user: dedicated 'devskyy-service' (Shop Manager or Admin).")
        print("  Input is hidden; values go only to .env (chmod 600).\n")
        prompts = {
            "WP_APP_USER": ("Service username", input),
            "WP_APP_PASSWORD": ("Application Password (xxxx xxxx …)", getpass.getpass),
            "WC_CONSUMER_KEY": ("WooCommerce consumer key ck_…", getpass.getpass),
            "WC_CONSUMER_SECRET": ("WooCommerce consumer secret cs_…", getpass.getpass),
        }
        for k in need_input:
            label, fn = prompts.get(k, (k, getpass.getpass))
            env[k] = fn(f"  {label}: ").strip()
    for k in GENERATED:
        if not env.get(k):
            env[k] = pysecrets.token_hex(32)
            print(f"  generated {k} ({redact(env[k])})")
    write_env(envp, env)
    print(f"  .env written → {envp.resolve()} (0600)\n")

    # ---- 2. Live validation (real endpoints, no mocks) ----------------------
    base = env["WP_BASE_URL"].rstrip("/")
    results = []

    def check(name, fn):
        try:
            ok, note = fn()
        except Exception as e:
            ok, note = False, f"{type(e).__name__}: {e}"
        results.append(ok)
        print(f"{OK if ok else FAIL} {name} — {note}")

    check(
        "WP reachable (public skyyrose/v1/collections)",
        lambda: (
            (r := req("GET", f"{base}/wp-json/skyyrose/v1/collections")).status_code == 200
            and "collections" in r.text,
            f"HTTP {r.status_code}",
        ),
    )

    def wc():
        r = req(
            "GET",
            f"{base}/wp-json/wc/v3/products",
            auth=(env["WC_CONSUMER_KEY"], env["WC_CONSUMER_SECRET"]),
            params={"per_page": 1},
        )
        if r.status_code == 200:
            return True, f"HTTP 200, X-WP-Total={r.headers.get('X-WP-Total', '?')}"
        if r.status_code == 401:
            return False, "HTTP 401 — key/secret rejected (recreate, check Read/Write)"
        return False, f"HTTP {r.status_code}: {r.text[:120]}"

    check("WooCommerce wc/v3 auth (consumer key/secret)", wc)

    def app_pw():
        auth = (env["WP_APP_USER"], env["WP_APP_PASSWORD"])
        r = req("GET", f"{base}/wp-json/wp/v2/users/me", auth=auth, params={"context": "edit"})
        if r.status_code == 200:
            u = r.json()
            return True, f"authed as '{u.get('slug')}' roles={u.get('roles')}"
        if r.status_code in (401, 403):
            return False, f"HTTP {r.status_code} — app password rejected"
        return False, f"HTTP {r.status_code}: {r.text[:120]}"

    if env.get("WP_APP_USER") and env.get("WP_APP_PASSWORD"):
        check("WP Application Password (wp/v2/users/me)", app_pw)
    else:
        results.append(False)
        print(f"{FAIL} WP Application Password — not configured yet (skipped live check)")

    def custom_write_surface():
        auth = (env["WP_APP_USER"], env["WP_APP_PASSWORD"])
        r = req("GET", f"{base}/wp-json/skyyrose/v1/settings", auth=auth)
        if r.status_code == 200:
            return True, "skyyrose/v1/settings readable with app password"
        if r.status_code in (401, 403):
            return (
                False,
                f"HTTP {r.status_code} — service user lacks capability for skyyrose/v1/settings (check permission_callback / role)",
            )
        return False, f"HTTP {r.status_code}: {r.text[:120]}"

    if env.get("WP_APP_USER") and env.get("WP_APP_PASSWORD"):
        check("Custom namespace auth (skyyrose/v1/settings)", custom_write_surface)
    else:
        results.append(False)
        print(f"{FAIL} Custom namespace auth — needs the app password first (skipped)")

    def settings_anon_guard():
        r = req("GET", f"{base}/wp-json/skyyrose/v1/settings")
        if r.status_code in (401, 403):
            return True, f"anonymous correctly rejected (HTTP {r.status_code})"
        if r.status_code == 200:
            return (
                False,
                "SETTINGS READABLE ANONYMOUSLY — permission_callback hole, fix in theme before launch",
            )
        return True, f"HTTP {r.status_code} (non-200 anon)"

    check("Security: settings rejects anonymous", settings_anon_guard)

    # ---- 3. Vercel sync ------------------------------------------------------
    if not a.no_vercel:
        vercel = shutil.which("vercel")
        if vercel and Path(".vercel/project.json").exists():
            print("\n== Vercel env sync (production+preview) ==")
            for k in ENV_KEYS:
                for tgt in ("production", "preview"):
                    subprocess.run([vercel, "env", "rm", k, tgt, "--yes"], capture_output=True)
                    p = subprocess.run(
                        [vercel, "env", "add", k, tgt], input=env[k], text=True, capture_output=True
                    )
                    print(f"  {k} → {tgt}: {'ok' if p.returncode == 0 else p.stderr.strip()[:80]}")
        else:
            print(f"\n{WARN} Vercel CLI not linked here. From the dashboard repo run:")
            for k in ENV_KEYS:
                print(f"  vercel env add {k} production   # paste value from .env")

    print()
    if all(results):
        print(
            f"{OK} HG-7 CLOSED — wiring credentials live-validated. Claude Code may proceed with WS7."
        )
        sys.exit(0)
    print(f"{FAIL} HG-7 open — fix the FAIL lines above and re-run.")
    sys.exit(1)


if __name__ == "__main__":
    main()
