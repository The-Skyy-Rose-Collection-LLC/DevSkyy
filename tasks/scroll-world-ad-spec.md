# SkyyRose — Collections Ad Film (spec)
> **v2 research-driven revisions are at the BOTTOM of this file — they supersede any conflicting v1 detail. Read them.** (Full research: `tasks/ad-build-research.md`.)

# v1 (original concept)

**What:** a ~22s cinematic brand ad for paid social (9:16 primary + 1:1 + 16:9 cutdowns), cut from the same photoreal gothic-noir worlds as the website scroll-world. **Render once, use twice.**

**Founder direction (verbatim):** show the collections they already know first (Signature, Black Rose, Love Hurts); between those clips the mascot walks in **feet-up**, revealed progressively; at the **Kids Capsule** reveal her walk-in completes with her **introduction** — a short powerful line on the **rebrand + the new Kids Capsule**. Audio = **no music**, dramatic instrumental **sound statements** + a **voice identity**. The reveal literalizes the tagline: **the SR monogram grows out of concrete** (not the text "Luxury Grows from Concrete").

---

## Storyboard (≈22s, 9:16)

| t | Beat | Visual | Mascot | Sound |
|---|------|--------|--------|-------|
| 0:00–0:03 | **HOOK** | Inside the Signature world — dusk Oakland skyline through glass, gold SR-monogram statue on marble plinth. Slow forward glide. | — | deep sub-boom + Oakland ambience |
| 0:03 | reveal 1 | hard cut | **feet / boots** stride into frame | footstep impact |
| 0:03–0:06 | **Black Rose** | gothic rooftop, silver moonlight, black rose + star emblem | — | silver tension riser |
| 0:06 | reveal 2 | hard cut | **up to the knees** — walking in | second impact, closer |
| 0:06–0:10 | **Love Hurts** | crimson cathedral, enchanted rose under glass | — | deep romantic-dark swell |
| 0:10 | reveal 3 | hard cut | **up to the torso** — almost there, face still withheld | riser tightening |
| 0:10–0:16 | **KIDS CAPSULE — PAYOFF** | world lifts into warm rose-gold light (the NEW drop). Her walk-in **completes**: full-body, turns to camera. | **full reveal + VOICE line** (rebrand + new KC) | tension resolves → bright statement; her voice carries |
| 0:16–0:20 | **REBRAND REVEAL** | the **SR monogram grows out of cracked Oakland concrete** — rose-gold rising from the pavement, cracks radiating, gold light. Literal "luxury grows from concrete." | — | rising harmonic → **brand stinger** |
| 0:20–0:22 | **CTA** | monogram resolves → **"The Skyy Rose Collection"** + shop. | — | final resonant hit |

Camera order = the collections' canon order (SIG → BR → LH → KC), same as the website legs. The feet-up mascot reveal is **synced to the tour** and pays off exactly at the new-collection reveal.

---

## Voice line (the mascot's ONE spoken moment, ~0:10–0:16)

Short, powerful, covers the rebrand + the new Kids Capsule, ends toward "The Skyy Rose Collection". Corey/SkyyRose voice; NOT European-heritage; no hype clichés. **"the bloodline that raised me" is Love Hurts ONLY — not used here.**

*A voice-line panel (8 options) is being generated; drafts to seed it:*
- A — "Oakland built a house. Four worlds, one name — and the newest crown yet. The Kids Capsule."
- B — "We don't grow up. We level up. Same concrete, new heirs. The Skyy Rose Collection."
- C — "You know the worlds. Now meet the ones coming up — suited. The Skyy Rose Kids Capsule."

→ **founder picks / edits before the voice is built.**

---

## Audio (no music)

- **Sound statements** (`generate_audio`, NOT music): sub-boom hook, per-reveal impacts, tension risers, a resolving harmonic at the payoff, a final brand stinger. Cinematic sound design bed.
- **Voice identity** (`create_voice`): build one SkyyRose mascot voice, then generate the approved line. Voice is a brand asset — reusable across future ads.
- **Muted-safe:** 85% of paid-social plays muted → the line also appears as **on-screen caption** at the payoff, and the CTA text is always on-screen.

---

## Production manifest (Higgsfield + ffmpeg)

| Shot | Tool / model | Shared w/ website? | Est. cr |
|------|--------------|--------------------|---------|
| SIG / BR / LH / KC world clips (4 legs) | `generate_video` seedance_2_0, 1080p, forward-glide | **yes** (website legs) | ~48 |
| Finale leg (→ monogram-from-concrete) | `generate_video` | partial | ~12 |
| Mascot feet-up fragments ×3 (feet, knees, torso) | `generate_video` from mascot ref (`skyy-canonical-v2.png`), consistent identity | ad-only | ~36 |
| Mascot full reveal + turn (at KC) | `generate_video` | ad-only | ~12 |
| **Monogram-grows-from-concrete** hero | `generate_video` from a concrete still → monogram rises (rose-gold, cracks) | ad-only (reusable) | ~12 |
| Sound design (~5 statements) | `generate_audio` | ad-only | preflight |
| Voice identity + line | `create_voice` + generate | ad-only (reusable) | preflight |
| Assembly + 9:16/1:1/16:9 cutdowns | ffmpeg + `reframe` | — | free / cheap |
| Re-roll budget (mascot consistency is the hard part) | — | — | ~40 |

**Est. total ≈ 150–190 cr** of 1000 (voice + sound preflight to firm). Legs (~48–60cr) are shared with the website, so the ad's *marginal* cost is ~100–130cr.

---

## Risks + de-risk gate

1. **Mascot identity in generated video is the make-or-break unknown.** AI video drifts character faces/proportions. Before spending the full mascot budget, **fire ONE mascot feet-up fragment (~12cr)** from `skyy-canonical-v2.png` and eyes-on whether Higgsfield holds her identity + does the feet-up framing. If it holds → proceed. If it drifts → pivot (use the 3D rig / composite the canonical mascot over generated worlds instead of generating her).
2. **World-to-world morph** (Architecture A) — the website legs already carry this risk; test Leg 0 first (as before).
3. **Feet-up mechanic legibility** on a muted phone feed — being pressure-tested by the ad-effectiveness pass; may need on-screen text cues.

**De-risk order:** (1) mascot fragment test ~12cr → (2) Leg 0 test ~12cr → if both read, fire the full batch.

---

## Reuse mapping (website ↔ ad)

| Asset | Website scroll-world | Ad film |
|-------|----------------------|---------|
| 5 world legs | scroll-scrubbed camera | linear world-tour cut |
| 5 scene stills | poster frames / reduced-motion | — |
| Monogram-from-concrete | (optional hero treatment) | rebrand reveal |
| Mascot clips | — | the through-line |
| Voice + sound | — | ad audio (reusable brand assets) |

Delivery: `9:16` master → `reframe` → `1:1` (feed) + `16:9` (YouTube/pre-roll). Encode `libx264 -crf 20 +faststart`.

---

# v2 — RESEARCH-DRIVEN REVISIONS (supersedes conflicting v1 above)
*Source: `tasks/ad-build-research.md` (4-agent deep research, 2026-07-16).*

