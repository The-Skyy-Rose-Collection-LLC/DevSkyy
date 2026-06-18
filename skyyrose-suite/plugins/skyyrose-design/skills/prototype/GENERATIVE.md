# Generative Prototype

Produce **several radically different variants of a generated artifact** — image, video, 3D asset, audio, copy, a design comp — present them side-by-side, let the user pick one (or steal bits from each), throw the rest away.

Use this when the question is **"which produced artifact / approach is right?"** and the medium is something *generated* rather than a screen (UI.md) or a state model (LOGIC.md). If the artifact is a web page, that's UI.md. If it's business logic, that's LOGIC.md. Everything else that gets *produced* — a hero image, a lookbook shot, a 3D mesh, a voiceover, a tagline set — lives here.

## When this is the right shape

- "Which way should this hero image / lookbook shot look?"
- "Show me a few options for this product render before we commit the batch."
- "Try this on-model shot through a couple of different engines and let me compare."
- "I want to hear two takes on this voiceover / read three versions of this headline."
- Any time the user would otherwise pick blindly between approaches they can't see yet.

The variants usually differ along one of these axes — pick whichever the question is really about:

- **Engine / model** — same prompt, different generators (e.g. FASHN try-on vs gpt-image-2 edit vs FLUX Kontext). Best when "what's the right tool" is the open question.
- **Approach / method** — same engine, structurally different method (text-to-image vs reference-composite vs masked inpaint). Best when the *technique* is unsettled.
- **Direction / concept** — same engine and method, genuinely different creative directions (not different seeds). Best when the *look* is open.

Differing only by **seed or a single parameter** is not a prototype — it's a re-roll. Variants must disagree about something the user actually has to decide.

## Process

### 1. State the question and pick N

Default to **3 variants**; cap at 5. Write the plan in one line at the top of the prototype location:

> "One Love Hurts on-model look (bomber + joggers, in the gothic scene), generated three ways — FASHN try-on / gpt-image-2 edit / FLUX Kontext — to decide which wears most naturally."

Name the axis explicitly (engine / approach / direction) so the comparison is fair — all three should answer the *same* brief, varying only along that axis.

### 2. Isolate inputs from the throwaway generator

The **inputs** are the bit worth keeping — the real garment files, the approved scene, the verified prompt, the canonical references. Resolve them through the project's canonical sources (catalog, dossiers, visual manifest), not ad-hoc. The generator script around them is throwaway.

Put the prototype in a clearly-marked throwaway location next to where the real pipeline lives — e.g. `renders/.../_prototype/` or `scripts/.../proto-*.py` — with `prototype` in the name. One in-memory/scratch output dir; never write variants into a production asset path.

### 3. COST GATE — before any paid or metered generation

Generative media usually **costs money or compute**. Before generating, STOP-AND-SHOW the exact manifest: engine(s), model id, image count, per-unit cost, total estimate, hard cap, output path. Wait for explicit `y`. A free dry-run / `plan` mode that builds the prompts and prints the manifest **without** calling any API is the correct first run. (This step is what makes a generative prototype safe — never skip it for paid engines.)

### 4. Generate the variants — one command

