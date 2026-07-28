# Scroll-World FINISH Plan — single-conversation closeout (2026-07-20)

Outcome: scroll-world ad campaign + collections site at production tier, shipped or founder-gated.
Session: snoopy-roaming-globe worktree, /loop self-paced. Spec of record: tasks/scroll-world-ad-spec.md.

## Ordered by importance to outcome

### P1 — Ship the site branch (biggest unshipped value)
- [x] Review 38 commits on `worktree-collections-scroll-world` vs main — Fable verdict: feature clean, bundled catalog-naming commits conflict with main (br-006 rename collision)
- [x] Verify: php -l 4/4 pass, .min current (grep-verified), freshness-guard pass, no rider-deletion risk
- [x] Clean branch `feat/collections-scroll-world` extracted (14 files) → **PR #774** open, CI 4/4 green
- [x] Ultracode adversarial review (18 agents, 5 lenses, every finding re-verified): 13 raw → 10 confirmed → ALL FIXED in b466b9b9d (lazy-load defeat ~836KB, missing perf-gating slugs ~95KB, Photon srcset for stills+preload, safeHref ×2, crossfade:0 NaN, will-change gating, preview.html moved out of deployable dir, comment fixes, jersey-build.sh docs)
- [x] GATE CLOSED 2026-07-22: PR #774 MERGED (squash f8e9895b3) + PR #785 MERGED (43ffb0467, buglog union-merged) + theme DEPLOYED (134s, 13/13 assertions, riders 7/7, v1.12.7). Page 10315 /collections-world/ created (WP.com MCP; template via wp-cli meta — REST template enum empty on this proxy). Live-verified: HTTP 200 93KB, scroll-world .min css+js enqueued, Playwright mobile+desktop clean, packshot bytes md5-match. KNOWN GAP: scene camera-leg mp4s (scene-N*.mp4 + -m.mp4) never produced/uploaded — engine fails closed to still-scrub (1 expected console 404). Free follow-up: map campaign dive clips (f1-sig/f0-br/f1-lh/f1-kc-dive) -> leg filenames, SFTP, re-verify.
- [ ] FOLLOW-UP GATE (founder): br-006 canonical name — main says "The Bomber Sherpa" (slug kept), branch says "The Black Rose Bomber Sherpa" (slug+file renamed). Pick one, then land catalog-naming pass as separate PR.

### P2 — Production QC gate on the 6 films (bug-276 mandate) — COMPLETE 2026-07-21
- [x] Independent Fable QC, side-by-side vs canon at full-res, in-motion frames: **ALL 6 SHIP**, zero paid-fix defects. Technical pass clean (no black frames / freezes). Mascot identity holds vs canon across films; monogram, CTAs, garments verified vs real refs. Frames kept in scratchpad/filmqc/ for founder review.
- [x] Side-discovery FIXED: br-014/br-015 packshots (source-photos + theme) were byte-identical to br-003 black jersey — shop showed wrong garment for 2 SKUs. Eyes-on verified + repointed → **PR #785** (bug-277).
- [ ] FOUNDER-CALL: lh-005 fannie pack is NOT in the Love Hurts film — no fannie asset exists in the ad tree (never built). Options: accept as-is (film ships without it) or fund a fannie garment loop (paid render) + free re-splice.
- [ ] Follow-up (free, census first): rename misfiled `br-003-jersey-{giants,white}-front.jpeg` source files.

### P3 — House film audio completion (only hard blocker on flagship)
- [x] 3 candidates found + license-verified (all CC BY 4.0 via FMA; Pixabay/Mixkit/chosic/freepd unreachable): Kitana (1000 Handz), Head Soul (Ketsa/"Concrete Flowers"), Streetlight Star (Joseph Sacco). Credits + evidence: renders/scroll-world/ad/audio/beds/CREDITS.md
- [x] Best rising-energy 24s window found per track (ffmpeg volumedetect scan); 3 preview muxes built (bed ducked 0.32× under VO 12.6–18.4s, loudnorm I=-14): final/previews/house-bed-{kitana,headsoul,streetlight}.mp4 — sent to founder
- [ ] GATE (founder pick): track choice (Kitana = data-backed recommendation: +10dB build ending on natural finale)
- [ ] After pick: final mix pass on house-1080 masters + credit line added to delivery doc

### P4 — Paid finishing layer (one manifest, one y per call)
- [ ] STOP-AND-SHOW manifest: per-film VO ×5 (~0.4cr ea, seed_audio "Skye"), optional 16:9 reframe (paid), optional 2K hero (~7cr), optional jersey uniformity re-render, br-009 on-model R-sleeve verdict (founder eyeball → $0.40 inpaint if off)
- [ ] Fire only items founder approves; QC each vs canon before accept

### P5 — Final packaging + closeout
- [ ] Masters + captions inventory in spec; delivery doc
- [ ] Update project memory (project_scroll_world_build) + .wolf/memory.md; sync spec status
- [ ] Loop stop

