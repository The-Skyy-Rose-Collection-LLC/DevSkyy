# SkyyRose Collections Ad + Scroll-World — Build Research Report
*Generated 2026-07-16 · 4 parallel research agents · WebSearch + WebFetch · Confidence: Medium-High (most AI-video sources are vendor/SEO blogs — cross-referenced + flagged where single-source)*

## Executive summary
Research to execute the SkyyRose collections ad + scroll-world flawlessly, before ~150 credits of paid generation. Four findings change the plan materially:
1. **Don't fully AI-generate the mascot — composite the 3D rig we already own for hero shots.** Full in-video AI gen still drifts faces/outfits; not reliable at zero-defect brand tolerance.
2. **`generate_audio` (Higgsfield) is text-to-speech only** — it can't make the cinematic sound design the brief assumed. Corrected paths below.
3. **Don't free-morph one world into the next, and don't scroll-scrub the monogram-from-concrete finale.** Use disguised "portal" transitions; play the finale forward-only/pinned.
4. **The ad's objective (cold-prospecting vs brand-awareness/warm) decides the whole structure.** As a cold-prospecting cut, the current backloaded, caption-less, empty-open design is under-supported by the data. As a warm/brand-launch piece it's defensible with caption discipline + earlier brand resolution. **This is the one decision that gates everything.**

---