## Changed decisions
1. **Mascot hero shots = composite the rigged 3D GLB over AI world plates** — NOT full AI-generation. AI video still drifts her face/outfit at hero close-up tolerance. Register `skyy-canonical-v2.png` as Higgsfield Element `@skyy` (+ `@skyy-outfit`) for any low-stakes AI walk-in/silhouette shots only. Optional: render ~20 GLB angles (free) → train Soul ID (~$1.25, gated) for cross-shot lock.
2. **Transitions = disguised "portal" moves, NOT free morphs.** One continuous camera gesture carries each seam: push through a rose-gold archway → rooftop; plunge through crimson petals/fog → cathedral; flare through a doorway → capsule set. (Kling docs: wildly-different start/end frames break the morph.) Prompt each clip "single continuous shot, no cuts," name the camera verb, state what it does NOT do; negatives `jump cut, hard cut, strobing` at seams.
3. **Monogram-from-concrete = forward-only, pinned play-once** on arrival — REMOVE it from the scroll-scrubbed timeline (irreversible cracks/rise/dust un-form when scrubbed backward). Build as start/end-frame "Lock-Move-Land" on kling3_0 (start = emblem flush in cracked concrete; end = risen dimensional rose-gold monogram; rose-gold particle-convergence).
4. **Audio path CORRECTED:** Higgsfield `generate_audio` is TTS-only — it can NOT make the cinematic sound design. Use `create_voice` for the mascot voice; get sound design from EITHER a native-audio video model (WAN 2.5 class) OR a licensed SFX library mixed in post. Master at **-14 LUFS / -1 dBTP**.
5. **Muted-first, captioned.** ~70–85% watch muted → burn in styled captions for the whole ad (hook line, per-world collection labels, VO verbatim, CTA), in the center safe band (avoid top ~130px / bottom ~20% / right ~140px). Caption font = brand (Archivo/Anton).
6. **Open on the mascot in motion + face/eye-contact**, not the empty Signature architecture. Resolve "this is SkyyRose" EARLY; surface a brand/shop cue by ~sec 8–10; reserve the finale for the *specific* news (rebrand + Kids Capsule).
7. **CTA split by product state:** "Shop the Collections" (Signature/Black Rose/Love Hurts, live) + **"Join the Waitlist" for Kids Capsule** (launch-mode, not buyable — VERIFY SKUs before any shop CTA).
8. **Two cuts, not one:** (A) the ~22s cinematic brand-launch cut → warm/retargeting, judged on recall/brand-lift; (B) a 9–15s product-forward cold-prospecting cut, CTA in first half. 9:16 primary; 1:1/16:9 are reframes.
9. **Scroll-scrub website legs encode:** `-g 8 scenecut=0`, dual H.264 MP4 + VP9 WebM, `+faststart`, blob-load, poster per scene, `prefers-reduced-motion` branch; test iOS single-active-decoder on real hardware.

