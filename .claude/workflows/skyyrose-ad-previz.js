export const meta = {
  name: 'skyyrose-ad-previz',
  description: 'Phase-gated previz-first pipeline for the SkyyRose collections ad — paid phases refuse to run without a founder-approved manifest (content-verified, cost-capped)',
  whenToUse: 'Invoke with args {phase:"prep"} (free) first. Paid phases {phase:"bridges"|"previz"|"final"} require args.approved="y" AND args.manifest = the EXACT object prep returned (items + signature + capCr) after founder STOP-AND-SHOW. {phase:"assemble"} is free.',
  phases: [
    { title: 'Prep', detail: 'free: crop start/end frames + author both paid manifests' },
    { title: 'Bridges', detail: 'PAID+gated: generate bridge/anchor stills' },
    { title: 'Previz', detail: 'PAID+gated: fast-tier clips (morphs + world beats + tease)' },
    { title: 'Assemble', detail: 'free: ffmpeg rough cut, 22s warm + 9-15s cold' },
    { title: 'Final', detail: 'PAID+gated: re-render founder-marked keepers at final tier' },
  ],
}

// ---------------------------------------------------------------------------
// SkyyRose collections ad — previz-first production pipeline (v3 spec locked)
const ROOT = '/Users/theceo/DevSkyy/.claude/worktrees/collections-scroll-world'
const SPEC = ROOT + '/tasks/scroll-world-ad-spec.md'          // v1+v2+LOCKED v3 + assembly recipe/EDL
const RESEARCH = ROOT + '/tasks/ad-build-research.md'         // 4-agent cited research
const STILLS = '/Users/theceo/DevSkyy/renders/scroll-world'   // 5 source stills (2048x1360)
const WORKDIR = '/Users/theceo/DevSkyy/renders/scroll-world/ad' // durable working tree
// Output path convention (all phases MUST follow it so manifests can reference
// assets that don't exist yet): frames -> WORKDIR/frames/<name>.png,
// bridges -> WORKDIR/bridges/<id>.png, previz clips -> WORKDIR/previz/<id>.mp4,
// final renders -> WORKDIR/final/<id>.<ext>, cuts -> WORKDIR/out/.
//
// LOCKED v3 (do not re-litigate inside agents): mascot = the CHILD in scene-4;
// hook = feet-up tease (feet->knees->torso across SIG/BR/LH, face reveal at KC);
// KC reveal = child turns to camera + line "The house grew up. Now the next
// generation gets suited too."; finale = cement-cracking start-plate -> SR
// monogram rises (forward-only); morphs are ANCHORED (rose BR->LH is the
// linchpin and needs NO bridge; SIG->BR, LH->KC, KC->finale use bridge stills);
// audio = create_voice + licensed SFX/WAN-native (NOT generate_audio); captions
// burned-in; CTA split Shop-live / Waitlist-KC; two cuts (22s warm + 9-15s cold).
// ---------------------------------------------------------------------------

// args can arrive JSON-encoded as a string (harness serialization); parse defensively —
// otherwise args.phase is undefined and a PAID invocation silently falls back to 'prep'.
const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const phaseArg = A.phase || 'prep'
const PAID = { bridges: 'Bridges', previz: 'Previz', final: 'Final' }
// Signature binds the FULL approved content of every item (id + prompt + cost
// bounds + model/tier), not just the id set — an id-only signature would pass a
// manifest whose prompts or estimates were mutated after the founder's "y".
const sig = items => JSON.stringify(
  [...items].sort((a, b) => (a.id < b.id ? -1 : 1)).map(i => ({
    id: i.id, prompt: i.prompt, estCrLow: i.estCrLow, estCrHigh: i.estCrHigh,
    model: i.model ?? null, resolution: i.resolution ?? null, kind: i.kind ?? null,
  }))
)