## 1. Mascot / character consistency in AI video
**Verdict: composite the rig for hero shots; AI-generate only low-stakes walk-ins/background.**
- Full in-video AI generation of a character across models in 2026 is better than a year ago (Higgsfield **Soul ID** + **Elements** genuinely cut drift) but **not zero-defect reliable** for a hero cinematic spot — faces/outfits measurably drift, especially on close-ups and past ~4–8s. ([Higgsfield Soul ID](https://higgsfield.ai/blog/sould-id-best-character-consistency), [DEV.to](https://dev.to/andrew_klubnikin_609150ae/ai-videos-character-consistency-problem-how-to-fix-it-3amj), [Kittl](https://www.kittl.com/blogs/ai-video-character-consistency-workflow/))
- **Dominant pro workflow:** generate a locked hero still → image-to-video from it (not text-to-video) → keep the character "asset prompt" identical, vary only the shot prompt → short clips (4–8s), cut between them. ([Hailuo mascot workflow](https://hailuoai.video/pages/knowledge/animating-brand-mascots-ai-consistency-workflow), [Kittl](https://www.kittl.com/blogs/ai-video-character-consistency-workflow/))
- **Higgsfield tools we have** map directly: `show_reference_elements` (Elements = `@skyy` reusable identity lock), `show_characters` (Cast sheets), Soul ID (trained identity, needs 20+ photos, ~25 cr). Soul ID works across seedance/kling/veo once trained. ([Higgsfield Elements doc](https://github.com/Abteeeen/higgsfield-prompting-skill/blob/main/elements_and_consistency.md))
- **Composite-the-rig wins** exactly when the character IS the brand IP and a wrong face/garment is unacceptable (SkyyRose's #1 recurring defect) AND a rigged asset already exists (the GLB). Trade-off: matching light/shadow/parallax between a 3D render and an AI plate takes real compositing or the seam shows. ([Krikey](https://www.krikey.ai/create/character-rigging))

**Actionable:** register `skyy-canonical-v2.png` as Element `@skyy` + lock outfit as a separate `@skyy-outfit`; render ~20 GLB angles (free) to unlock Soul ID (~$1.25, gated); first-frame-condition every shot; **composite the rigged GLB for the full-body reveal + hero close-ups**; reserve pure AI gen for feet/silhouette/background walk-ins.

## 2. Seamless camera flights + morph VFX
**Verdict: disguised "portal" transitions, not free morphs; finale plays forward-only.**
- Both `seedance_2_0` and `kling3_0` accept `start_image` + `end_image` (confirmed via MCP `models_explore`, not just blogs).
- **Free-morphing disparate worlds is a documented failure mode** — Kling's docs: "wildly different [start/end frames] in color, style, or lighting… can break the transition." ([Higgsfield Kling S/E frames](https://higgsfield.ai/blog/Kling-Start-End-Frames), [ImagineArt](https://www.imagine.art/blogs/kling-2-1-start-end-frame-overview))
- **The fix is match-cut logic wearing a camera move**: a physical connective device carries the camera through the seam (push through an archway/doorway, plunge into fog/petals, whip past an object). Grounded in film match-cut literature, not vendor morph-marketing. ([StudioBinder match cuts](https://www.studiobinder.com/blog/match-cuts-creative-transitions-examples/), [MindStudio](https://www.mindstudio.ai/blog/ai-video-transitions-locations-runway-seedance))
- **Prompt each clip as one continuous take**: name the exact camera verb across the whole duration, state "single continuous shot, no cuts," state what the camera does NOT do; negative tokens `jump cut, hard cut, strobing` at seams. ([Higgsfield Seedance guide](https://higgsfield.ai/blog/seedance-prompting-guide))
- **Monogram-from-concrete = "Lock, Move, Land"**: start image = emblem flush in cracked concrete; end image = risen dimensional rose-gold monogram; the rose-gold **particle-convergence** pattern is explicitly luxury-suited. ([LightX logo prompts](https://www.lightxeditor.com/blog/logo-animation-video-prompts/))
- **Scroll-scrub caveat (critical):** pure camera moves scrub safely both directions, but **irreversible-formation physics** (cracks/rise/dust) un-forms when scrubbed backward → the monogram-from-concrete shot must NOT be bound to scroll; play it forward-only/pinned on arrival.

## 3. Scroll-scrub encoding + audio/voice
**Scroll-scrub encode (the leg recipe):**
- **Keyframe interval `-g 8` / `keyint=8` + `scenecut=0`** (dense, NOT the 2s streaming GOP — practitioners: every 5–10 frames smooth, 100 choppy). ([Muffin Man](https://muffinman.io/blog/scrubbing-videos-using-javascript/), [Chris How](https://medium.com/@chrislhow/scroll-to-scrub-videos-4664c29b4404))
- **Ship dual container** — H.264 MP4 (Safari) + VP9 WebM (Firefox needs it; "MP4 choppy even with keyframes"). **`+faststart` mandatory** or first-load scrub stalls. ([Muffin Man](https://muffinman.io/blog/scrubbing-videos-using-javascript/))
- **`fetch()`→Blob→createObjectURL** before enabling scroll (the `preload` attr is only a hint); clamp progress to ~0.998; `muted playsinline` + explicit `poster`; ship a `prefers-reduced-motion` branch; **test iOS single-active-decoder** limit on real hardware. My engine already does blob-load, 0.999 clamp, reduced-motion, poster, playsinline — so this is mostly the encode recipe + iOS test.
**Audio (corrects the brief):**
- **`generate_audio` is TTS only** — its own description forbids general music/SFX. Real paths: (1) generate the ad on a **native-audio video model (WAN 2.5 class)** so ambient/sound bakes in, or (2) **licensed SFX library + mix in post** (Apple "Sound" campaign = scored from product sounds — the on-brand precedent). ([Boom Box Post — risers/stingers/hits](https://www.boomboxpost.com/blog/2021/1/8/creating-risers-stingers-and-hits))
- **`create_voice` is correct** for the mascot voice; keep takes <5 min (drift), reuse one `voice_id`, budget ~2–3× credits for retakes. Mix **-14 LUFS / -1 dBTP** (cross-platform safe; IG/TikTok "official" LUFS numbers are guesses). ([Dan Murtagh LUFS](https://danmurtagh.com/lufs-loudness-standards))
- Sound-design-only is legit for premium/product ads, but forgoes the recall lift of a fit sonic mnemonic — a deliberate trade.

## 4. Luxury paid-social ad best practices
**Verdict: the concept is defensible as a WARM/brand-launch piece with caption discipline + earlier brand resolution; it's under-supported as a COLD-prospecting ROAS cut. Decide the objective.**
- **Hook (muted, 3s):** empty architectural establishing shot is the **weakest** frame-1 choice. Open on the mascot in motion + face/eye-contact + product-on-body. ([303.London luxury TikTok](https://www.303.london/blog/the-tiktok-creative-system-for-luxury-fashion-brands-summer-2026-edition), [Madgicx](https://madgicx.com/blog/clothing-ad))
- **Muted-first: ~70–85% watch muted → burned-in styled captions are non-negotiable** (+56% comprehension, +16% recall), placed in the center safe band (avoid top ~130px / bottom ~20% / right ~140px UI zones). ([Sharethrough](https://www.sharethrough.com/blog/infographic-research-reveals-growth-in-muted-videos-need-for-captions-across-all-screens), [House of Marketers safe zones](https://houseofmarketers.com/guide-to-safe-zones-tiktok-facebook-instagram-stories-reels/))
- **Length:** ~22s sits inside both platforms' sweet spots (Meta 21–24s, TikTok 21–34s) — length isn't the problem, but ~45–55% completion means the finale-only offer misses ~half. Move a brand/shop cue to ~sec 8–10; hook in first 6s (TikTok: 90% of ad recall lands in first 6s). ([TikTok creative best practices](https://ads.tiktok.com/help/article/creative-best-practices))
- **Progressive reveal** works for serialized microdrama (episode-2 pull), NOT a standalone 22s spot. Resolve brand identity EARLY; reserve suspense for the *specific news* (rebrand + Kids Capsule), not "what is this brand."
- **CTA split by product state:** "Shop the Collections" for live Signature/Black Rose/Love Hurts; **"Join the Waitlist" for Kids Capsule** (launch-mode, not buyable — verify SKUs before any shop CTA). ([Blazon waitlist strategy](https://blazonagency.com/post/waitlist-strategy))
- **Keep the mascot** — character brand assets outscore logos on effectiveness (System1/WARC: characters 105 vs logos 82), but she must do hook work in frame 1, not only appear in the tour. ([WARC brand characters](https://srh.agency/wp-content/uploads/2025/02/Brand-characters-boost-the-effectiveness-of-TV-ads-_-WARC.pdf))
- **Cut two versions:** the 22s cinematic cut → warm/retargeting, measured on recall/brand-lift; a 9–15s product-forward cut → cold prospecting, CTA in first half.

---

## Key takeaways (the plan changes)
1. **Mascot hero shots = composite the rigged GLB** (own it, zero-defect). AI-gen only low-stakes walk-ins. Register `@skyy` Element.
2. **Transitions = disguised portals** (camera through archway/fog/flare), never free-morphs.
3. **Monogram-from-concrete = forward-only/pinned**, out of the scroll-scrub timeline.
4. **Audio = `create_voice` for the voice + (WAN-native-audio OR licensed-SFX+post) for sound design** — NOT `generate_audio`. Captions burned-in regardless. Mix -14 LUFS.
5. **Open on the mascot+face in motion**, caption the whole thing, surface a brand/shop cue by ~sec 8, split the CTA (Shop live / Waitlist KC).
6. **Two cuts** (22s warm-cinematic + short cold-prospecting), and **decide the objective** — it defines "done."
7. **Scroll-scrub legs encode:** `-g 8 scenecut=0`, dual MP4+WebM, `+faststart`; test iOS single-decoder.
8. **Verify Kids Capsule has buyable SKUs** (it's launch-mode/0-cards by design) before any shop CTA.

## Methodology
4 parallel agents (WebSearch + WebFetch), ~110 sources, sub-questions: (1) AI-video character consistency, (2) seamless camera chaining + emergence VFX, (3) scroll-scrub encoding + AI audio/voice, (4) luxury paid-social best practices. Most AI-video sources are vendor/SEO blogs → cross-referenced across ≥2 where possible; single-source and vendor-motivated claims flagged inline. Firecrawl/exa not yet loaded this session (WebSearch/WebFetch used); can re-crawl for depth after restart.
