# Eval — Integrations

> Pass/fail rubric for every external integration. Phase 5 sub-phases are graded against this.

## Stripe payment processing (Phase 5.10)

| ID | Criterion | Method |
|----|-----------|--------|
| STR1 | Stripe Elements load on checkout block | DOM check for `.StripeElement` |
| STR2 | Test card `4242 4242 4242 4242` → successful charge → WC order in `processing` state | Playwright e2e |
| STR3 | Test card `4000 0027 6000 3184` → 3DS challenge appears → `Submit` → success | Playwright e2e |
| STR4 | Test card `4000 0000 0000 0002` → declined → user-friendly error → user can retry | Playwright e2e |
| STR5 | Refund from WC admin → Stripe dashboard shows refund within 60s | Manual + Stripe MCP `mcp__stripe__*` |
| STR6 | Apple Pay button visible on Safari with Apple Pay enabled | Manual on real device |
| STR7 | Google Pay button visible on Chrome with Google Pay enabled | Manual |
| STR8 | Webhook endpoint at `wp-json/wc/v3/stripe/webhook` accepts Stripe signature | curl with valid signature |
| STR9 | No Stripe secret key in any client-rendered HTML/JS | grep response body |
| STR10 | CSP headers permit `js.stripe.com` + `api.stripe.com` only — no wildcard | curl `-D -` |

## FASHN AR try-on (Phase 5.6)

| ID | Criterion | Method |
|----|-----------|--------|
| FSH1 | "Try on" button visible on every product page with `try_on_enabled: true` meta | DOM check |
| FSH2 | Modal opens on click; user image upload accepts JPG/PNG up to 10MB | E2E |
| FSH3 | Vercel `/api/fashn-tryon` accepts product_id + image_url, returns 4-model response | curl with auth header |
| FSH4 | Roundtrip < 8s p95 (image upload + FASHN inference + return) | Vercel function timing |
| FSH5 | Per-user daily cap enforced (default: 5 try-ons/day) | Hit endpoint 6 times → 6th returns 429 |
| FSH6 | Per-user lifetime cap enforced for non-customers (default: 2) | Same |
| FSH7 | Cost per try-on logged to Vercel KV → admin dashboard shows daily/weekly spend | Manual |
| FSH8 | Failure case: API timeout → falls back to size guide modal with apologetic copy | Mock failure |
| FSH9 | Cost ceiling: stops accepting new try-ons when daily cap of $25 reached (raise once usage proven sustainable) | Stress test |
| FSH10 | No FASHN API key in any client-rendered code | grep response |

## Pinecone semantic search (Phase 5.7)

| ID | Criterion | Method |
|----|-----------|--------|
| PIN1 | Vercel `/api/semantic-search` accepts query string, returns ranked product list | curl |
| PIN2 | Query latency < 300ms p95 | Vercel function timing |
| PIN3 | Vercel `/api/embed-products` cron runs nightly, indexes all published WC products | Vercel cron logs |
| PIN4 | Webhook on WC product save → incremental reindex within 30s | WP webhook + Vercel logs |
| PIN5 | Theme `search.php` hits Pinecone first; falls back to WP search if 5xx or timeout | E2E with Pinecone offline |
| PIN6 | Relevance: 50 hand-graded queries return relevant top-3 result ≥ 80% of time | Manual relevance test |
| PIN7 | Index size < 100MB (cost control) | Pinecone dashboard |
| PIN8 | Empty index handled (returns WP fallback, no 5xx) | Test on empty namespace |
| PIN9 | No Pinecone API key in any client-rendered code | grep response |

## WebXR / spatial layer (Phase 5.8)

| ID | Criterion | Method |
|----|-----------|--------|
| XR1 | `navigator.xr.isSessionSupported('immersive-vr')` detects Vision Pro Safari | Manual on Vision Pro |
| XR2 | Session-start button visible only on supported devices | DOM check + UA detection |
| XR3 | Quest 3 browser starts immersive-vr session, scene renders | Manual on Quest 3 |
| XR4 | Vision Pro Safari starts immersive-vr session, scene renders | Manual on Vision Pro |
| XR5 | iOS / Android: AR button shown via WebXR Hit Test or AR Quick Look fallback | Manual |
| XR6 | Hand tracking: pinch-and-pull interactions on Quest 3 work | Manual |
| XR7 | Falls back to standard 3D viewer on unsupported browser/device | Manual on desktop Chrome |
| XR8 | Session exit returns to standard 3D state without re-loading the page | E2E |
| XR9 | Memory: < 500MB after 10-min XR session (no leaks) | Quest 3 perf overlay |
| XR10 | Avatar (`skyy.glb`) renders correctly post Blender rig pass (if used) | Manual visual |

