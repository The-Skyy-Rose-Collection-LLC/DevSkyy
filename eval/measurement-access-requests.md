---
name: Measurement Access Requests Packet (single-sitting Corey-action doc)
specified_by: [wp: §WP-0.5.a]
phase: 0 (generated); 0.5 (actioned by Corey)
test_command: node scripts/measurement/verify-all-grants.js  # PHASE 0.5 DELIVERABLE — script does not exist yet; running it will exit 1 with a "Phase 0.5 not started" message until the verify-* scripts are built. See scripts/measurement/README.md.
pass_threshold: All grants verified PASS, or each PENDING row has documented blocker
last_updated: 2026-05-03
last_updated_by: eval-harness (Phase 0; refined 2026-05-03 — JSON-via-redirect, GA4/GSC/GTM/Sentry IDs added to Step 7, GTM scope tightened to Read, env-var manifest table added)
---

# Measurement Access Requests — Single Sitting

This is the **one document Corey needs to action** to unblock Phase 0.5 measurement provisioning. Each section is a separate platform with click-by-click steps. Goal: complete this packet in one sitting, then ping me and Phase 0.5 verifies + pulls baselines.

**Why this exists:** §4.10 of the WP plan requires GA4, GSC, GTM, Meta Business System User access — these are UIs Claude Code cannot reach. Everything else (WC API keys, Klaviyo, Stripe, Hotjar) Claude Code can autonomously provision once Corey confirms account presence.

---

## Service account email to add (used in steps below)

> **You'll generate this in Step 1 below. It will look like `skyyrose-readonly@<project-id>.iam.gserviceaccount.com`.**

The same service account is added to GA4, GSC, GTM, and (separately) granted as a Google Cloud Project member. One identity, multiple grants.

---

## Step 1 — Google Cloud service account (5 minutes)

**Why:** GA4 + GSC + GTM API access via service account is more reproducible than human OAuth tokens. Once granted, Claude Code can pull baselines and run weekly cron reports without re-authenticating.

**Steps:**