## GATING DECISION (founder)
**What is this ad's objective + audience?**
- **Warm / brand-launch** (retargeting + brand-lift measurement) → the cinematic 22s vision holds; fixes are caption discipline + earlier brand resolution.
- **Cold prospecting** (conversion/ROAS) → lead with the short product-forward cut; the 22s cinematic is a secondary/retargeting asset.
This decision defines "done" more than any single tactic. Recommended: build BOTH (the 22s cinematic warm cut is the founder's vision; the 9–15s cold cut is cheap to derive from the same footage).

## Revised de-risk order (before the full spend)
1. **Composite test (free-ish):** render the GLB mascot over one AI world plate → confirm the rig+plate composite reads premium. Zero/low paid cost.
2. **Portal-transition test (~12cr):** one world→portal→next clip, to prove the disguised-seam technique.
3. **Monogram-from-concrete test (~12cr):** the Lock-Move-Land emergence shot.
If all three read, fire the full batch. (Mascot AI-fidelity test from v1 is downgraded — we're compositing the rig instead, so that risk is largely removed.)

## LOCKED (founder decisions, 2026-07-16)
- **Objective = BOTH:** 22s cinematic cut → warm/retargeting (recall/brand-lift); 9–15s product-forward cut → cold prospecting (CTA in first half). Both derived from the same footage.
- **Voice line (mascot, at the Kids Capsule reveal):** "The house grew up. Now the next generation gets suited too." (panel top pick — built from canon "next generation, suited", hits rebrand + KC evenly.)
- Mascot = composite the rigged GLB for hero/reveal; audio via create_voice + (WAN-native OR licensed-SFX+post); captions burned-in; CTA split (Shop live / Waitlist KC).

## LOCKED v3 (founder, 2026-07-16 — previz forks resolved)
- **Mascot = the CHILD** (scene-4's figure IS the SkyyRose mascot, not an adult). No adult-GLB composite for the ad — AI-gen the child with a scene-4 reference-lock (@skyy Element). Tease shots (feet/knees/torso) have NO face → drift-tolerant/low-stakes; only the KC face-reveal needs identity-lock + a re-roll budget.
- **Hook = FEET-UP TEASE** (founder override of research's face-open — "fans already know it's Skyy"). The child's feet→knees→torso reveal syncs across SIG→BR→LH and completes at the Kids Capsule payoff. (The 9–15s COLD cut stays product-forward per research; the tease is the WARM/cinematic cut's device.)
- **KC reveal = the child mascot** turns to camera + delivers "The house grew up. Now the next generation gets suited too."
- **Finale start-plate = CEMENT CRACKING** — SR monogram flush in cracking Oakland concrete (unlit) → rises, rose-gold, resolving to the gold Signature monogram (full-circle). Forward-only/pinned.
- Morphs (pixel-verified feasibility): BR→LH (the rose) = strongest; SIG→BR + LH→KC + KC→finale need cheap bridge stills first.

## PREVIZ ASSEMBLY RECIPE + COLD-CUT EDL (referenced by .claude/workflows/skyyrose-ad-previz.js assemble phase)

### Assembly (previz tier: 720x1280@24 · final tier: 1080x1920, same logic)
1. **Normalize** each clip: `ffmpeg -i IN -vf "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=24,format=yuv420p" -c:v libx264 -crf 18 -preset veryfast -an OUT`
2. **Concat with 0.2s xfade** at morph seams — build the xfade chain programmatically (offsets are cumulative: `off_n = sum(durations_0..n-1) - n*0.2`, durations via ffprobe).
3. **Burn captions** (drawtext, Archivo/Anton TTF), center safe band (avoid top ~130px / bottom ~20% / right ~140px at 1080x1920; scale proportionally at previz res): SIGNATURE / BLACK ROSE / LOVE HURTS world labels; VO verbatim at KC reveal ("The house grew up. Now the next generation gets suited too."); end card "SHOP THE COLLECTIONS · JOIN THE WAITLIST — KIDS CAPSULE".
4. **Audio** (final tier only): loudnorm `I=-14:TP=-1:LRA=11`, mux AAC 192k.
5. **1:1**: center-crop the pre-caption master, re-run captions repositioned (never crop a captioned file). **16:9**: Higgsfield `reframe` at final tier only (previz fallback: blurred-pillarbox, never ship it).

### Cold-cut EDL (9–15s, product-forward, cold prospecting — derived from the same normalized pool, no new gens)
1. 0.0–1.2  Open on the single most striking world beat (LH enchanted rose or SIG monogram push) — product/world forward, NOT the tease (tease is the warm cut's device).
2. 1.2–4.0  Hard-cut montage of the remaining world beats (0.5–0.9s each: SIG → BR → LH order preserved), each with its collection label caption.
3. ~3.0     Persistent lower-third CTA fades in: "SHOP THE COLLECTIONS" (research: commercial cue in the first half).
4. 4.0–7.5  KC reveal trimmed (child turns to camera; VO line captioned verbatim).
5. 7.5–8.5  Finale emergence trimmed/sped (monogram rises).
6. 8.5–11+  Full-screen CTA card, extended hold: SHOP THE COLLECTIONS · JOIN THE WAITLIST — KIDS CAPSULE. Widen montage/holds to reach 15s if desired.

---

## MEDIA REGISTRY (Higgsfield media_ids — account-durable; REUSE, never re-upload)

| media_id | file | note |
|---|---|---|
| 6eac53a2-cede-40e7-94e3-b90c1044b76c | ad/frames/monogram-gold.png | plain-gold statue crop (superseded as mark by rose canonical) |
| c9a0a7d5-70d2-41e7-bc62-3f70ae03afe6 | ad/frames/mascot-feet.png | scene-4 crop (off-canon identity, bug-268) |
| 1db24675-e967-4b4c-9933-13eeaa8db9ae | ad/frames/mascot-knees.png | scene-4 crop (off-canon) |
| be31ba69-413f-42a2-a90f-9277b5a0a5ee | ad/frames/mascot-torso.png | scene-4 crop (off-canon) |
| ac6eeb7b-15ea-4eb9-b122-a01fd9dedc4b | ad/frames/star-point.png | |
| af41e0e0-176d-415f-91f4-971803f299f2 | ad/bridges/sig-br-flare.png | |
| 4a3bbf8f-36d0-4062-a7ea-a35dd5408dd9 | ad/bridges/finale-concrete.png | plain-mark engraving (v2 re-render gated) |
| 21539624-2452-4827-8f90-ba9485050493 | ad/bridges/finale-risen.png | STALE — uploaded pre-v4; file now has rose mark; re-upload before use |
| 83538c7c-1b4e-40a7-b3d9-7db06fbe56e7 | ad/frames/kc-lightbeam.png | |
| 6756ab9e-6c3a-4371-8a93-174e99220901 | assets/branding/mascot/skyy-canonical-reference.jpeg | ISSUED, PUT PENDING |
| f3ca2d19-4dac-405d-8647-33611b686ee1 | assets/branding/mascot/skyyrose-mascot-reference.png | ISSUED, PUT PENDING |
| 12e6586c-87d8-4fa9-b9fe-c87b29245211 | assets/branding/sr-monogram-rosegold-canonical.png | ISSUED, PUT PENDING |

Higgsfield job IDs (results re-downloadable via job_status): sig-br-flare fc27fc36 · lh-kc-petal 0280f5a3 · lh-kc-arch-ignite 973e2b85 · finale-concrete 5349893c · clip-sig 6d53e0dc · clip-br 2fa304b1 · clip-morph-rose 8ba09008 · clip-lh 56475f4a · clip-morph-lh-kc 8b3209a9 · clip-kc-reveal 22ee1e3d · clip-tease-knees 75b99167 · clip-tease-feet 55cc0ddf · clip-tease-torso 75103469 · clip-morph-sig-br b841e48a · clip-morph-kc-fin d25b32be · clip-finale b39f92de

### Higgsfield Elements (identity engine — embed <<<id>>> in prompts; created 2026-07-16)
| element_id | name | category | sources |
|---|---|---|---|
| cf20a690-7828-4738-9557-2ef00bc42591 | skyy-mascot | character | skyy-canonical-reference.jpeg + skyyrose-mascot-reference.png |
| 7f6e1df4-c4c9-4b89-83be-20f26e14a8b6 | sr-monogram-rose | prop | sr-monogram-rosegold-canonical.png |

kc-arch-bg.png media_id: 8076b0e1-1405-4cac-9b65-65d1cc657a55 (uploaded by bridges run)
Reshoot-round jobs (2026-07-16 y+kc, 24.5cr): finale-concrete-v2 05d67472 · tease-tiltup-v2 656b26bc · kc-reveal-v2 d5c8d687 · kc-world 2b830a1f (+ kc-fin-v2, finale-v2 after plate lands)

### Reshoot round v2 (y+kc, 24.5cr cap 26) — job IDs
| job_id | item | model | cr |
|---|---|---|---|
| 05d67472-fe27-4a81-a56e-88fadeb4a1a3 | finale-concrete-v2 (rose mark engraved) | gpt_image_2 1k/low | 0.5 |
| 656b26bc-35a5-45dc-9688-538428639719 | tease-tiltup-v2 (Element skyy-mascot) | seedance_2_0 fast/480p | 6 |
| d5c8d687-606d-4da9-9f86-3fb96f518c78 | kc-reveal-v2 (Element skyy-mascot) | seedance_2_0 fast/480p | 6 |
| (pending fire) | kc-world | seedance_2_0_mini 480p | 4 |
| (pending fire, needs concrete-v2) | kc-fin-v2, finale-v2 | seedance_2_0_mini 480p | 4+4 |

### Round v2 additions
media: finale-concrete-v2 = a529db4a-4eb2-4db6-9a3c-88664b421dab · finale-risen-v2 = 130d3cec-aa4a-4feb-887b-daabd9f93fd4 · canon uploads: skyy-canonical 6756ab9e / mascot-ref f3ca2d19 / rose-monogram 12e6586c
jobs: kc-world ff7e17e9-cbe1-400a-8066-c4a7546b6dd0 · kc-fin-v2 24465ebb-430a-43b7-8c68-ddf97eda2ac3 · finale-v2 17b27400-f47c-4890-a837-8bd1e2147268 (after declined_preset_id IN THE DARK)
IDENTITY GATE PASSED (eyes-on): tiltup-v2 + kc-reveal-v2 = canonical toon Skyy, on-model, one character. PLATE GATE PASSED: rose mark engraved correctly.

### B-takes (pre-restart zombie session duplicates — real paid outputs, usable alternates)
| job_id | item | note |
|---|---|---|
| 2b830a1f-8204-491a-a187-ca5ee42fbadc | kc-world B-take | 05:33:20Z |
| 8d693759-09a4-40bc-90c6-124d40410343 | kc-fin B-take | end plate 49f02dd4 (zombie's own upload) |
| 0b9d2a23-2df6-47df-b9bb-451ef4047a7b | finale B-take | plates 49f02dd4 → ca85b34d (zombie's own composite) |
Round v2 ACTUAL: 36.5cr (24.5 approved + 12 restart-duplication, bug-269). Balance 913.5.

### LOCKED (founder 2026-07-17): Skyy's jacket script
The varsity jacket chest script reads EXACTLY "Love Hurts" (red brand script, as on skyy-canonical-reference.jpeg). Acceptance criterion for torso tease + KC reveal at FINAL tier: script legible and correctly spelled. Any character re-fire prompt must state: 'the jacket's chest script reads exactly "Love Hurts" in red cursive lettering, matching the reference'.

### Round v3 (y+jacket, 21cr cap 22) — Context7-verified: gpt_image_2 = text-rendering/typography/editing model; text anchored in stills, video driven FROM them
media: scene-1 original = a1bf8c9f-9f34-4a33-a005-f1f942ee7b0d · statue crop rose = 55b4d6df-1f06-4cf0-b56b-5885456d23a6
stills (gpt_image_2 1k/low 0.5cr each, both eyes-on PASSED): scene-1-v2 = bf444534-f304-4215-ab3f-1db1cfee285f (rose statue, scene preserved) · skyy-anchor = bb794b66-7605-41b0-9e4a-8aeb2911c23d ("Love Hurts" legible; ad/frames/skyy-anchor.png)
clips: reveal-v3 9d823aa5-457e-4d8d-9c62-296dc7107f55 (6cr, start=anchor) · tiltup-v3 a54da5c2-af0e-466b-8909-0557b943c28b (6cr, ref=anchor) · clip-sig-v2 1be1fdcc-4cbd-4305-b736-93f0d0fa1f8d (4cr, start=scene-1-v2) · sig-br-v2 6afb506c-bc15-4896-b53d-f0423beed954 (4cr, start=crop)

#### Round v3 — completion (verified 2026-07-16 23:14)
All 4 clips COMPLETED, downloaded, ffprobe-verified 496x864/4.04s, eyes-on gate PASSED:
- reveal-v3 → `ad/previz/clip-reveal-v3.mp4` — identity on-canon, "Love Hurts" legible+correct.
- tiltup-v3 → `ad/previz/clip-tiltup-v3.mp4` — outfit on-canon, script legible at torso; chin enters ~3.8s → torso beat trimmed to end 3.60s.
- sig-v2 → `ad/previz/clip-sig-v2.mp4` — rose-adorned monogram statue dolly-in, skyline preserved.
- sig-br-v2 → `ad/previz/clip-sig-br-v2.mp4` — rose-monogram → flare portal → star point.
Slices (from normalized tiltup-v3): feet 0.00–1.35, knees 1.35–2.70, torso 2.70–3.60 → `ad/work/norm3/clip-tease-{feet,knees,torso}-v3.mp4`.
Preview: `ad/out/preview-flow-v3.mp4` (13 shots, 44.08s, 720x1280@24). EDL = `ad/work/concat3.txt` (v3 replaces sig, 3 tease beats, sig-br morph, kc-reveal; rest from norm2).
Spend reconciled: balance 913.5 → 892.5 = 21cr exact (cap 22). No zombie duplicates.

#### Round v4 — ROI optimization pass (Fable creative-director agent, FREE, 2026-07-16 ~23:30)
Visual diagnosis of v3: hook C+ (static 1.5s open), 4 morphs = 16.16s/36.7% dead transition time, reveal buried at 73%, zero muted-autoplay text.
Executed (0cr): `ad/out/preview-flow-v4.mp4` (30.5s, −31%) — feet-tease cold open (reveal NOT spoiled), SIG setpts 0.55x, morphs setpts 0.4x (departure+arrival frames preserved), worlds 0.65x, reveal untouched full 4.04s now at 63%, finale +1.5s frozen hold; new PIL text system (SKYYROSE wordmark fade-in, per-collection kinetic captions incl. new KIDS CAPSULE, "Luxury Grows from Concrete." end card; old SHOP-THE-COLLECTIONS endcard deliberately unused). Plus `ad/out/preview-flow-v4-6s.mp4` 6.0s bumper.
Re-verified independently: ffprobe 720x1280@24 yuv420p both cuts + 6-frame eyes-on grid (`ad/work/v4/reverify/`) — captions legible, marks correct, reveal clean. v3 untouched.
Paid recs (NOT fired): SIG opener regen 6cr · A/B reveal 2x4cr · flash-cut open 6cr · VO/music layer (needs preflight). Balance still 892.5.
Full report: `ad/out/roi-optimization-report.md`.

#### Round v5 — restructured cut, founder shot-order latitude (Fable creative-director, FREE, 2026-07-16 ~23:48)
`ad/out/preview-flow-v5.mp4` (31.4s) — 2-glimpse cold open (BR+LH held real-motion, no character), feet-tease relocated after SIG. Kept as a founder A/B alternate; NOT conformed to this spec (built before this doc was read in full).

#### Round v6 — spec conform: locked warm (22s) + cold (9-15s) masters (Fable creative-director, FREE, 2026-07-17)
**Context:** v4/v5 were built without reading this spec doc in full — shipped with the wrong end card (tagline instead of the locked CTA) and no locked VO caption, and neither hit the two-cut requirement (line 104/120). Corrected and conformed both cuts to LOCKED v3 + the assembly recipe (lines 124-146).

**`ad/out/master-warm-22s.mp4`** (22.875s, target "~22s") — v4's structure (feet-up-tease hook per line 126, world order SIG→BR→LH→KC unchanged), re-cut at more aggressive speed factors (worlds setpts=0.43, morphs setpts=0.26; tease beats + reveal untouched) and reassembled with a **12-seam 0.2s xfade chain** (spec line 135 cumulative-offset formula: `off_k = sum(durations[0:k]) - k*0.2`), not the hard-concat v4 used. Locked VO caption ("The house grew up. Now the next generation gets suited too.") over the reveal clip; locked end card ("Shop The Collections / Join The Waitlist / Kids Capsule", 3-line wrap for hero size) over the finale hold, timed to start once the monogram is visibly settled (verified via frame extraction, not assumed — raw finale clip is fully risen by ~t=2.0s). Standalone tagline treatment dropped for this cut (locked CTA is the end card per line 136; tagline can return elsewhere if wanted — flagged, not silently cut).

**`ad/out/master-cold.mp4`** (11.125s, target 9-15s) — built from scratch per the cold-cut EDL (lines 140-146): opens on SIG monogram push (not the tease), hard-cut montage (BR→LH, no xfade — spec says "hard-cut" explicitly), persistent lower-third "SHOP THE COLLECTIONS" fading in ~3.0s and holding through the reveal + finale-emergence, trimmed KC reveal (3.5s) with the same locked VO caption, sped finale emergence (setpts=0.4) into a settled hold, full-screen locked CTA card over the hold. Note: spec's step-1 opener offers "LH enchanted rose OR SIG monogram push" as alternatives; picked the SIG push (a purpose-built dolly-in asset) and treated the montage's "remaining beats" as BR+LH only (not re-showing SIG) — a defensible reading, flagged as a judgment call rather than asserted as the only one.

**Verification (this session, not carried over from earlier claims):** both masters ffprobe-confirmed 720x1280@24 yuv420p h264; faststart confirmed via moov/mdat byte-offset check (warm: moov@36<mdat@7153; cold: moov@36<mdat@4113); every caption safe-band position programmatically asserted against the scaled exclusion zone (top<87px, bottom>1024px, right>627px at previz res) before render, not eyeballed; 10-frame and 6-frame spot QC grids read eyes-on across every caption beat on both cuts — locked copy verbatim, correct collection colors, no unsafe-zone intrusion, no caption-overlap collisions. v3 and v5 untouched on disk throughout (v5 kept as founder A/B alternate per team-lead direction, not conformed).

**Not done this round:** Variant E / bonus "Reveal-Into-KC" (from the killed adversarial-planning Round 1) were never checked against the LOCKED v3 tease-sync constraint — their shot lists lived only in conversation, not a file, and weren't reconstructed rather than risk asserting an unverified compliance verdict. Audio/VO recording, `1:1`/`16:9` reframes, and final-tier `-14 LUFS` mix are out of scope for this previz-tier pass.

#### Round v5 — founder-note restructure (Fable creative-director agent, FREE, 2026-07-16 ~23:45)
`ad/out/preview-flow-v5.mp4` (31.42s) + `preview-flow-v5-6s.mp4` (6.04s); v3/v4 preserved.
Changes vs v4: cold open = 2 held glimpses BR (~0.46s) + LH (~0.46s) then SIG world w/ wordmark+SIGNATURE by 1.5s; feet-tease relocated to after SIG (motion-in-context, not context-free open); reveal-flash rejected on evidence (no non-resolving frame in reveal clip — tease→reveal preserved); world order SIG→BR→LH→KC kept (LH torso-tease wears the reveal jacket = connective tissue).
Re-verified independently: ffprobe both + 8-frame eyes-on grid (`ad/work/v5/reverify/`) — glimpses land, attribution at 1.5s, reveal unspoiled at 21.5s, end card clean. Constraints hold (finale last, teases pre-reveal).
Flagged not shipped: 4+ hard-cut sub-second multi-flash open needs real playback + audio stab review, unsafe to judge from spot frames.
Report addendum §6 in `ad/out/roi-optimization-report.md`. Spend this round: 0cr.

#### DIRECTION CHANGE — garments-in-worlds (founder, 2026-07-17 ~07:45)
Founder: "we need the worlds incorporated with the clothing" — garments STAGED INSIDE world environments, NOT product-card cutaways. Card-montage branch DROPPED mid-build (fallback artifact kept: ad/work/cold-product/cold-product-base.mp4 + timeline.json, unfinished, no captions).
New pipeline: (1) FREE — 7 garment Elements from eyes-on-verified SOT product photos: sg-009 The Sherpa Jacket, sg-015 The Windbreaker Set, br-001 BLACK Rose Crewneck, br-004 BLACK Rose Hoodie, lh-004 Love Hurts Bomber Jacket (HERO — adult twin of mascot's reveal jacket), lh-002 Love Hurts Joggers, kids-001 Kids Colorblock Hoodie Set; placement plan → ad/work/garment-in-world-plan.md. (2) PAID wave A: 7 garment-in-world stills gpt_image_2 1k/low = 3.5cr — manifest SHOWN, awaiting founder y. (3) PAID wave B: animate keepers, seedance mini ~4cr each, separate gate. Fidelity gate: every generated still eyes-on vs the real product photo before animating.
Product-image constraint remains LOCKED: only the 7 verified SOT files are garment identity sources.

#### Garment media + Elements (created 2026-07-17 ~09:30, all FREE — account-durable, REUSE)
| element_id | name | media_id | product |
|---|---|---|---|
| 807cba2a-4419-4f85-b712-13511a157955 | garment-sg009-sherpa | d6c96411-1175-4065-ac72-1f26a8e39de9 | The Sherpa Jacket (SIG) |
| f01b2801-4c52-484d-8d6d-30a06280b08c | garment-sg015-windbreaker | 0e8128b7-f1d9-43c9-aca4-dec402a37b1b | The Windbreaker Set (SIG) |
| 5a66e14f-072f-4b13-997d-6cb0d177bf18 | garment-br001-crewneck | 23455e84-a3d9-4c1f-9c30-2a6b0c8bd24d | BLACK Rose Crewneck (BR) |
| 93cda914-9d34-4388-80a8-f275d805a026 | garment-br004-hoodie | b8b2f679-e69d-4294-9d1f-c30bbb996ac7 | BLACK Rose Hoodie (BR) |
| a40d0d89-4eb4-433c-8d5d-9749f69aa08c | garment-lh004-bomber | e13297dc-b980-4702-874c-14a2b02708ee | Love Hurts Bomber Jacket (LH, HERO) |
| 3284a058-2f3a-48d0-81c8-3f88514c253d | garment-lh002-joggers | 72550f71-863a-4b69-9ed6-d66ff39554df | Love Hurts Joggers (LH) |
| 5222699b-0a13-43ad-b03a-4cd68c7ea182 | garment-kids001-set | 2d750759-3a46-4071-8ecd-d66eafa6324a | Kids Colorblock Hoodie Set (KC) |
Source files = the 7 eyes-on-verified SOT product photos (see Direction Change entry). Uploads 7/7 HTTP 200, confirmed "uploaded".
Founder approval: "y+worn" — wave A (7 × gpt_image_2 1k/low = 3.5cr) cleared, WORN staging; fires when the v2 WORN prompts land in ad/work/garment-in-world-plan.md.

#### Wave A fired (2026-07-17 ~09:37) — 7 × gpt_image_2 1k/low 9:16, preflight 0.5cr exact, total 3.5cr
World-plate media_ids (new uploads, REUSE): sig-world 5cf2602c-ceee-47a8-a430-a017bb1852ae · br-world c56f21fa-230e-4097-a5e5-82ffed63097b · lh-world 6ac93d2c-07c2-43a9-9399-dfef16ebb3e8 · kc-world a13a378b-a59b-47bc-8d58-63bfc9e8a595 · dome-glass e11ac01b-4c18-4dc0-9ed2-dd0ef615cb33. Shot 1 plate = scene-1-v2 job bf444534 (image_job, reused).
| job_id | shot |
|---|---|
| b5cb2861-5d75-4931-902c-40c3629c8e6a | The Sherpa Jacket → SIG showroom |
| 04a52d89-d62d-4b8b-97f4-e7ac01a29ef3 | The Windbreaker Set → SIG terrace |
| 36bc8443-6da9-4557-9360-7c92acb3a8d3 | BLACK Rose Crewneck → BR monument |
| 1e4cc162-8d11-4cc6-a848-9d611d973b40 | BLACK Rose Hoodie → BR pillar corner |
| 52add74a-0191-434d-b24e-8ff1137daac6 | Love Hurts Bomber (HERO) → LH aisle |
| 93d4d1b1-1b81-4b2e-a70f-5ff0091eeea3 | Love Hurts Joggers → LH dome detail |
| 02b54fe8-1553-4670-978e-c8c50ae53847 | Kids Colorblock Set → KC corridor |

#### Wave A results + fidelity gate (2026-07-17 ~09:42)
All 7 completed 752x1344, downloaded to ad/garments/*-world.png. Eyes-on vs source photos (qc-pairs-a/b.jpg + z-details.jpg):
PASS (6): sg009-sherpa (fleece collar + rose embroidery confirmed), sg015-windbreaker (leg chevron + rose confirmed; slightly soft — final-tier note), br001-crewneck, br004-hoodie, lh002-joggers, kids001-set. Worlds preserved in all.
FAIL (1): lh004-bomber HERO — jacket silhouette/trim/colorblock correct but chest script ambiguous ("Huntts"-read), violates locked exact-spelling requirement. Reshoot pending founder y (0.5cr).
Spend: 3.5cr as approved (892.5 → 889 by preflight math).

#### Bomber reshoot v2 (job 9be48136-bd19-4b13-96d4-42c3fb874f29, 0.5cr, founder-approved)
`ad/garments/lh004-bomber-world-v2.png` — script letterform MATCHES the real embroidery (source's own "Hurts" is heavily stylized; v1 fail call was over-strict vs the garment's actual stitching). Remaining deviation: gen stacks "Love"/"Hurts" on one panel; real jacket splits them side-by-side across the placket. v2 = PASS-with-note; optional v3 (side-by-side placement clause) 0.5cr, founder's call. Wave A spend to date: 4.0cr (balance ~888.5).

FOUNDER ACCEPTED bomber v2 (2026-07-17 ~09:50) — full 7-shot garment-in-world set GATE-CLEAN: sg009-sherpa, sg015-windbreaker, br001-crewneck, br004-hoodie, lh004-bomber-v2 (HERO), lh002-joggers, kids001-set. Files ad/garments/*-world*.png. Wave A closed at 4.0cr.

#### master-cold-garments.mp4 built (2026-07-17 ~11:55, FREE — orchestrator-built after agent API failure)
`ad/out/master-cold-garments.mp4` — 14.83s, 720x1280@24, faststart. Cold cut + 4 garment-in-world beats (0.92s Ken Burns each, zoompan 1.0→1.07): Sherpa after SIG open, Crewneck after BR beat, Bomber-HERO + Kids Set after LH beat (both w/ lower-third CTA overlay). Product-name plates (Futura, y=852 — v1 at y=950 collided with lower-third, rebuilt). Beats DROPPED for pace (logged, not silent): windbreaker, br-hoodie, lh-joggers — stills remain available.
QC: ffprobe + 6-frame + 4-frame eyes-on grids (work/coldg/qc/) — all captions clean, no collisions, locked CTA/VO/end-card intact from base. master-cold.mp4 untouched.
Build note: zsh subscript gotcha — "$VAR[label]" in ffmpeg filter strings must be "${VAR}[label]".

#### All-options round (2026-07-17 ~15:40, FREE) + bomber-v2 verification
- Founder flagged "video didn't use V2 bomber" → pixel-diff verdict: beat frame masked-MSE 203.7 vs v2, 3367.7 vs v1 — cut DOES use v2 (v1/v2 share pose lineage; v2 fixed script only). Proof: work/coldg/qc/bomber-which.jpg.
- `out/master-cold-garments-ext.mp4` — 17.58s EXTENDED (exceeds spec 9-15s bound, flagged): all 7 garment beats (sherpa, windbreaker, crewneck, br-hoodie, lh-joggers, bomber-v2, kids), CTA on post-LH beats only.
- `out/master-warm-22s-garments.mp4` — 24.08s: bomber-v2 beat (1.2s, name plate, no CTA) inserted at 9.18s (LH→torso seam); VO/end-card shift verified.
- QC grids: work/coldg/qc/qc-variants.jpg. 4-beat master-cold-garments.mp4 remains the spec-compliant primary.
#### PENDING FOUNDER DIRECTION: KC scene → "Skyy walking down the Oakland streets" (replaces rose-gold corridor as KC world; paid manifest presented).

#### Oakland-street + wave B fired (2026-07-17 ~16:20, founder "y+mini", manifest 36.5cr, briefs = ad/work/photo-briefs.md)
| job_id | item |
|---|---|
| dd9d46a8-382b-42a0-b62f-69acb8f77f3d | 1(a) Oakland anchor still (gpt_image_2 1k/low, 0.5cr) |
| 81e502dc-f6d2-4749-8bfb-16950ac1581a | B1 sherpa micro-motion (mini 480p/4s, 4cr, preset-declined retry) |
| 5c1e2378-2862-41fa-8a43-9df522d01aad | B2 windbreaker (4cr) |
| acc7eae4-1713-4226-988f-2260e97d515b | B3 crewneck (4cr) |
| 0c518956-b700-450c-8211-97947d7ebd8c | B4 br-hoodie (4cr, preset-declined retry) |
| b96db97e-9b4b-4295-9246-de07a67e45e5 | B5 bomber HERO from v2 job 9be48136 (4cr) |
| 5c7c3dc9-e62d-4d4b-bd5a-8b51ae3f7806 | B6 joggers (4cr, preset-declined retry) |
| (pending retry) | B7 kids corridor — 429 rate_limit on first attempt, NO job created, NO charge |
1(b) walk + 1(c) push fire after anchor passes eyes-on gate. Mini preflight 4cr exact. Preset guard hit 4x (sherpa/hoodie/joggers/kids), all declined-retried per contract.
Late fires (post rate-limit + preset declines): 1(b) walk ebbfe465-ed16-4d95-ac41-9e3e3a710f8c (start=anchor dd9d46a8) · 1(c) street push ceab3992-f469-4ecb-a87e-200c5e66a4f4 (image_references=anchor) · B7 kids 5c3cdc2e-686f-4b59-92d6-e3fce353e151. Anchor still eyes-on gate PASSED (identity + script + Oakland read + roses-in-cracks) → frames/skyy-oakland-anchor.png.

#### Manifest COMPLETE (2026-07-17 ~16:45) — all 10 items landed, QC PASSED, spend reconciled
Balance 888.5 → 852 = 36.5cr EXACT (0.5 anchor + 9×4 mini clips). Files:
- frames/skyy-oakland-anchor.png (gate PASSED) · previz/street/skyy-walk-oakland.mp4 (identity holds through walk) · previz/street/oakland-street-push.mp4 (NO character bleed — image_references risk cleared)
- garments/motion/b1..b7 (all 7 micro-motion loops PASS: pose held, ambient per brief, no graphic warp)
- out/preview-oakland-street.mp4 = push→walk pair preview. QC grid work/streetqc/street-waveb-qc.jpg.
NEXT: founder verdict on street pair → swap into cuts (KC world beat → street push; reveal stays corridor OR moves to street walk — founder call), wave-B loops → upgrade Ken Burns beats to live loops in cold/warm garment cuts (free re-assembly).

#### Overwrite incident + resolution (2026-07-17 ~17:00)
Resumed ad-creative-director (stale context, pre-crash task) rebuilt and OVERWROTE out/master-cold-garments.mp4 (my 14.83s 4-beat version → its 14.625s all-7-beat version). Agent STOPPED before touching other outputs; ext + warm variants intact. Independent 6-frame verify of its cut: PASSED — all 7 garments, collection-accent name captions, CTA fade ~3s, VO+CTA coexist, end card clean, bomber v2 confirmed used. ACCEPTED as primary (superior to the overwritten build). Its planned warm variant was cancelled (already exists as master-warm-22s-garments.mp4).

#### PICTURE-LOCK CANDIDATES built (2026-07-17 ~17:20, FREE)
- `ad/out/master-cold-garments-live.mp4` — 14.75s: agent's accepted cold structure, all 7 Ken Burns beats REPLACED with wave-B live loops (sliced from t=1.2, accent-color name plates y=800 band, CTA on post-3s beats). World/reveal/finale segments untouched from accepted cut.
- `ad/out/master-warm-street.mp4` — 23.88s: warm chain rebuilt (14 segments, xfade recipe) with Oakland street push replacing kcworld (setpts 0.43), street WALK replacing corridor reveal (protected full length, VO re-timed onto it at +0.25s), live bomber beat post-LH, KIDS CAPSULE label re-timed onto street push, end card from finale+2.0s. Known previz seams: lhkc-morph arrives on street (tonally adjacent, xfade-covered) — final tier can regen a street-specific bridge if founder wants.
QC: 7-frame eyes-on grid (work/livebuild/final-qc.jpg) — all captions/beats/identity clean. Total optimization+integration spend since previz: 40.5cr paid (wave A 4.0 + manifest 36.5), balance 852.
NEXT GATES: founder picture-lock verdict → audio (create_voice preflight needed) → final tier (2k heroes ~7cr each) → reframes → ship.

### BOMBER CANON DEFECT (bug-271, 2026-07-17) — eyes-on verified
Mascot canon jacket (skyy-canonical-reference.jpeg + skyy-outfit-ref.jpeg) vs video/product bomber:
hood = rose-print WHITE (canon) vs plain black (video+SOT photo) · sleeves = clean black (canon) vs white stripe (video) · cuffs/hem = black/white rib (canon) vs red/black (video). Script split Love/Hurts MATCHES.
Root cause: Element a40d0d89 anchored to lh-004 product photo, never cross-checked vs mascot canon. Bomber spend to date: 5cr (v1 0.5 + v2 0.5 + b5 loop 4).
RULE (canon-first identity gate): reference image for any paid identity fire gets founder eyes-on approval BEFORE Element creation. Correction paths: (C) free — pull bomber beats, splice-only · (A) 0.5cr — canon still + free Ken Burns beat · (B) 4.5cr — canon still + live loop. Awaiting founder pick.

#### FOUNDER RULING (2026-07-17): lh-004 true design = MASCOT JACKET
Canon spec: rose-print WHITE hood · clean black raglan sleeves (no stripe) · black/white striped rib cuffs+hem · chrome-red "Love"/"Hurts" script split across placket · white satin body, black welt pockets, snap placket.
Consequence: SOT product photo for lh-004 is STALE for design intent (black hood, sleeve stripe, red cuffs = superseded). Catalog/SOT refresh is a separate task — ad proceeds from mascot canon.
Path A approved-in-principle: canon ref crop -> ad/work/canon/lh004-canon-ref.png (from skyy-outfit-ref.jpeg, FREE). Element + 0.5cr still await founder eyes-on of the reference (canon-first identity gate, bug-271).

#### SOT VISUAL PASS — all 33 SKU fronts (founder-ordered, 2026-07-17, 0cr)
Method: 4 labeled contact sheets (ad/work/canon/sot-audit-sheet-1..4.jpg) from data/sot-images.json fronts @ THEME_ROOT, eyes-on vs catalog name/color/garment_type_lock. NOTE: manifest paths are THEME-relative (wordpress-theme/skyyrose-flagship/), not repo-relative.
VERDICTS: 28 MATCH · 1 STALE (lh-004, founder ruling — mascot jacket is true design) · 3 SUSPECT flagged for founder:
- kids-002: name says "Purple/Black" — pixels pink/lavender/purple, ZERO black. Name colorway stale or garment revised.
- sg-003: CSV color=White — shorts read PURPLE sunset bridge-print. Color field wrong or wrong image.
- br-006 "BLACK Rose Sherpa Jacket": reads satin bomber, no visible sherpa pile (contrast sg-009 where sherpa collar is obvious). Fabric unverifiable from front alone.
Notes (no action): BR noir grade makes colorway claims unverifiable in-photo (br-010 White/Gold); br-011 type_lock=hoodie on hockey jersey = KNOWN-RESOLVED, not re-opened; lh-006 white joggers broadly consistent with mascot canon joggers; sg-002 SOT front (packshot) clean despite historical onmodel defect (bug-146).
GENERATION FREEZE holds until founder clears flags.

#### FOUNDER RULINGS on SOT pass (2026-07-17) + actions
1. br-009 white football jersey: SOT front MISSING PATCH -> render backlog (OAI2).
2. br-015 white baseball jersey: patch + lettering UNDERSIZED vs jersey series -> render backlog (OAI2).
3. kids-002: imagery is hoodie-only; SET requires jogger reference -> render backlog (OAI2 full-set packshot). Name/description still say "Purple/Black" though pixels + founder both say lavender/purple — rename PROPOSED, awaiting founder word.
4. sg-003 "golden gate shorts are purple": DONE — catalog color White->Purple (CSV, byte-safe CRLF edit).
5. br-006 renamed "The Bomber Sherpa": DONE — CSV name edit; black-rose/sot.json picked it up on regen; dossier_slug unchanged (slug != display name).
Verification: build-collection-sot.py 0 unresolved · make sot-manifest 33 skus · 50 catalog/SOT guard tests green (1 known sparse-skip). Product-render backlog is OAI gpt-image-2 ONLY (LOCKED engine rule) — NOT Higgsfield. WC store conform push deferred (WC MCP auth broken 2026-07-15).

FOUNDER RULING add (2026-07-17): sg-015 The Windbreaker Set SOT front reads SWEATSUIT, not windbreaker (catalog/branding_spec correctly say windbreaker; pixels are the defect). -> Render backlog item 4 (OAI2): re-render with nylon-shell fabric read. BLOCKER: sg-015 branding_spec = "TBD" — founder locks design/branding spec before fire. DOWNSTREAM: ad Element garment-sg015-windbreaker (f01b2801) + wave-A still + b2-windbreaker loop inherited the sweat-fabric read — b2 beat re-fire decision deferred to picture-lock.

#### DOSSIER VERIFICATION (founder-ordered Context7 pass, 2026-07-17)
Authority chain confirmed: dossier md (wordpress-theme/skyyrose-flagship/data/dossiers/{slug}.md, Corey-authored) -> skyyrose/core/dossier_loader.py (sections: Branding/Negative/Scene direction) -> dossier_schema.py (Pydantic v2). Context7 /pydantic/pydantic verdict: field_validator+classmethod ordering, multi-field args, Field(min_length) usage all match current v2 docs — no API drift.
- sg-015 UNBLOCKED: the-windbreaker-set.md is COMPLETE (nylon lock, white+pink hood+4-color chevron, techflat ref, "NO cotton-fleece" negative). CSV branding_spec "TBD" is stale metadata, dossier is authority. Current SOT front violates the dossier's own negative -> render backlog item 4 ready to fire on founder y.
- br-006 duplicate dossier RESOLVED: dossier_slug repointed black-rose-sherpa-jacket -> black-rose-bomber-sherpa (richer, real ref photos, storm-flap spec); superseded duplicate DELETED same change (census-clean). render_output_slug untouched (render dirs live under old name).
- OPEN for founder: display name "The Bomber Sherpa" (CSV, per your words) vs "The Black Rose Bomber Sherpa" (dossier) — pick one; sg-015 dossier CATALOG NOTE says CSV color=Black but CSV=White (stale note, Corey-authored file so left alone).
- Validator gap: dossiers/CLAUDE.local.md (claude-mem stub) is the 1 "FAILED" in validate_dossier.py — glob should exclude non-dossier files.
Proof: validate_dossier 35/36 (fail=stub only) · lint clean on both key dossiers · pytest dossier schema+completeness+catalog integrity 107 passed 0 failed.
FOUNDER (2026-07-18): br-006 display name FINAL = 'The Black Rose Bomber Sherpa' (dossier name adopted; CSV aligned).
FOUNDER (2026-07-18): deterministic hex backfill APPROVED + committed — 100 regions, 26 dossiers, coverage 0->31%. Ambiguous 154 regions = Corey judgment tier, open.

#### PRIORITY-LIST EXECUTION (2026-07-18)
DONE (free): kids-002 rename Purple/Black -> Lavender/Purple (commit 404ec4826).
BATCH 1 (OAI render fixes) — BLOCKED, cannot fire from this worktree:
- No .env/.env.secrets in sparse worktree -> OPENAI_API_KEY absent (renders run from main checkout only).
- br-009: OAI pipeline REFUSES (patchless-jersey guard) — missing ref asset assets/products/techflats/hero-overlays/br-patch-nfl-football.png. The missing patch IS the defect root.
- br-015: same refusal — missing assets/products/techflats/hero-overlays/br-patch-mlb-baseball.png.
- kids-002 full-set: joggers SKIP — no usable jogger garment reference (front techflat exists, flatlay=None).
- sg-015: READY (2 imgs, ~$0.80 @ $0.40/img floor) — dossier complete, refs present; only item unblocked, still needs key + STOP-AND-SHOW.
  ACTION: create the 3 missing reference assets (2 sport-patch PNGs + 1 jogger flatlay) in main checkout, then render batch there. Not doable here.
BATCH 2 (bomber path A) — FREE PREP DONE, awaiting founder y for the 0.5cr fire:
- New canon Element garment-lh004-bomber-canon = 2d708bf2-7369-477f-908c-bd19fcc17f9e (media f6cb4712-bf82-4219-9b43-77bd43ca5f69, from ad/work/canon/lh004-canon-ref.png). Supersedes a40d0d89 (stale SOT).
- get_cost preflight: gpt_image_2 1k/low/9:16 = 0.5cr EXACT. Balance 852.

#### BATCH 1 UNBLOCKED (2026-07-18) — was sparse-exclusion, not missing assets
Root correction: br-patch-nfl-football.png / br-patch-mlb-baseball.png / kids-purple-joggers-front.jpeg all EXIST in main — the sparse worktree excluded them. `git sparse-checkout add assets/products/techflats assets/products/references` materialized them (tracked files, reversible). OPENAI_API_KEY loaded from /Users/theceo/DevSkyy/.env.hf into render shell (value never printed, sk- prefix validated). REPO_ROOT = worktree, so renders use THIS branch's corrected dossiers (sg-015 nylon lock, hex backfill).
Dry-run (assets+key present) — ALL 4 renderable, 11 images:
  br-009 ghost+ghost-back+on-model (4 refs) · br-015 same (4 refs) · kids-002 ghost+ghost-back+on-model-paired (3 refs) · sg-015 ghost+on-model (2 refs).
Est ~$4.40 floor (@ $0.40/img); SpendTracker hard-caps actual at $50 (incl QC re-renders/judge).
INPUT fidelity gate PASSED eyes-on: 2 authentic sport patches clean; jogger = deep-purple + rose; sg-015 techflat = correct nylon windbreaker (white body/pink hood/pastel chevron/SR back). OUTPUT gate = post-render vision QC before any site touch.
STOP-AND-SHOW pending founder y (dollars). Bomber 0.5cr (credits) still pending separately.

#### BATCH 1 FIRING (2026-07-18, founder-approved "Batch 1")
Env setup (founder-authorized "import all keys"): sparse-checkout add assets/products (full tree, for correct manifest + refs); gemini/.env created with OPENAI_API_KEY (from .env.hf) + ANTHROPIC_API_KEY (founder ran the `!` append) — both gitignored, pipeline load_env picks them up. NOTE: first fire crashed at QCGate init (ANTHROPIC absent) BEFORE any spend — 0 render events.
Run run-20260718-060212.jsonl: 11 plans (br-009 ×3, br-015 ×3, kids-002 ×3, sg-015 ×2), est $4.40, cap $50, judge claude-sonnet-4-6. Background id b34we6sy0.
POST-RENDER: vision-QC every output vs dossier before any site touch (wrong-garment gate). Then present results.

#### BATCH 1 RESULT + EYES-ON QC (2026-07-18) — all 4 defects FIXED
Spend: $4.40 actual (11 imgs × ~$0.40, 0 re-renders). Higgsfield balance untouched (852). Images landed in renders/oai/_rejected/<slug>/ because the Claude QC judge ERRORED on all 11 ("Your credit balance is too low" — the ANTHROPIC judge account is out of credits, NOT a quality rejection). Manual vision QC done instead:
- br-009 (was: missing patch): NFL AUTHENTIC gold patch now present at hem (ghost+back+on-model). PASS.
- br-015 (was: patch/lettering too small): MLB gold patch present, "BLACK IS BEAUTIFUL" arched lettering substantial. PASS — recommend side-by-side vs br-003/br-014 to confirm "matches other baseball jerseys" scale.
- kids-002 (was: joggers missing): FULL SET rendered — lavender/light-pink+purple colorblock hoodie + deep-purple joggers w/ rose emblem, paired on-model. PASS.
- sg-015 (was: reads sweatsuit): now reads NYLON windbreaker (sheen/structure), white body/pink hood/pastel chevron/zip, matches techflat. PASS.
No wrong-garment defects. Images are CANDIDATES in _rejected/ — promotion to keepers + SOT/catalog wiring + deploy = separate founder-gated step (production).
FOLLOW-UP: Anthropic judge account (key in .env.judge-opus-thinking) out of credits — top up for future auto-QC, else pipeline QC always errors→needs-review.

#### BATCH 1 RE-RENDER FIRING (2026-07-18, founder y) — judge restored
Run: 6 plans (br-009 ghost/ghost-back/on-model + br-015 same), judge claude-sonnet-4-6 ACTIVE (founder topped up Anthropic acct). est ~$2.40, cap $50. bg id buw1pbphj.
Fixes in this pass: br-009 back "32" rose-in-2-only + white/black-border letters + sleeves full-"32"-with-rose (not split); br-015 bigger front lettering + real product photo as ground-truth ref. Dossier fixes committed 727236286; playbook committed 50e53b170.
POST: eyes-on QC all 6 vs corrected dossiers; with judge back, expect renders in renders/oai/<slug>/ (not _rejected).

#### BATCH 1 RE-RENDER RESULT + QC (2026-07-18) — $2.40, judge STILL down
Judge STILL errors "credit balance too low" — founder's top-up didn't reach THIS judge key's Anthropic account (.env.judge-opus-thinking). All 6 -> _rejected, manual QC:
- br-009 back "BLACK IS BEAUTIFUL": WHITE letters + black border. ✓ FIXED.
- br-009 sleeves: full "32" on each sleeve WITH rose fill (no longer split). ✓ FIXED.
- br-009 back "32" rose-in-"2"-only: ✗ NOT FIXED — model still put rose in BOTH back digits; couldn't isolate one digit. Needs another attempt or founder accept.
- br-015 front lettering: bigger than v1 ✓, but may not match the real photo's bold/wide scale — founder to judge.
Session OpenAI spend: $4.40 (batch1) + $2.40 (re-render) = $6.80. Higgsfield 852 untouched.

#### QC CORRECTION (2026-07-18): br-009 v2 back "3" WAS fixed — my error
Full-res crop (br009-back-32-zoom.png) proves the center back "3" is PLAIN WHITE + black outline, rose in the "2" ONLY. My earlier "NOT FIXED — both digits rose" verdict was a MISREAD on the downscaled contact sheet (520px cells lose plain-vs-rose distinction at digit scale). ALL 3 br-009 fixes landed: white/black-border back letters ✓, rose-in-2-only ✓, full-"32"-rose sleeves ✓. The $2.40 re-render was fully successful. NO further fix/spend needed. Masked-inpaint research (gpt-image-2 images.edit + mask, pipeline supports client.edit(mask_path)) documented for future selective-edit needs but NOT required here.
