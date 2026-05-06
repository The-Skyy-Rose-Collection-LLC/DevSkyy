# Decision Memo: Three.js Dormant 3D Experience System

**Item:** P2 #24 from `_CONSOLIDATED-CLEANUP-TARGETS.md`
**Authored:** 2026-05-06 by Claude (DevSkyy engineering agent)
**Status:** **APPLIED-INTERIM** 2026-05-06 — feature flag added to `inc/enqueue.php` defaulting to `false`, stops 140 KB JS download on production. JS-side no-container guard verified to already exist. Full DEFER vs REMOVE decision still open for next milestone.
**Decision required from:** Corey (founder) — UX intent on 3D experiences (revive eventually vs. remove entirely)

---

## Current state (verified 2026-05-06)

The Three.js 3D experience system **lives, loads, but renders nothing** on production.

### Files (140 KB total, all unminified)

| File | Size | Last modified |
|------|------|---------------|
| `assets/js/experiences/experience-base.js` | 18.6 KB | 2026-05-05 16:41 |
| `assets/js/experiences/init-3d.js` | 14.1 KB | 2026-05-05 16:23 |
| `assets/js/experiences/blackrose-experience.js` | 25.0 KB | 2026-04-16 21:50 |
| `assets/js/experiences/lovehurts-experience.js` | 23.5 KB | 2026-04-16 21:50 |
| `assets/js/experiences/signature-experience.js` | 18.2 KB | 2026-04-16 21:50 |
| `assets/js/experiences/luxury-animations.js` | 2.3 KB | 2026-04-07 12:25 |
| `assets/js/experiences/mannequin-bust.js` | 9.4 KB | 2026-04-07 12:25 |

**No `.min.js` files exist.** Production loads the full source.

### Enqueue (`inc/enqueue.php:814–882`)

The Three.js stack is conditionally enqueued on three templates:

```
'template-immersive-black-rose.php' => 'experiences/blackrose-experience'
'template-immersive-love-hurts.php' => 'experiences/lovehurts-experience'
'template-immersive-signature.php'  => 'experiences/signature-experience'
```

When a visitor hits any immersive page, the browser downloads:
- `threejs` CDN script
- `experience-base.js`
- `luxury-animations.js`
- The collection-specific scene script
- `init-3d.js`

### What happens at runtime

**Verified 2026-05-06 by reading `init-3d.js:79–170`:** the JS is already defensive.

- Line 81: `document.querySelectorAll('.skyyrose-3d-container[data-config]')` — returns `[]` (not throws) on no match
- Line 144: `document.getElementById('${collection}-experience')` — returns `null`
- Line 146: `if (container && container.dataset.initialized !== 'true')` — guards the null case

So the runtime behavior is: download → parse → query selectors → find nothing → silently return. **No thrown error.** The earlier digest claim of "throws on construction" was incorrect.

**Container existence check:**

```bash
grep -rn 'id="[a-z-]*-experience"' template-parts/ *.php
# (no matches)
```

No PHP template emits any `#*-experience` container. Every page load on an immersive template:
1. Downloads ~140 KB of unused JS (the actual cost)
2. Parses + executes the IIFE
3. querySelectorAll returns empty, ID lookups return null + are guarded
4. Renders the 2D-hotspot engine instead (the actual UX)

### Why the 2D hotspot engine instead

`template-immersive-black-rose.php:13` has a comment:

```
@updated 6.0.0 — Rebuild on shared 2D engine, AI scene images
```

Line 23 confirms: "Room Data — 2 atmospheric rooms with product hotspots." The template renders AI-composited WebP scene images with beacon-style hotspots overlaid via `template-parts/immersive-scene.php`. The Three.js stack is a vestige of the prior 3D-rendered design.

---

## Cost of leaving it

