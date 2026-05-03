# Three.js Immersive Experiences — Agent Guide

> **V2 Build Addendum (Phase 0+, 2026-05-03):** This guide is augmented by the Skyyrose V2 build:
> - Source-of-truth plans: `docs/SKYYROSE_V2_MASTER_PLAN.md` §0.4 (this directory's allowed/forbidden table), §3 (integration architecture), §5.0 (avatar GLB rig prereq), §5.2/5.8 (WebGL canvas, WebXR layer)
> - Cost-cap policy for paid API calls: `eval/cost-cap-policy.md` (hybrid stance — supersedes CLAUDE.md STOP-AND-SHOW for ≤$1 calls)
> - 6-step per-edit workflow (Phase 0.5+ once toolchain scripts ship): adds `verify-impl` (Step 2, Context7-first) + `post-simplify-verify` (Step 4, 4-check revert protocol) + `kb-distill` (Step 6, KB pattern entry) on top of the lint/simplify/verification-loop workflow already documented below.
> - KB cross-references: `knowledge-base/README.md` integration map covers 4 prior memory systems (OpenWolf, Serena, GSD, claude-mem) + new `knowledge-base/` + graphify topology graph (Phase 0 Deliverable J).
> - Cross-boundary handoff: sequenced agents only (agent A commit → exit → agent B reads → commit). Never simultaneous.
> - WebXR is enhancement; desktop must always have the standard 3D fallback path (V2 §1.2 + §9 risk matrix).

## Isolated Workspace

**Your scope — read/write freely:**
```
wordpress-theme/skyyrose-flagship/assets/js/experiences/
```

**Adjacent reads allowed (do not write):**
```
wordpress-theme/skyyrose-flagship/assets/js/init-3d.js   # bootstrap — understand wiring
wordpress-theme/skyyrose-flagship/assets/js/skyy-3d.js   # avatar loader
wordpress-theme/skyyrose-flagship/template-immersive-*.php  # read PHP template wiring
wordpress-theme/skyyrose-flagship/inc/enqueue.php           # read how scenes are loaded
```

**Out of bounds — do not touch:**
```
wordpress-theme/skyyrose-flagship/assets/js/init-3d.js     # read only
wordpress-theme/skyyrose-flagship/assets/js/skyy-3d.js     # read only
wordpress-theme/skyyrose-flagship/assets/css/              # separate agent scope
wordpress-theme/skyyrose-flagship/inc/                     # separate agent scope
frontend/                                                  # completely separate system
```

The Three.js scenes are the most complex JS in the project. Changes here can break 3D rendering silently (WebGL errors don't crash the page). Test every change locally before reporting complete.

---

## Infrastructure

**Host**: WordPress.com Business plan — NOT self-hosted
- **Deploy**: `bash scripts/deploy-theme.sh` (hot-swap script) OR `sftp sftp.wp.com` (SSH) — both require explicit user confirmation
- Three.js loaded via CDN — no npm build pipeline
- Immersive templates use the **2D composited-image system** as the primary content layer (PHP + `immersive.js`). Three.js scenes are loaded on top via this directory's files.

---

## Permissions

You MAY:
- Modify any Experience subclass (`blackrose-experience.js`, `lovehurts-experience.js`, `signature-experience.js`)
- Add new Three.js effects by extending `ExperienceBase` — call `this.addPass()` for post-processing
- Create new utility files within `experiences/`
- Add new spawn points or interact-able objects to existing worlds
- Implement `skyy-cameo.js` (easter egg scaffold — see architecture below)

You MUST NOT:
- Modify `experience-base.js` for per-collection behavior — extend it in the subclass
- Hardcode product data in JS — read from `window.SKYYROSE_PRODUCTS` (PHP-injected)
- Add `MeshLambertMaterial` — PBR materials only (`MeshStandardMaterial` / `MeshPhysicalMaterial`)
- Exceed 500K triangles in any single scene (performance budget: 60fps on M2)
- Add new Three.js CDN imports not already in `experience-base.js`
- Deploy immersive template changes without local Three.js scene verification

---

## Safeguards — Hard Rules

**Extend, never modify the base:**
```js
// WRONG — modifying base class for per-collection behavior
// experience-base.js:
addFogEffect() { /* black-rose-specific code */ }

// CORRECT — override in subclass
// blackrose-experience.js:
import ExperienceBase from './experience-base.js';
class BlackRoseExperience extends ExperienceBase {
    initScene() {
        super.initScene();
        this.addFog({ color: 0x0a0a0a, near: 10, far: 100 });
    }
}
```

**Performance budget — check triangle count:**
```js
let triangles = 0;
scene.traverse(obj => {
    if (obj.isMesh) triangles += obj.geometry.index?.count / 3 || obj.geometry.attributes.position.count / 3;
});
console.log('Triangle count:', triangles); // Must be < 500,000
```

**Product data from PHP only:**
```js
// WRONG — hardcoded product in JS
const products = [{ sku: 'br-001', name: 'Black Rose Crewneck' }];

// CORRECT — PHP injects via window global
const products = window.SKYYROSE_PRODUCTS ?? [];
```

**PBR materials only:**
```js
// WRONG
const mat = new THREE.MeshLambertMaterial({ color: 0x333333 });

// CORRECT
const mat = new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.8, metalness: 0.1 });
```

**Immediate fix mandate**: If you find a `MeshLambertMaterial` or hardcoded product data while working, fix it in the same commit.

---

This directory contains the Three.js immersive world system for the SkyyRose WordPress theme.
Each collection gets a dedicated 3D world that loads on `template-immersive-*.php` templates.

## Architecture

```
experience-base.js        ← Base class: PBR renderer, post-processing, particles, shadows (492L)
init-3d.js                ← Bootstrap: detects collection, instantiates correct Experience (385L)
blackrose-experience.js   ← Black Rose world: Oakland Bay Bridge, night, street luxury (757L)
lovehurts-experience.js   ← Love Hurts world: gothic cathedral, enchanted rose dome (696L)
signature-experience.js   ← Signature world: Golden Gate Bridge, golden hour (521L)
luxury-animations.js      ← Shared luxury animation utilities (timelines, eases)
mannequin-bust.js         ← Ghost mannequin 3D bust renderer (product preview overlay)
skyy-3d.js               ← (in assets/js/) Skyy avatar: loads skyy.glb, expects Mixamo idle+walk
```

## Collection-to-Scene Mapping

| Collection    | World                          | Scene mood                        |
|---------------|-------------------------------|-----------------------------------|
| Black Rose    | Oakland Bay Bridge (night)     | Street luxury, "Luxury Grows from Concrete" |
| Love Hurts    | Gothic cathedral / rose dome   | Enchanted, Beauty & Beast (Beast's POV) |
| Signature     | Golden Gate Bridge (golden hour)| Fashion runway, Bay Area fog through cables |
| Kids Capsule  | (no immersive template yet)    | TBD                               |

## PHP Template Wiring

Each world is loaded via a dedicated template registered in `inc/enqueue.php`:
- `template-immersive-black-rose.php` → slug `immersive-black-rose`
- `template-immersive-love-hurts.php` → slug `immersive-love-hurts`
- `template-immersive-signature.php` → slug `immersive-signature`
- `template-immersive-kids-capsule.php` → slug `immersive-kids-capsule` (template exists, no world yet)

`init-3d.js` reads `window.SKYYROSE_COLLECTION` (set by the PHP template) to pick which Experience class to instantiate.

## Skyy Avatar — Current State (2026-04-27)

`assets/models/skyy.glb` (32MB) has **0 bones, 0 animations**. The character mesh renders but
cannot animate. `skyy-3d.js` calls `mixer.clipAction(AnimationClip.findByName(clips, 'idle'))` —
this fails silently when clips is empty.

**What's needed (JS side only):**
1. Drop in a rigged GLB with Mixamo clip names `idle` and `walk`.
2. `skyy-3d.js` will auto-detect the clips array and begin the idle loop.
3. No JS changes required — the loading + animation scaffold is already wired.

**Do NOT re-rig in JS** — the mesh needs a Blender/Mixamo rig pass. File the GLB replacement
under `assets/models/skyy-rigged.glb` and swap the import path once verified.

## Easter Egg — Skyy Hidden in Each World

Goal: A small Pixar-quality Black girl avatar (the SkyyRose mascot) hidden somewhere in each
of the 3 collection worlds. Finding all 3 triggers the brand intro sequence.

Current state: **No scaffold exists.** The feature is planned but not implemented.

Minimum architecture when building this:
- `SkyyCameoManager` class (new file: `skyy-cameo.js`) — tracks found count via `localStorage`
- Each Experience subclass registers a `cameo` spawn point as `{ position, triggerRadius }`
- `init-3d.js` instantiates `SkyyCameoManager` after world loads and passes the spawn point
- On player proximity (raycaster distance < triggerRadius): play wave anim, set found flag, emit event
- After 3 found: `window.dispatchEvent(new CustomEvent('skyy:allFound'))` → intro sequence

## Rules

- **No new Three.js dependencies** beyond what `experience-base.js` already imports via CDN.
- Use `ExperienceBase` methods for lighting, post-processing, and particle systems — don't re-implement.
- PBR materials only (`MeshStandardMaterial` / `MeshPhysicalMaterial`) — no `MeshLambertMaterial`.
- Post-processing passes live in the base class. Add per-world passes by calling `this.addPass(pass)`.
- `mannequin-bust.js` is purely additive — it overlays a product preview, it does not modify the scene graph.
- Performance budget: 60fps on M2 MacBook. Don't exceed 500K triangles in any single scene.

## Mandatory Quality Workflow

After every change to any file in `experiences/`, run ALL three steps in order.

### 1. Code Quality Check
```bash
cd wordpress-theme/skyyrose-flagship
# Syntax check the modified file:
node --check assets/js/experiences/blackrose-experience.js
node --check assets/js/experiences/experience-base.js

# Verify no hardcoded product data:
grep -n "sku:\|name:\|'br-\|'sg-\|'lh-\|'kids-" assets/js/experiences/
# Must return nothing (product data comes from window.SKYYROSE_PRODUCTS only)
```

### 2. /simplify
Invoke the `code-simplifier` agent on the modified file. In Three.js code, focus on:
- Geometry disposal (missing `geometry.dispose()` + `material.dispose()` on cleanup = memory leak)
- Event listener removal in `dispose()` method
- Repeated `new THREE.Vector3()` allocations in animation loops (cache them)

### 3. /verification-loop
```bash
# Must be tested locally — Three.js scene changes cannot be verified via curl
# 1. Open the immersive template in a local WP environment or static preview
# 2. Open Chrome DevTools → Console — verify 0 WebGL errors
# 3. Check Performance tab: frame time must stay < 16.7ms (60fps)
# 4. Verify triangle count stays under 500K
# 5. Test on a lower-end device or throttled CPU (6x slowdown in DevTools)

# After confirming local test passes, verify live site after deploy:
curl -s -o /dev/null -w "%{http_code}" https://skyyrose.co/immersive/black-rose/
# Must return 200
```

---

## Do NOT

- Modify `experience-base.js` for per-collection behavior — extend it in the subclass
- Hardcode collection product data in JS — read from `window.SKYYROSE_PRODUCTS`
- Deploy changes to immersive templates without local Three.js scene verification
- Use `MeshLambertMaterial` — PBR only (`MeshStandardMaterial` / `MeshPhysicalMaterial`)
- Exceed 500K triangles per scene (performance budget)
- Add new Three.js imports not already available via CDN in `experience-base.js`
- Touch files outside your workspace without flagging to the user