// HARD GATE — content-verified, cost-capped. The main thread presents prep's
// manifest (items + signature + capCr + live cost preflight) as STOP-AND-SHOW,
// gets an explicit founder "y", then re-invokes passing that object VERBATIM:
//   args = { phase, approved:'y', manifest:{ items:[...], signature, capCr } }
if (PAID[phaseArg]) {
  const m = A.approved === 'y' && A.manifest
  if (!m || !Array.isArray(m.items) || m.items.length === 0) {
    throw new Error(`Phase "${phaseArg}" is PAID and gated: missing args.approved="y" + args.manifest.items[]. Run {phase:"prep"} first.`)
  }
  // (1) Every item must be fully specified — no fail-open cost checks (bug-230).
  for (const it of m.items) {
    if (!it.id || !it.prompt || typeof it.estCrHigh !== 'number' || typeof it.estCrLow !== 'number') {
      throw new Error(`Gated manifest item ${JSON.stringify(it.id || it)} lacks id/prompt/estCrLow/estCrHigh — refuse to fire.`)
    }
    // id becomes an output filename segment — allowlist it so a hostile/typo'd
    // manifest can't traverse paths or smuggle prompt-shaped text into the task.
    if (!/^[a-z0-9][a-z0-9-]{0,63}$/.test(it.id)) {
      throw new Error(`Manifest item id ${JSON.stringify(it.id)} fails the [a-z0-9-] allowlist — refuse to fire.`)
    }
  }
  // (2) Integrity: the passed list must match its own signature (catches
  // accidental mutation/expansion between STOP-AND-SHOW and invocation).
  if (m.signature !== sig(m.items)) {
    throw new Error(`Manifest signature mismatch (expected ${sig(m.items)}) — the item list is not the one that was approved. Refuse to fire.`)
  }
  // (3) Cost ceiling: the summed high estimate must fit the approved cap.
  const totalHigh = m.items.reduce((s, i) => s + i.estCrHigh, 0)
  if (typeof m.capCr !== 'number' || totalHigh > m.capCr) {
    throw new Error(`Cost gate: sum(estCrHigh)=${totalHigh}cr exceeds approved capCr=${m.capCr} — refuse to fire.`)
  }
}

const CTX = `DOC VERIFICATION (Context7-first, founder-mandated): BEFORE composing or firing ANY generation call, verify parameters against current docs — (a) Context7: resolve-library-id "Higgsfield" then query-docs /llmstxt/higgsfield_ai_llms_txt for platform/API behavior; (b) models_explore(<model id>) for the LIVE MCP param schema (authoritative for tool params); (c) get_cost:true preflight before every fire. VERIFIED 2026-07-16: seedance_2_0_mini REQUIRES explicit resolution:"480p" (omitting it quotes 10cr; 480p/4s = 4cr exact); media roles = start_image/end_image/image_references; generate_audio:false; duration clamps to 4s minimum; gpt_image_2 accepts only media role "image", 1k/low = 0.5cr; a preset_recommendation notice means NO job was created — retry the SAME call once with declined_preset_id (tool contract, not a reroll).
IDENTITY CANON (bug-268, founder-mandated): character/mascot identity references resolve ONLY from assets/branding/mascot/ (skyy-canonical-reference.jpeg = the canonical stylized-toon Skyy) — NEVER from a generated render (scene-4's child is off-canon). Identity mismatches BLOCK generation; multi-beat character continuity = ONE generation sliced in edit, never independent generations. MANDATORY: the character matches the canonical picture; all 4 collections (SIG/BR/LH/KC) featured.
Context files (READ FIRST): spec ${SPEC} (the "LOCKED v3" block + "PREVIZ ASSEMBLY RECIPE + COLD-CUT EDL" section govern), research ${RESEARCH}. Source stills in ${STILLS}: scene-1-signature-monogram.png (gold SR monogram statue, Oakland showroom), scene-2-blackrose-silverstar.png (silver star + engraved black rose, gothic rooftop), scene-3-lovehurts-enchantedrose.png (red rose under glass dome, crimson cathedral), scene-4-kids-mascot.png (THE CHILD MASCOT walking a rose-gold corridor), scene-5-finale.png (OLD cloaked placeholder — do NOT use as finale content). Working tree: ${WORKDIR}; path convention: frames/ bridges/ previz/ final/ out/ subdirs, filenames = the item/crop id. Never fire a paid API call outside the exact manifest you were handed.`