## V4 FLIGHT PLAN — restructure around Higgsfield expertise (founder-directed 2026-07-21)

Principle: every film is ONE CONTINUOUS CAMERA FLIGHT (generation grammar), not segments+xfades
(editing grammar). Logo bookends = launch/landing pads. Garments are encountered IN the world
via the existing `garments/*-world.png` composites — never cut to a floating product photo.
Clips chain by shared frames: each shot's end frame (extracted free) anchors the next shot's
start_image. Engine: seedance_2_0 fast 4s = 14cr/clip (verified). Every clip QC'd in-motion
vs canon (bug-276 method) before the next fires. One y per clip.

### Shot grammar per collection film (~12s, 3 paid clips)
- A DIVE    logo → world: camera dolly-pushes into the approved scene still
            (SIG: through the monogram curl · BR: orbit into the silver star ·
             LH: down the cathedral aisle · KC: down the rose-gold corridor)
- B SWEEP   end(A) → <garment>-world.png: camera swings to find the garment in-scene,
            fabric/model motion (LH uses bomber-canon-world; joggers rejoins after the
            0.5cr heart-rose-composite re-still)
- C RESOLVE garment-world → pull-back that lands on the collection logo + CTA
Free between clips: end-frame extraction, assembly, music, grade (v3 edit grammar).

### Shared-shot pool (the restructure's economics)
The same accepted shots serve BOTH product lines — 5 collection cuts AND the House anthology
(its locked 11-shot storyboard already IS this flight design; previz validated every
composition). House hero pass adds: 4 portal morphs + KC payoff + hook at fast tier.

### Budget ladder (per-clip y, sequential)
- F0 taste test — Black Rose flight A+B+C ............ 42cr  ✅ COMPLETE 2026-07-21:
  3/3 clips first-take QC PASS (jobs 07b39a02 / 27bdb9ef / 0042034c), chain seams landed
  on anchors, film-black-rose-flight.mp4 (15.5s) delivered. mode:"fast" param + preset-decline
  playbook logged in spec registry. Balance after F0: ~769.6
- F0.5 JERSEY flight (10 clips, founder-designed) .... 140cr  ✅ COMPLETE 2026-07-21:
  br-009 patch fix (free PIL) + br-012 green re-render ($0.40 OAI) preceded spend;
  10/10 first-take QC PASS, film-jersey-flight.mp4 (43.75s SILENT) assembled.
  Open note: J-B aerial reads Golden Gate vs J-A Bay Bridge — 14cr re-roll gated on y.
- F1 SIG + LH + KC flights (9 clips) ................. 126cr ✅ COMPLETE 2026-07-22 (9/9 first-take;
  films film-{signature,love-hurts,kids-capsule}-flight.mp4; resolves land pixel-true on v7 lockups)
- F2 House hero: 4 morphs + KC payoff + hook ......... 70cr  ✅ COMPLETE 2026-07-22 (5/5 first-take,
  hook = free f1-sig-dive reuse; film-house-flight.mp4 36.88s; mascot identity PASS vs canon)
- F3.5 KC journey redesign (4 stills + 3 clips) ...... 44cr ✅ COMPLETE 2026-07-22 (journey-to-throne
  21.79s: SIG statue / BR roof / LH hallway walks, all first-take; both kids sets in film)
- F3 LH joggers corrected still (gpt_image_2 1k/low) . 0.5cr ✅ COMPLETE 2026-07-22 (heart-rose-composite
  thigh logo QC PASS; joggers beat restored in LH flight film)
- F4 audio: child voice (record-via-widget 0cr + 0.4cr/line | pitch test 0.4cr | caption-only)
       + per-film VO ×5 ≈ 2cr · music pick A/B/C (free)
- F5 upscale/reframe — free get_cost preflight first
Ceiling ≈ 255cr all-in vs balance ~851cr. Re-rolls cost the same per clip; jerseys/fine
lettering = likeliest re-roll candidates.

## Status log
- 2026-07-20: plan authored; P1 review agent + P2 QC agent + P3 music research dispatched in parallel.

### Film embeds SHIPPED 2026-07-23 (income step 2)
- 4 web encodes (crf24, 2.6-3.8MB) + posters → Media Library IDs 10322-10329 (uploads/2026/07/ — uploads, never theme assets, no new riders).
- template-parts/collection/page.php: col-film section (muted autoplay loop, poster, reduced-motion → static poster swap) between hero and shop grid; collection-pages.css + .min rebuilt.
- Deployed + live-verified: SIG/BR/LH pages play films (mobile+desktop eyes-on); mp4s serve 206 ranges. KC = launch-mode teaser template (founder-locked, no film BY DESIGN) — teaser embed = founder call.
- scp gotcha logged: WP.com scp/SFTP chroots to htdocs/ while ssh shell home = /home/<id> — same "tmp-films/" path names two different dirs.