## Drop queue WebSocket (Phase 5.4)

| ID | Criterion | Method |
|----|-----------|--------|
| DQ1 | WebSocket endpoint at Vercel `/api/drop-queue` accepts client connections | wscat |
| DQ2 | Server emits `position-update` every 5s to all connected clients | Manual + Playwright |
| DQ3 | Stress test: 1000 concurrent connections, all receive updates within 1s | k6 / artillery |
| DQ4 | Unlock event broadcast to all clients within 500ms of server-side trigger | Stress test |
| DQ5 | Reconnection: client auto-reconnects within 3s on network blip | Network throttling |
| DQ6 | Falls back gracefully to polling if WebSocket fails | Mock WS unavailable |
| DQ7 | No PII (email, name) sent over public WS channel — only opaque queue position | Wireshark / browser inspect |

## Klaviyo email integration (already wired — verify Phase 5.4 + 6)

| ID | Criterion | Method |
|----|-----------|--------|
| KLV1 | Profile create on cart abandonment | Klaviyo MCP `klaviyo_get_profiles` |
| KLV2 | "Pre-Order Drop Launch" 7-email flow active | Klaviyo MCP `klaviyo_get_flows` |
| KLV3 | Welcome flow (5 emails) active | Klaviyo MCP |
| KLV4 | Post-Purchase flow (4 emails) active | Klaviyo MCP |
| KLV5 | Per-collection waitlist segment functional | Klaviyo MCP `klaviyo_get_segments` |
| KLV6 | Event fire on add-to-cart, view-product, purchase | Klaviyo MCP `klaviyo_get_events` |
| KLV7 | API key in WP options, not hardcoded | grep theme files |

## Claude Lab admin tool (Phase 5.9)

| ID | Criterion | Method |
|----|-----------|--------|
| CL1 | Sandbox tab: prompt + run + streaming output works | Playwright e2e |
| CL2 | Cache hit indicator flips to HIT on identical prompt re-run | Manual |
| CL3 | Cost telemetry accurate within 5% of Anthropic dashboard | Manual reconciliation |
| CL4 | Eval tab: run a 3-item suite returns rubric scores | E2E |
| CL5 | History sidebar persists last 10 runs across browser refresh | E2E |
| CL6 | Auth: only admin users can access route | Negative test (logged-out) |
| CL7 | No Anthropic API key in client-rendered code | grep |

## Conversion tracking (Phase 6.6)

| ID | Criterion | Method |
|----|-----------|--------|
| CV1 | GA4 page_view fires on every page | GA4 DebugView |
| CV2 | GA4 view_item, add_to_cart, begin_checkout, purchase events fire correctly | DebugView |
| CV3 | Meta CAPI events match browser pixel events (deduplication) | Meta Events Manager |
| CV4 | LinkedIn Insight Tag fires page_view + conversion event | LinkedIn Campaign Manager |
| CV5 | GTM container loaded asynchronously, no CLS impact | Lighthouse |
| CV6 | Consent banner gates all tracking before user opts in (GDPR) | Cookies tab pre-consent |

## SEO (Phase 6.7)

| ID | Criterion | Method |
|----|-----------|--------|
| SEO1 | JSON-LD Product schema valid on every product page | Google Rich Results Test |
| SEO2 | JSON-LD Organization schema valid on home page | Same |
| SEO3 | JSON-LD BreadcrumbList valid on every interior page | Same |
| SEO4 | Sitemap.xml at `/sitemap.xml` lists all published pages + products | curl |
| SEO5 | Canonical URL set on every page, never points to a 404 | crawler |
| SEO6 | robots.txt allows crawl of public pages, blocks `/cart`, `/checkout`, `/my-account` | curl |
| SEO7 | OG / Twitter Card meta on every shareable page | View source |

---

## Integration eval execution protocol

Each integration phase exits when ALL criteria above PASS or are explicitly waived by user. Results stored in `eval/results/integrations-<phase>-<timestamp>.json`.