// ---------------------------------------------------------------------------
if (phaseArg === 'prep') {
  phase('Prep')
  const ITEM_SCHEMA = {
    type: 'object', additionalProperties: false,
    properties: {
      items: { type: 'array', items: { type: 'object', additionalProperties: true,
        properties: {
          id: { type: 'string' }, prompt: { type: 'string' },
          estCrLow: { type: 'number' }, estCrHigh: { type: 'number' },
        }, required: ['id', 'prompt', 'estCrLow', 'estCrHigh'] } },
      totalEstCr: { type: 'string' },
      notes: { type: 'string' },
    }, required: ['items', 'totalEstCr'],
  }
  const [crops, bridgeManifest, clipManifest] = await parallel([
    () => agent(
      `${CTX}
TASK (free, mechanical): produce the start/end reference CROPS for the previz morphs and tease shots, into ${WORKDIR}/frames/ via Python PIL or ffmpeg (bash). Crops (from the 2048x1360 stills; generous margins, PNG, name EXACTLY):
 1. rose-black.png       — scene-2 tight on the engraved black rose bloom
 2. rose-red-dome.png    — scene-3 tight on the red rose under its glass dome
 3. monogram-gold.png    — scene-1 tight on the gold SR monogram statue
 4. star-point.png       — scene-2 tight on the silver star's top point
 5. dome-glass.png       — scene-3 tight on the glass dome (push-through point)
 6. kc-arch-bg.png       — scene-4 background arch/corridor WITHOUT the child (crop above/behind her)
 7. kc-lightbeam.png     — scene-4 tight on a rose-gold ceiling/arch light beam
 8. mascot-full.png      — scene-4 full frame (identity reference for the KC reveal)
 9. mascot-feet.png      — scene-4 cropped to feet/sneakers only
10. mascot-knees.png     — scene-4 cropped feet-to-knees
11. mascot-torso.png     — scene-4 cropped shoulders-down (NO face)
Eyes-on verify each crop by reading the output image ONCE (batch your reads); confirm subject centered + un-clipped. Return JSON: {crops:[{name, path, ok, note}]}.`,
      { label: 'prep:crops', phase: 'Prep', effort: 'low' }
    ),
    () => agent(
      `${CTX}
TASK (free, authoring only — NO generation): write the BRIDGE-STILLS manifest, the exact gpt_image_2 batch the founder will approve. Previz tier = 1k/low (~0.5cr class) unless noted. Output paths are FIXED: ${WORKDIR}/bridges/<id>.png. Items:
 a. sig-br-flare        — abstract radial light-streak, warm gold center -> cool silver-blue edges, no objects
 b. lh-kc-petal         — single red petal falling in darkness, close-up
 c. lh-kc-arch-ignite   — rose-gold light-flare shaped as an igniting archway (match scene-4's real arch; ref kc-arch-bg.png)
 d. finale-concrete     — THE CEMENT-CRACKING START-PLATE (founder-directed): SR monogram flush/engraved in cracking Oakland concrete pavement, unlit, hairline cracks radiating, dust; gothic-noir photoreal grade matching the existing stills; ref monogram-gold.png for the letterforms. List BOTH tier options (1k/low previz + 2k/high hero) as separate estCr notes — the manifest fires previz tier; the hero re-render happens in phase "final".
 e. finale-risen        — gold SR monogram fully risen, dimensional, rose-gold light, particles settling (end-plate). NOTE: if the monogram-gold.png crop alone can serve as the end frame, say so and mark this item optional-skip.
DO NOT include a BR->LH bridge — LOCKED v3: the rose morph is direct (rose-black.png -> rose-red-dome.png), no bridge. (Contingency only: if the linchpin morph fails at previz review, a rose-mid-transform bridge may be added to a NEW manifest then.)
For each item: {id, prompt (full text, style preamble consistent with existing stills), aspect_ratio, resolution, quality, refImages (exact paths), estCrLow (number), estCrHigh (number), note}. Return JSON {items:[...], totalEstCr:"low-high", notes}.`,
      { label: 'prep:bridge-manifest', phase: 'Prep', schema: ITEM_SCHEMA }
    ),
    () => agent(
      `${CTX}
TASK (free, authoring only — NO generation): write the PREVIZ-CLIPS manifest (seedance_2_0 mode=fast, 9:16, ~2-4s each). All start/end frames are pre-defined crops (${WORKDIR}/frames/) or bridges (${WORKDIR}/bridges/) so the WHOLE batch is parallelizable. Items:
 1. clip-sig            — world beat: glide toward monogram (start: ${STILLS}/scene-1-signature-monogram.png)
 2. clip-tease-feet     — tease: feet stride into frame (start: frames/mascot-feet.png; NO face; drift-tolerant)
 3. clip-br             — world beat: orbit-in to black rose (start: ${STILLS}/scene-2-blackrose-silverstar.png)
 4. clip-tease-knees    — tease: knees-down walking (start: frames/mascot-knees.png)
 5. clip-morph-rose     — THE LINCHPIN: frames/rose-black.png -> frames/rose-red-dome.png anchored morph (petals bleed black->red; NO bridge)
 6. clip-lh             — world beat: push down cathedral aisle (start: ${STILLS}/scene-3-lovehurts-enchantedrose.png)
 7. clip-tease-torso    — tease: torso, face withheld (start: frames/mascot-torso.png)
 8. clip-morph-sig-br   — frames/monogram-gold.png -> bridges/sig-br-flare.png -> frames/star-point.png portal (two-hop or single gen with the flare as mid-reference — author's choice, justify)
 9. clip-morph-lh-kc    — frames/dome-glass.png -> frames/kc-arch-bg.png via bridges/lh-kc-petal.png + bridges/lh-kc-arch-ignite.png
10. clip-kc-reveal      — the child completes her walk, turns to camera (start: ${STILLS}/scene-4-kids-mascot.png). IDENTITY LOCK: pass frames/mascot-full.png via seedance's image_references role in the SAME generation (the model supports reference images alongside start_image) so her face/outfit anchor to the canonical child. Flag identity risk in riskNote.
11. clip-morph-kc-fin   — frames/kc-lightbeam.png -> bridges/finale-concrete.png (the beam narrows to darkness, landing on the cracked pavement — hands off to clip-finale)
12. clip-finale         — bridges/finale-concrete.png -> bridges/finale-risen.png (or frames/monogram-gold.png if finale-risen was marked optional-skip): cracks spread, monogram rises, camera LOCKED (forward-only)
For each: {id, model:"seedance_2_0", mode:"fast", aspect:"9:16", durationSec, startImage (exact path), endImage (exact path or null), imageReferences (paths or []), prompt (full text: single-continuous-take language, camera verb, negatives "jump cut, hard cut, strobing"), estCrLow (number), estCrHigh (number), riskNote}. Return JSON {items:[...], totalEstCr:"low-high", notes:"note that clip-morph-rose (the linchpin) can fire FIRST alone as a single-item manifest if the founder wants a one-clip proof before the batch"}.`,
      { label: 'prep:clip-manifest', phase: 'Prep', schema: ITEM_SCHEMA }
    ),
  ])
  const withSig = m => m && m.items ? { ...m, signature: sig(m.items), capCr: Math.ceil(m.items.reduce((s, i) => s + i.estCrHigh, 0)) } : m
  return {
    crops,
    bridgeManifest: withSig(bridgeManifest),
    clipManifest: withSig(clipManifest),
    next: 'Present both manifests (run live get_cost preflights first) as STOP-AND-SHOW. On founder "y": invoke {phase:"bridges", approved:"y", manifest:<bridgeManifest verbatim>} then {phase:"previz", approved:"y", manifest:<clipManifest verbatim>}. For a linchpin-first proof, pass a single-item manifest {items:[clip-morph-rose], signature:"clip-morph-rose", capCr:<its estCrHigh>}.',
  }
}