1. Go to https://console.cloud.google.com/projectcreate
2. Project name: **skyyrose-measurement** (or use existing if you have one)
3. Click "Create"
4. Once created, go to https://console.cloud.google.com/iam-admin/serviceaccounts
5. Click "+ Create Service Account"
6. Service account name: **skyyrose-readonly**
7. Description: "Read-only access for Skyyrose measurement pipelines"
8. Click "Create and Continue"
9. Role: skip (we'll grant per-resource access)
10. Click "Done"
11. Find the new account in the list, click on it
12. Tab "Keys" → "Add Key" → "Create new key" → JSON → Create
13. **Save the downloaded JSON file to a known path** — recommended: `~/Downloads/skyyrose-readonly-key.json`. Step 7 reads it via shell redirection (`< file.json`), so the path matters and the JSON content stays on a single Vercel env value untouched. Do NOT email it; do NOT commit it to git. Plan to delete the local copy once Phase 0.5 verifies — Vercel keeps the canonical copy.

**Verify:**

```bash
# After Step 7 (Vercel env), this verifies:
node scripts/measurement/verify-google-service-account.js
```

---

## Step 2 — Google Analytics 4 (3 minutes)

**Why:** Every KPI in WP §9 (bounce rate, ATC rate, conversion rate, AOV, etc.) comes from GA4. Without this, Phase 0.5 can't capture baselines, and every "before/after" claim in Phase 7 is unfalsifiable.

**Steps:**

1. Go to https://analytics.google.com — log in as the GA4 admin for `skyyrose.co`
2. Select the GA4 property for skyyrose.co
3. Bottom-left gear (Admin) → Property settings → Property Access Management
4. Click "+" (top-right) → "Add users"
5. Email address: paste the service account email from Step 1 (e.g., `skyyrose-readonly@skyyrose-measurement.iam.gserviceaccount.com`)
6. Permissions: **Viewer** (we want read-only)
7. Uncheck "Notify new users by email" (it's a service account, no inbox)
8. Click "Add"

**Then enable the API:**

9. Go to https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com
10. Make sure project `skyyrose-measurement` is selected (top bar)
11. Click "Enable"

**Capture the Property ID** (verifier needs this — service account access alone isn't enough; we have to tell the script which property to query):

12. Still in GA4 Admin → Property settings (top of the right column)
13. Copy the **Property ID** (a 9-10 digit number, e.g., `345678901`)
14. **Save it for Step 7** — we'll set `GA4_PROPERTY_ID=properties/345678901` in Vercel env

**Verify:**

```bash
node scripts/measurement/verify-google-service-account.js  # confirms JWT auth works
node scripts/measurement/verify-ga4.js                     # confirms property read access + returns 30d sessions
```

---

## Step 3 — Google Search Console (2 minutes)

**Why:** Indexed page count, top queries, click-through rate from organic search — needed for SEO baselines (WP §4.4) and Phase 6 SEO sub-phase.

**Steps:**

1. Go to https://search.google.com/search-console
2. Select the `skyyrose.co` property
3. Settings (left sidebar gear) → Users and permissions
4. Click "Add user"
5. Email: same service account email from Step 1
6. Permission: **Restricted** (we want read-only)
7. Click "Add"

**Then enable the API:**

8. Go to https://console.cloud.google.com/apis/library/searchconsole.googleapis.com
9. Project `skyyrose-measurement` selected
10. Click "Enable"

**Capture the Site URL** (verifier needs to know which Search Console property to query — properties are addressed by their canonical site URL, *with* trailing slash for URL-prefix properties or `sc-domain:` prefix for domain properties):

11. **Save for Step 7**: `GSC_SITE_URL=https://skyyrose.co/` (URL-prefix) **or** `GSC_SITE_URL=sc-domain:skyyrose.co` (domain property — pick whichever matches what's listed in your Search Console)

**Verify:**

```bash
node scripts/measurement/verify-gsc.js
# Returns: top 10 search queries by clicks for the last 28 days (proves read access).
# Indexed-page-count uses a different API (URL Inspection / Sitemaps) and is captured
# later by pull-baselines.js — Phase 0.5.e — not this verifier.
```

---

## Step 4 — Google Tag Manager (3 minutes)

**Why:** GTM is the chassis for GA4 events, Meta Pixel + CAPI, conversion tracking. Without GTM access, Phase 6.6 conversion tracking sub-phase can't deploy.

**Note:** If you don't already have GTM installed on skyyrose.co, this is the moment to create the container. The WP plan §4.6 + §4.10 says GTM is the install method for GA4.

**Steps (if GTM container already exists):**

1. Go to https://tagmanager.google.com
2. Select the container for skyyrose.co
3. Admin (top-right gear) → User Management
4. Click "+ Add User"
5. Email: same service account email from Step 1
6. Account permissions: **User**
7. Container permissions: **Read** for now (so the verifier can confirm access without standing authorization to mutate tags). When Phase 6.6 deploys GA4 + Pixel + CAPI tags via this account, we'll bump to **Publish**. Smaller blast radius until then.
8. Click "Add"

**Steps (if GTM container does NOT exist yet):**

1. Go to https://tagmanager.google.com
2. Click "Create Account"
3. Account name: **Skyyrose**
4. Country: United States (or your country)
5. Container name: **skyyrose.co**
6. Target platform: **Web**
7. Click "Create" → accept ToS
8. **Save the `GTM-XXXXXXX` container ID** AND the **Account ID** (the all-numeric ID in the URL after creation) — we need both in Step 7. Tag Manager API addresses containers as `accounts/{ACCOUNT_ID}/containers/{CONTAINER_ID}`, so the public `GTM-` slug alone is not enough.
9. Skip the install snippet for now (Phase 6.6 wires it into the WP theme)
10. Then follow the "container already exists" steps above to add the service account

**Then store container ID + account ID in Vercel** (Step 7):

```
GTM_CONTAINER_ID=GTM-XXXXXXX     # the public-facing container slug
GTM_ACCOUNT_ID=12345678          # the numeric account ID (from the URL or Admin → Account settings)
```

**Verify:**

```bash
node scripts/measurement/verify-gtm.js
# Returns: container ID, last published version
```

---

## Step 5 — Meta Business Manager + Pixel + CAPI (5 minutes)

**Why:** Meta Pixel is already installed on skyyrose.co via `inc/facebook-sdk.php`. To add server-side dedup (Conversions API), we need a System User token — not a personal access token, which expires.

**Steps:**

1. Go to https://business.facebook.com → Business Settings (gear top-right)
2. Left sidebar: Users → System Users
3. Click "Add"
4. Name: **skyyrose-measurement-api**
5. Role: **Employee**
6. Click "Create System User"

**Assign to ad account, pixel, page:**

7. With the new system user selected, click "Add Assets"
8. Select: Ad Accounts (assign your skyyrose ad account), Pixels (assign skyyrose pixel), Pages (assign skyyrose page)
9. For each: assign with **View** + **Manage** permissions

**Generate access token:**

10. With system user selected, click "Generate New Token"
11. App: select your Meta app (or create one — `developers.facebook.com/apps` → Create App → "Other" → Business)
12. Permissions:
    - `ads_read`
    - `ads_management` (for CAPI)
    - `business_management`
    - `pages_read_engagement`
13. Click "Generate Token"
14. **Save the long-lived token** — paste into Vercel env (Step 7) as `META_SYSTEM_USER_TOKEN`

**Verify:**

```bash
node scripts/measurement/verify-meta.js
# Returns: pixel events 30d, ad spend if applicable
```

---

## Step 6 — Sentry (2 minutes)

**Why:** Phase 6.5 perf phase + Phase 7 post-deploy verification need error tracking on `skyyrose.co` (frontend errors) and `devskyy.app` (Vercel routes).

**Steps:**

1. Go to https://sentry.io
2. If you don't have a Sentry org yet: create one ("Skyyrose")
3. Create two projects:
   - Project name: **skyyrose-co** — Platform: JavaScript / Browser
   - Project name: **devskyy-app** — Platform: Next.js
4. After each project is created, copy the DSN (looks like `https://abc123@o123456.ingest.sentry.io/789`)
5. **Save both DSNs** for Vercel env (Step 7):
   - `SENTRY_DSN_SKYYROSE_CO=...`
   - `SENTRY_DSN_DEVSKYY_APP=...`

**For MCP read access:**

6. In Sentry: Settings (top-right) → Auth Tokens → Create New Token
7. Scopes — check exactly these (don't grant more than the verifier needs):
   - `org:read` — list orgs the token belongs to
   - `project:read` — list projects per org (verifier asserts both `skyyrose-co` and `devskyy-app` exist)
   - `event:read` — count last-30d issues for baseline
8. **Save the auth token** for Vercel env: `SENTRY_AUTH_TOKEN_READ=...`
9. **Save your Sentry org slug** (visible in any Sentry URL: `https://sentry.io/organizations/<slug>/...`). Set in Step 7 as `SENTRY_ORG_SLUG=<your-slug>`.

**Verify:**

```bash
node scripts/measurement/verify-sentry.js
# Returns: project list, last 30d issue count per project
```

---

## Step 7 — Add all secrets to Vercel env (single sitting)

**Why:** Per WP §4.10 architecture, all measurement secrets live in Vercel env vars only — never in WP DB, never in the WP theme repo.

**Steps:**

1. Open a terminal where the `vercel` CLI is authenticated (`vercel whoami` returns your user).
2. Navigate to the project root: `cd /Users/theceo/DevSkyy`.
3. Add the **secret** values (these never leave Vercel after this step):

```bash
# Google service account JSON — read directly from the downloaded file from Step 1.
# Using `< file.json` avoids the multi-line-paste foot-gun where newlines in the JSON
# get re-interpreted by the terminal and break the private_key on the other side.
vercel env add GOOGLE_SERVICE_ACCOUNT_JSON production < ~/Downloads/skyyrose-readonly-key.json

# Meta system user token (from Step 5) — paste when prompted (single line, no quotes)
vercel env add META_SYSTEM_USER_TOKEN production

# Sentry auth token (from Step 6, scopes: org:read project:read event:read)
vercel env add SENTRY_AUTH_TOKEN_READ production

# Sentry DSNs (these are non-secret, but per WP §4.10 still live as Vercel env)
vercel env add SENTRY_DSN_SKYYROSE_CO production
vercel env add SENTRY_DSN_DEVSKYY_APP production
```

4. Add the **identifier** values (these tell the verifiers *which* property/container/org to query):

```bash
# GA4 (Step 2)
vercel env add GA4_PROPERTY_ID production         # e.g. properties/345678901

# Search Console (Step 3)
vercel env add GSC_SITE_URL production            # e.g. https://skyyrose.co/  OR  sc-domain:skyyrose.co

# Tag Manager (Step 4)
vercel env add GTM_CONTAINER_ID production        # GTM-XXXXXXX
vercel env add GTM_ACCOUNT_ID production          # numeric account ID

# Sentry (Step 6)
vercel env add SENTRY_ORG_SLUG production         # your sentry.io org slug
```

5. **Sanity-check** the manifest (every key from the table below should be listed):

```bash
vercel env ls production
```

6. Redeploy production so env vars take effect on serverless functions and crons:

```bash
vercel deploy --prod
```

7. (Optional but recommended) Pull a local `.env.local` so you can run individual `verify-*.js` scripts from your laptop too:

```bash
vercel env pull .env.local
```

The local file is gitignored. Delete it after verification.

### Env var manifest you should now have

After Step 7 finishes, `vercel env ls production` should show all of these. The verifier dispatcher cross-references this list and reports which (if any) are missing before it tries any API calls.

| Key | Source step | Used by |
|-----|-------------|---------|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Step 1 | `verify-google-service-account.js`, `verify-ga4.js`, `verify-gsc.js`, `verify-gtm.js` |
| `GA4_PROPERTY_ID` | Step 2 | `verify-ga4.js` |
| `GSC_SITE_URL` | Step 3 | `verify-gsc.js` |
| `GTM_CONTAINER_ID` | Step 4 | `verify-gtm.js` |
| `GTM_ACCOUNT_ID` | Step 4 | `verify-gtm.js` |
| `META_SYSTEM_USER_TOKEN` | Step 5 | `verify-meta.js` |
| `SENTRY_AUTH_TOKEN_READ` | Step 6 | `verify-sentry.js` |
| `SENTRY_ORG_SLUG` | Step 6 | `verify-sentry.js` |
| `SENTRY_DSN_SKYYROSE_CO` | Step 6 | runtime error reporting (not the verifier) |
| `SENTRY_DSN_DEVSKYY_APP` | Step 6 | runtime error reporting (not the verifier) |

---

## What Claude Code does next (autonomous after you finish Step 7)

Once you tell me Step 7 is done, Claude Code runs Phase 0.5:

1. **Verification sweep** — runs every `verify-*.js` script. Each must return PASS or Phase 0.5 doesn't advance.
2. **Autonomous provisioning** of WC REST API keys (via wp-admin REST), Hotjar/Microsoft Clarity (free tier install), and any other claude-code-owned items from §4.10.
3. **Baseline capture** — `pull-baselines.js` runs and writes `eval/baselines.md`, `eval/qualitative-baselines.md`, `eval/funnel-baseline.md`. Every §9 KPI now has a real number.
4. **Ongoing monitoring setup** — `vercel.json` `crons` block added; `weekly-report.js` posts Monday summaries; dashboard at `devskyy.app/admin/measurement` deployed.
5. **§3 critique completion** — fills the KPI columns in `eval/critique/current-site-audit.md` (v1 from §3 audit subagent already running) with real numbers.

After Phase 0.5 exits clean, Phase 1 (admin cleanup) begins. No code touches customer surfaces until Phase 0.5 baselines exist.

---

## What if a step fails or you get stuck?

Tell me which step. Common gotchas:

- **GCP project creation fails because of billing.** GA4 Data API + Search Console API + GTM API are all free tier — no billing required. If GCP asks, you can decline billing setup.
- **GA4 service account add fails because you're not the GA4 admin.** Verify you're the property admin (Settings → Property Access Management — you should see a list of users including yourself). If not, ask whoever set up GA4 to add you as admin first.
- **Meta system user creation fails.** Common cause: the Meta Business Manager doesn't yet exist for your domain. Create one at https://business.facebook.com first, claim skyyrose.co, then add the system user.
- **Sentry asks for a payment method.** Sentry's developer plan is free; if it asks for payment, decline — the free tier covers everything we need for Phase 0.5–7.

---

## What if you can't action this in one sitting?

Mark it as partial — tell me which steps are done, which aren't. I can verify the partial grants and proceed with available data. If a step is genuinely blocked (e.g., no Meta Business Manager exists), I document the gap in `eval/baselines.md` with the proxy used instead and the confidence cost — Phase 0.5 advances rather than stalling the whole build.

---

**Estimated time:** 20-25 minutes total if you have all admin access ready.

**When done:** Reply "access packet complete" and I'll start Phase 0.5 verification.
