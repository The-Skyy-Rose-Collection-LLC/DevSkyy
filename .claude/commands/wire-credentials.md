---
description: Close HG-7 — set up and live-validate the dashboard↔WordPress credentials, then sync to Vercel
allowed-tools: Bash(python3 scripts/remediation/setup_credentials.py*), Bash(vercel env*), Read
---

# /wire-credentials — HG-7 closer

Run `python3 scripts/remediation/setup_credentials.py` and orchestrate to green. Rules:

1. **Never print, log, or echo secret values** — not in output, not in summaries, not in
   commit messages. The script redacts; you redact too. If the user pastes a secret into
   chat by mistake, tell them to rotate it in wp-admin immediately.
2. **Credential creation is the user's step, not yours.** If the script reports missing
   credentials, STOP and hand off with exactly this (then wait):
   - WooCommerce key (Read/Write): https://skyyrose.co/wp-admin/admin.php?page=wc-settings&tab=advanced&section=keys&create-key=1
   - Application Password: https://skyyrose.co/wp-admin/profile.php#application-passwords-section
     (use/create a dedicated `devskyy-service` user; name the password `devskyy-dashboard`)
   - They paste values into the script's hidden prompts (interactive mode), or into
     `.env` directly — never into this chat.
3. **Interpret failures precisely:**
   - `wc/v3 ... 401` → key/secret wrong or Read-only; recreate with Read/Write.
   - `users/me ... 401` → app password wrong, or the host blocks Basic auth — WP.com
     Atomic supports Application Passwords; check the user isn't a WP.com-connected-only
     account (must be a site user).
   - `skyyrose/v1/settings ... 401/403 with valid app password` → capability gap: read the
     theme's `register_rest_route` permission_callback for that route, grant the service
     user the required capability (prefer a targeted `map_meta_cap`/role grant over
     promoting to admin), redeploy, re-run.
4. **Run order:** `--validate` first (non-destructive). Only go interactive if it exits 2.
   After exit 0, confirm Vercel sync ran (or print the manual `vercel env add` commands
   from a linked dashboard-repo directory), then trigger a redeploy so route handlers
   pick up env: `vercel redeploy --prod` is NOT needed tonight — preview deploy suffices
   for wiring_audit; production redeploy happens at launch cutover.
5. Exit 0 = announce "HG-7 closed" and proceed with WS7 (C3 client layer) per
   SKYYROSE_LAUNCH_NIGHT_SPEC_V2.md. Do not proceed to WS7 write-path work before this.