// ---------------------------------------------------------------------------
if (phaseArg === 'bridges' || phaseArg === 'previz' || phaseArg === 'final') {
  phase(PAID[phaseArg])
  const items = A.manifest.items
  const EXEC_SCHEMA = {
    type: 'object', additionalProperties: false,
    properties: {
      id: { type: 'string' }, ok: { type: 'boolean' },
      path: { type: 'string' }, actualCr: { type: 'number' },
      durationSec: { type: 'number' }, note: { type: 'string' },
    }, required: ['id', 'ok', 'actualCr', 'note'],
  }
  const results = await parallel(items.map(item => () => {
    // Per-item media kind: manifests may mix stills + clips (e.g. a final-tier
    // hero re-render of the finale-concrete STILL). Default by phase.
    const isVideo = (item.kind || (phaseArg === 'bridges' ? 'image' : 'video')) === 'video'
    return agent(
      `${CTX}
TASK (PAID — this exact item was founder-approved; generate it and NOTHING else): execute this ${isVideo ? 'video clip' : 'still'} via the Higgsfield MCP (load tools via ToolSearch: generate_${isVideo ? 'video' : 'image'}, media_upload, media_confirm, job_status, balance).
ITEM (verbatim, do not alter prompt/model/tier): ${JSON.stringify(item)}
HARD RULES: exactly ONE generate_* call for this item in this invocation. Ignore any rerollBudget/riskNote metadata for firing decisions — re-rolls require a NEW founder-approved manifest, never a decision made inside this call. If the job errors, you may retry the SAME call once (transient failure); a second failure = stop and report ok:false.
Steps: (0) verify param names/roles for THIS model via models_explore + Context7 (per DOC VERIFICATION above) — never guess a param shape; (1) balance check; (2) media_upload -> curl PUT -> media_confirm for each start/end/reference file; (3) run the get_cost preflight FIRST — if live cost > item.estCrHigh * 1.5, ABORT with ok:false and the quoted cost instead of firing; (4) fire the generation; (5) poll job_status to completion (3-8 min typical); (6) download to ${WORKDIR}/${phaseArg}/${item.id}.${isVideo ? 'mp4' : 'png'}; (7) verify (ffprobe duration/resolution for video; nontrivial file size for stills). Return JSON per schema. If the MCP is unavailable, return ok:false — do NOT improvise an alternative paid path.`,
      { label: `${phaseArg}:${item.id}`, phase: PAID[phaseArg], schema: EXEC_SCHEMA }
    )
  }))
  // Never silently drop a possibly-spent item: nulls (stalled/killed agents)
  // become explicit failures so cost reconciliation sees them.
  const reconciled = results.map((r, i) => r || { id: items[i].id, ok: false, actualCr: 0, note: 'agent stalled/no response — VERIFY whether the job fired via show_generations before re-approving this item' })
    // The per-item 1.5x ceiling is instructed in the agent prompt, but prompts
    // are not enforcement — re-check reported spend in code so an over-ceiling
    // fire surfaces as a typed flag, not buried prose (fails loud downstream).
    .map((r, i) => (typeof r.actualCr === 'number' && r.actualCr > items[i].estCrHigh * 1.5)
      ? { ...r, overCap: true, note: `${r.note} | OVER-CEILING: actualCr ${r.actualCr} > estCrHigh ${items[i].estCrHigh} x1.5` }
      : r)
  const spent = reconciled.reduce((s, r) => s + (r.actualCr || 0), 0)
  return {
    phase: phaseArg, results: reconciled, spentCr: spent, approvedCapCr: A.manifest.capCr,
    next: phaseArg === 'bridges' ? 'Report spend vs cap to founder. Then {phase:"previz"} with its approved manifest (bridge paths now exist).'
        : phaseArg === 'previz' ? 'Report spend vs cap. Then {phase:"assemble"} (free); founder eyes-on review marks keepers.'
        : 'Report spend vs cap. Then {phase:"assemble", tier:"final"}; then audio (create_voice + SFX post-mix, -14 LUFS) + reframe + ship.',
  }
}