One runnable command (the project's task runner / `python <path>`), with the same brief fed to each variant and only the chosen axis varying. Mark each output so the variant is obvious: `<look>-<engine>.png`. Keep generation resilient — one variant failing shouldn't kill the others (surface the failure, continue).

### 5. Present one comparable view

The user must judge variants **together**, not one at a time. Produce a single side-by-side artifact in the medium's native form:

- **Images / video frames** — a labelled montage / contact sheet (each tile tagged with its engine/approach), plus the full-res originals.
- **Audio** — a single playlist / concatenated stems with spoken labels between takes.
- **Copy** — a single doc, variants stacked with headers.

Send the comparison to the user (surface the files). Respect any platform constraints — e.g. batch image reads, don't retry past a quota.

### 6. Hand it over

Give the user the comparison + the per-variant labels. The useful feedback is usually **"the garment from A but the lighting from C"** — that's the real direction. If they want another axis explored, that's a new round (re-gate cost).

### 7. Capture the answer and clean up

The winning *approach* (and *why*) is the only durable output. Capture it in `NOTES.md` next to the prototype (or a commit/ADR/memory entry), with the question it answered. Then fold the winning engine/approach into the real pipeline and delete the losing variants + the throwaway generator. Keep the resolved inputs (prompts, refs) — they're reusable.

## Worked example — on-model lookbook (do / don't)

**Question:** "Which engine makes the real Love Hurts garments look genuinely *worn* (not floating) on a model in the gothic scene?" Axis = **engine**.

| Step | ✅ Do | ❌ Don't |
|------|-------|---------|
| Inputs | Resolve the garment files from the catalog + `data/product-references/`; reuse the approved `love-hurts-remake-v2-masked.png` scene. | Describe the garments in a prompt and let the model invent them. |
| Variants | Same look + same scene through **3 different engines** — FASHN try-on, gpt-image-2 edit (reference-guided), FLUX Kontext. | Run gpt-image-2 three times with different seeds and call it three variants. |
| Location | Write to `renders/oai/_lookbook/_prototype/<look>-<engine>.png`. | Write into `assets/.../products/` where it could be mistaken for a real asset. |
| Cost | `python proto.py plan` (free) → show the manifest (`3 engines × 1 look`, per-unit + total) → wait for `y`. | Fire all three engines immediately because "it's only a couple dollars." |
| Present | One labelled montage (`engine` tag per tile) + the full-res originals, sent to the user. | Send three bare PNGs across three messages with no labels. |
| Verdict | "FLUX Kontext wins — garment seats into the light, no floating" → `NOTES.md` → fold that engine into the real pipeline, delete the rest. | Leave all three + the generator in the repo and move on. |

The payoff of the right version: the user says *"the try-on from FASHN but the lighting from Kontext"* — a real, buildable direction you could not have reached by arguing about it in prose.

## Verify before hand-over (authoritative)

Run a check that can return **"no"** — never hand over on assumption. Concrete recipe for image/video variants:

```bash
cd renders/oai/_lookbook/_prototype
# 1. every variant exists and DECODES (catches zero-byte / truncated / API-error blobs)
for f in <look>-*.png; do identify -format '%f %wx%h %m\n' "$f" || echo "FAIL: $f"; done
# 1b. NOT BLANK — a render can decode fine yet be a uniform/empty image (an engine
#     that "succeeds" with an all-black/grey frame). stddev≈0 => blank => FAIL.
for f in <look>-*.png; do echo "$f $(convert "$f" -colorspace Gray -format '%[fx:standard_deviation]' info:)"; done
# 2. variants are NOT re-rolls — hashes must all differ
shasum <look>-*.png            # identical hashes => same image => not a prototype
# 3. THIS prototype's outputs are confined to the throwaway dir (scope to your
#    own outputs — don't grep all untracked files or you'll false-flag unrelated
#    pre-existing state). The output dir path must carry a throwaway marker.
pwd | grep -qE '_prototype|/_lookbook|/scratch|/tmp/' \
  && echo "clean — outputs in a throwaway location" \
  || echo "LEAK: prototype is writing outside a throwaway dir"
```

Note the scoping: check **the files the prototype produced**, not the whole working tree — a repo often has unrelated untracked assets, and flagging those is a false alarm, which erodes trust in the check.

Then confirm by eye (batch the image reads, never retry past quota): each variant answers the stated question and differs along the *named axis* (here: engine), not by accident. Report the result as evidence — "3 files, 3 distinct hashes, all 1536×1024, decoded OK, none in asset paths" — not "looks good." For non-image media: decode/play each file, diff transcripts/waveforms/text to prove the variants differ, confirm the comparison artifact was delivered. Any failure → fix before hand-over.

## Anti-patterns

- **Re-rolls dressed as variants.** Different seed / one tweaked parameter is not a prototype. Variants must disagree about engine, method, or direction.
- **Skipping the cost gate.** Never fire a paid generator without the STOP-AND-SHOW manifest + `y`. A free `plan`/dry-run first is mandatory.
- **Writing into production asset paths.** Variants are throwaway — keep them in a `_prototype/` / scratch dir so a stray one can't get treated as a real asset.
- **Presenting variants one at a time.** Without a side-by-side, every variant looks fine alone; the comparison is the whole point.
- **Inventing inputs.** The garment, product, scene, or facts must resolve through canonical sources — a prototype that hallucinates the subject answers the wrong question.
- **Keeping the generator.** When the question's answered, the generator script is deleted; only the verdict and the reusable inputs survive.
