---
name: Measurement Access Requests Packet (single-sitting Corey-action doc)
specified_by: [wp: §WP-0.5.a]
phase: 0 (generated); 0.5 (actioned by Corey)
test_command: node scripts/measurement/verify-all-grants.js  # exits 0 once all grants present
pass_threshold: All grants verified PASS, or each PENDING row has documented blocker
last_updated: 2026-05-03
last_updated_by: eval-harness (Phase 0)
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
13. **Save the downloaded JSON file** — we'll add it to Vercel env vars (Step 7 below). Do NOT email it; do NOT commit it to git.

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

**Verify:**

```bash
node scripts/measurement/verify-ga4.js
# Returns: GA4 property ID, last 30d sessions count
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

**Verify:**

```bash
node scripts/measurement/verify-gsc.js
# Returns: indexed page count, top 10 queries by clicks
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
7. Container permissions: **Edit**
8. Click "Add"

**Steps (if GTM container does NOT exist yet):**

1. Go to https://tagmanager.google.com
2. Click "Create Account"
3. Account name: **Skyyrose**
4. Country: United States (or your country)
5. Container name: **skyyrose.co**
6. Target platform: **Web**
7. Click "Create" → accept ToS
8. **Save the GTM-XXXXXXX container ID** — we'll need it in Step 7 (Vercel env)
9. Skip the install snippet for now (Phase 6.6 wires it into the WP theme)
10. Then follow the "container already exists" steps above to add the service account

**Then store container ID in Vercel:**

```
GTM_CONTAINER_ID=GTM-XXXXXXX
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
7. Scopes: **read** for all (project:read, event:read, etc.)
8. **Save the auth token** for Vercel env: `SENTRY_AUTH_TOKEN_READ=...`

**Verify:**

```bash
node scripts/measurement/verify-sentry.js
# Returns: project list, last 30d issue count per project
```

---

## Step 7 — Add all secrets to Vercel env (single sitting)

**Why:** Per WP §4.10 architecture, all measurement secrets live in Vercel env vars only — never in WP DB, never in the WP theme repo.

**Steps:**

1. Open a terminal where the `vercel` CLI is authenticated (`vercel whoami` returns your user)
2. Navigate to the project root: `cd /Users/theceo/DevSkyy`
3. Add each env var (production scope):

```bash
# Google service account (paste the full JSON from Step 1's downloaded file)
vercel env add GOOGLE_SERVICE_ACCOUNT_JSON production
# Then paste the JSON content when prompted

# GTM container ID (from Step 4)
vercel env add GTM_CONTAINER_ID production
# Then paste GTM-XXXXXXX

# Meta system user token (from Step 5)
vercel env add META_SYSTEM_USER_TOKEN production

# Sentry DSNs (from Step 6)
vercel env add SENTRY_DSN_SKYYROSE_CO production
vercel env add SENTRY_DSN_DEVSKYY_APP production
vercel env add SENTRY_AUTH_TOKEN_READ production
```

4. After all are added, redeploy the latest production deployment so env vars take effect:

```bash
vercel deploy --prod
```

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