// ---------------------------------------------------------------------------
if (phaseArg === 'assemble') {
  phase('Assemble')
  const tier = A.tier || 'previz'
  const cut = await agent(
    `${CTX}
TASK (free): assemble the rough cuts with ffmpeg (confirmed at /opt/homebrew/bin/ffmpeg). Clips are in ${WORKDIR}/${tier === 'final' ? 'final' : 'previz'}/.
Follow the spec's "PREVIZ ASSEMBLY RECIPE + COLD-CUT EDL" section EXACTLY (it exists — read it): (1) normalize every clip (${tier === 'final' ? '1080x1920' : '720x1280'}@24 yuv420p libx264 crf18); (2) concat with 0.2s xfade at morph seams, cumulative offsets from ffprobe durations; (3) burn captions in the center safe band (Archivo/Anton; world labels; the VO line verbatim at the KC reveal; the split CTA end card); (4) out/master-9x16.mp4; (5) derive the 9-15s COLD cut per the EDL (product-forward open, hard-cut montage, lower-third CTA at ~sec 3, KC reveal, extended CTA card); (6) 1:1 center-crop with repositioned captions; 16:9 only at final tier via Higgsfield reframe (do NOT ship the blur-pillarbox fallback).
Verify every output with ffprobe and return JSON: {masters:[{path,durationSec,resolution}], coldCut:{path,durationSec}, missingClips:[ids], notes}. Missing clips: skip gracefully and list them — never block the cut on an absent shot.`,
    { label: 'assemble:cuts', phase: 'Assemble' }
  )
  return { cut, next: tier === 'final' ? 'Audio pass (create_voice line + SFX post-mix at -14 LUFS/-1dBTP), mux, reframe 16:9, ship both cuts.' : 'Founder eyes-on review (watch muted, phone-size). Mark KEEPER/RESHOOT per shot -> {phase:"final", approved:"y", manifest:{items: keepers-at-final-tier (carry kind:"video"|"image" per item), signature, capCr}}.' }
}

throw new Error(`Unknown phase "${phaseArg}". Valid: prep | bridges | previz | assemble | final.`)
