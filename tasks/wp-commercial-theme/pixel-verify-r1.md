# Pixel verify r1 — v1.12.0 live (2026-07-19)

9 production loads (fresh contexts), mobile 390x844 + desktop 1440x900. Full probe JSON: job tmp `verify-results.json`. Screenshots: `shots-r1/` (3, all vision-read). Lighthouse ran concurrently — structure/visuals only.

| Probe | Result | Evidence |
|---|---|---|
| Zero pageerror (home/shop/BR/LH/PDP/cart/privacy) | **PASS 9/9** | 0 pageerrors, 0 console errors on every load (was 4+/page pre-fix in this same headless env — WebGL guard working) |
| Hanken computed body font (≥5 pages) | **PASS 8/8** | `"Hanken Grotesk", Inter, sans-serif` everywhere; home `"Hanken Grotesk", sans-serif` |
| Consent banner reveal, no unstyled flash | **PASS** | hidden attr removed by JS, `position:fixed`, styled bg `rgba(10,10,10,.98)` at probe; `html.skyyrose-consent-open` present (clearance contract live). Mobile h=114 (compacted), desktop h=81 |
| Overlay stack occlusion | **PASS w/ note** | Banner+nav ≈ 185px total (was ~250px+widget clip). Mascot widget (PDP, h=63, bottom=620) sits fully ABOVE banner top=666 — no clipping. NOTE: banner bottom (780) overlaps nav top (773) by **7px** — nav renders 71px tall vs the 64px constant in the offset calc. P3 polish: share the nav height as a var. |
| Privacy table containment (mobile) | **PASS** | scrollWidth 390 = clientWidth; table display:block overflow-x:auto, right edge 374 < 390 |
| Collection lockup srcset (BR+LH mobile) | **PASS** | currentSrc = `i0.wp.com/...lockups/*.webp`; naturalWidth 349-350 vs 1600 pre-fix (Jetpack image CDN JS additionally right-sizes beyond our 480w floor — fine). Desktop natural 719. BR mobile screenshot: lockup crisp, hero clean |
| Shop grid @1440 | **PARTIAL FAIL → patched** | Container FIXED (h1 x=128, primary max-1600/pad-64), phantom grid item GONE (items in cols 1/2/3 at x=128/536/944), cards 2-3 render fully. BUT li width = 113px in 368px tracks: WC core ALSO ships `.columns-3`-qualified width rules (0,4,2) that outrank my (0,3,2) neutralizer. Source patched with `[class*="columns-"]` variant at matching specificity — needs next .min build+deploy. First card is the holo fallback (by-design card mix) and looks poor at 113px; should normalize once width lands |
| Cart (eyeball) | **PARTIAL — Atlas lane** | Empty state now the custom design (icon, "Your Cart is Empty", EXPLORE COLLECTIONS) — big improvement. h1 "Shopping Cart" still flush x=0: the canvas-template header sits outside the Woo container; pending Atlas's canvas-meta repoint |

**Net: 6 PASS, 1 partial-fail patched in source (shop card width — one build/deploy from closed), 1 partial pending Atlas (cart h1).**