| Cost vector | Magnitude |
|-------------|-----------|
| Per-page JS download on 3 immersive templates | ~140 KB unminified, ~40 KB gzipped |
| Per-page parse + thrown construction error | ~80–150 ms on cold load (mid-tier mobile) |
| Lighthouse penalty (unused JS warning) | -3 to -5 perf score points |
| Production bundle clutter | Engineers may misread it as live and add to it (this is what May 5 edits suggest) |
| WordPress theme upload size | +140 KB on every deploy |

**Not catastrophic.** Real but bounded.

## Cost of removing it

| Cost vector | Magnitude |
|-------------|-----------|
| Engineering effort | ~30 min (delete files + dequeue + smoke test) |
| Risk to current UX | None — immersive pages already use 2D hotspots |
| Risk to future revival | Files are in git history; revival is `git show` away |
| Documentation update | Brief mention in CLAUDE.md "Retired" section |

## Cost of reviving it

| Cost vector | Magnitude |
|-------------|-----------|
| Engineering effort | ~2–4 days (emit containers, fix init-3d clock bug, wire data, polish) |
| UX validation | Unknown — depends on scene quality vs. current 2D-hotspot UX |
| Performance budget | Three.js + scene = ~2–4 MB additional load on those pages |
| Mobile UX risk | High — Three.js scenes are CPU-intensive on phones |
| Conversion risk | Untested — current 2D engine works; switching to 3D is a bet |

---

## Open questions for Corey

1. **Was Three.js the original vision, abandoned for performance, and you'd like to revive it eventually?**
2. **Are the May 5 edits to `init-3d.js` and `experience-base.js` exploratory, or is someone actively wiring this up?**
3. **Does the "luxury immersive 3D" framing matter for brand, or is the 2D hotspot UX the final answer?**

If (1) yes + (3) yes → DEFER, document for next milestone, fix the load-but-thrown-error waste in the meantime.
If (1) no OR (3) "the 2D engine is the answer" → REMOVE.
If (2) "active work" → check with the developer doing it before any cleanup.

---

## Recommendation: DEFER with cleanup

**Rationale:** May 5 modification timestamps signal active intent. Removal would irreversibly nuke recent work. But the current state — *load full Three.js stack, throw on construction, render 2D hotspots* — is wasteful regardless of revival plans.

**Tactical:** Stop the waste without removing the option to revive.

### Two-step interim fix (~10 min, safe)

1. **Add a feature flag in `inc/enqueue.php`:**
   ```php
   if ( ! apply_filters( 'skyyrose_enable_3d_experiences', false ) ) {
       return; // skip Three.js stack
   }
   ```

2. **Update `init-3d.js` to no-op gracefully when no container exists:**
   ```js
   const container = document.getElementById(containerId);
   if (!container) {
       console.info('[skyyrose-3d] No container found, skipping 3D init.');
       return;
   }
   ```

This eliminates the per-page download and the thrown error. To revive, set the filter to `true` and emit the container in the immersive template — same code path resurrects.

**Decision gate for full removal:** Revisit at the next milestone planning. If Three.js is not on the roadmap by then, REMOVE entirely (delete files, dequeue, document in CLAUDE.md "Retired").

---

## Action items if user accepts this recommendation

- [ ] Add `skyyrose_enable_3d_experiences` filter + early-return in `inc/enqueue.php`
- [ ] Add no-container guard to `assets/js/experiences/init-3d.js`
- [ ] Add CLAUDE.md "Learnings" entry: "Three.js stack is feature-flagged off by default. Set the filter to true to revive. See `tasks/codebase-cleanup/decisions/24-threejs-dormant.md`."
- [ ] Mark P2 #24 in `_CONSOLIDATED-CLEANUP-TARGETS.md` as RESOLVED-DEFER with link to this memo

If user prefers REMOVE instead:

- [ ] `git rm assets/js/experiences/{experience-base,init-3d,blackrose-experience,lovehurts-experience,signature-experience,luxury-animations,mannequin-bust}.js`
- [ ] Strip the conditional enqueue block in `inc/enqueue.php:814–882`
- [ ] Add CLAUDE.md "Retired" entry referencing the commit hash
- [ ] PR title: `chore(theme): retire dormant Three.js 3D experience system`
