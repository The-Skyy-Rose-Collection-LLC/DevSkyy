# 3D Fashion Garment Rendering — Knowledge Base

Source of truth for `GARMENT_3D_SPEC`. Owns the Meshy + CLO3D/Marvelous Designer + Blender workflow, GLB/USDZ export discipline, LOD strategy, and integration with the live THREE.js collection experiences in `src/collections/`.

> A 3D garment in the browser must feel as real as the one hanging in the warehouse. Topology matters. Draping matters. The tiny stitch detail on a hover-zoom matters.

---

## 1. Pipeline overview (end-to-end)

```
reference photo / techflat
  ↓
Meshy v2 (image-to-3D)  → rough GLB mesh + diffuse texture
  ↓
Blender (cleanup)       → retopology, UV unwrap, seam placement
  ↓
CLO3D / Marvelous       → cloth simulation, fit + drape + wrinkles
  ↓
Blender (bake + export) → baked normals, Draco compression, GLB + USDZ
  ↓
Viewer integration      → LuxuryProductViewer.tsx / collection experiences
```

Existing tooling wired in this repo:
- `frontend/lib/meshy/client.ts` — Meshy API v2 client (text-to-3D + image-to-3D, preview + refine modes)
- `frontend/lib/pipeline-config/pipelines/virtual-tryon.ts` — FASHN virtual try-on pipeline config
- `frontend/components/three-viewer.tsx` + `frontend/components/3d/LuxuryProductViewer.tsx` — React Three.js wrappers
- `src/collections/{BaseCollectionExperience,BlackRoseExperience,LoveHurtsExperience,RunwayExperience,ShowroomExperience,SignatureExperience}.ts` — six live THREE.js collection experiences

Do NOT create parallel viewer components — extend the existing ones.

---

## 2. Topology rules (quad-dominant, fashion-specific)

| Region | Target poly density | Must-haves |
|---|---|---|
| **Shoulder / armpit** | Dense quads | Tri-edge-loop for sleeve rotation |
| **Elbow / knee** | Dense quads + bend loops | 3 horizontal loops for clean bend deformation |
| **Hem / neckline** | Moderate | Single clean loop, no n-gons |
| **Front center torso** | Uniform quads | Symmetrical topology for mirroring |
| **Pocket / patch areas** | High-density local | Preserve stitch silhouette, normal-map details |
| **Folded regions (hood, cuffs)** | Layered loops | 2+ stacked loops to sim real fabric thickness |

- **No n-gons** anywhere — they destroy deformation and Draco compression
- **Triangles** only at final triangulation for export — never in authoring topology
- **Mirroring axis**: Y-axis (left/right symmetry) — delete right half, model left, mirror-modifier, apply before export

---

## 3. UV unwrapping

- Single UV set for diffuse + normal + roughness + metallic (PBR)
- Stack mirrored shells where branding is symmetric
- Dedicated UV shell per logo/patch region — oversize to preserve pixel density
- Padding: 16px minimum at 2K texture size to avoid bleed after mipmap
- Seams on inner/underside surfaces (under sleeve, side seam, crotch for pants)

---

## 4. Cloth simulation (CLO3D / Marvelous Designer)

Use CLO3D or Marvelous Designer for:
- Drape simulation on hero shots (jacket hanging open, hoodie relaxed)
- Wrinkle baking for static poses (save normal map from simulated mesh)
- Fabric-specific physics (satin = low friction + high drape; denim = stiff + angular folds)
- Pose-to-pose drape for lookbook sequences

Export from CLO → OBJ → back into Blender for final topology cleanup. Bake the simulated shape into the base mesh (or use as a shape key blend target).

Fabric physics presets (map to SkyyRose materials):

| SkyyRose fabric | CLO fabric preset | Drape / stiffness |
|---|---|---|
| Satin / silk | Silk Charmeuse | High drape, smooth folds |
| French terry | Cotton Jersey Medium | Medium drape, soft folds |
| Sherpa / fleece | Fleece Bulk | Low drape, blocky silhouette |
| Denim | Denim Heavy | Low drape, angular folds |
| Mesh | Mesh Sport | Very high drape, transparent |
| Leather | Leather Thick | Low drape, crisp creases |
| Knit (ribbed) | Knit Ribbed | Medium drape, directional stretch |

---

## 5. LOD strategy (hero / mid / far)

Every GLB ships three LODs for smooth viewer performance across devices.

| Tier | Triangle budget | Texture size | Use case | File target |
|---|---|---|---|---|
| **Hero (LOD0)** | 80k–120k tris | 4K diffuse + 4K normal + 2K roughness/metallic | Detailed product page, zoom, AR | < 8 MB with Draco |
| **Mid (LOD1)** | 25k–40k tris | 2K diffuse + 1K normal | Collection showcase, landing hero | < 2 MB with Draco |
| **Far (LOD2)** | 5k–10k tris | 512 diffuse + 256 normal | Thumbnail, immersive world distant view | < 300 KB |

LOD switch via THREE.js `LOD` class or distance-based swap in the collection experience. Never load LOD0 on initial page paint — defer until user hovers/interacts.

---

## 6. Export formats

### GLB (primary, web)
- **Use case:** WordPress theme product viewer, collection experiences, shop page
- **Compression:** Draco (`--draco-compression-level=7` in `gltf-transform`)
- **Required:** `extensionsUsed: ["KHR_draco_mesh_compression"]`
- **Texture packing:** UASTC for normals/metallic, ETC1S for diffuse (via `gltf-transform optimize`)

### USDZ (iOS AR)
- **Use case:** Safari mobile AR quick-look, `ar-viewer-integrate` capability
- **Required:** Metallic-roughness PBR workflow, single UV set, no Draco (USDZ doesn't support it)
- **Max size:** 50 MB for Quick Look stability

### FBX (DCC interchange, NOT for web)
- **Use case:** Round-trip to CLO/Marvelous, archival
- **Never ship FBX** to viewer or WP theme

### Meshy API output mapping
- Meshy returns GLB, FBX, USDZ, and OBJ
- **Take GLB** for Blender cleanup → re-export as optimized GLB
- **Take USDZ** directly if Meshy's AR output quality passes QA; otherwise regenerate via Blender's USDZ exporter after cleanup

---

## 7. Collection experience wiring

Six THREE.js experiences in `src/collections/` are live. Integration points for 3D garments:

| Experience | Integration hook | What to inject |
|---|---|---|
| `BaseCollectionExperience.ts` | `addProductMesh(glb)` (create this method if missing) | Parent class for all — hold the generic 3D product slot |
| `BlackRoseExperience.ts` | `placeAt(x, y, z)` in cathedral scene | LOD1/2 GLBs for ambient placement, LOD0 on selection |
| `LoveHurtsExperience.ts` | Enchanted castle / beast perspective | Single hero GLB, user inspects via rotation |
| `SignatureExperience.ts` | Golden Gate scene | GLB with auto-rotate + hotspot labels |
| `RunwayExperience.ts` | Runway walk simulation | Hero GLB attached to animated "walking" skeleton |
| `ShowroomExperience.ts` | Gallery showroom | Multiple LOD1 GLBs on pedestals, LOD0 swap on approach |

Wire via the `collection_wire` capability — the agent produces the GLB set and the exact hook parameters; the frontend_dev agent implements the hook if missing.

---

## 8. AR viewer integration

iOS Safari Quick Look:
- Add `<model-viewer>` component in product page or use `rel="ar"` on an `<a>` tag pointing at USDZ
- Usage via `frontend/components/3d/LuxuryProductViewer.tsx` — extend with `arEnabled` prop if missing

Android Scene Viewer:
- Requires GLB with proper metadata (KHR_materials_pbrSpecularGlossiness or metallic-roughness)
- Links use `intent://arvr.google.com/scene-viewer/...`

WebXR (optional):
- `@react-three/xr` for immersive WordPress experience — deferred, not in scope for this spec yet

---

## 9. QA checklist (before shipping a 3D garment)

- [ ] Topology audit: no n-gons, quad-dominant, bend-loops at joints
- [ ] UV audit: no overlapping shells, seams on inner surfaces, padding ≥16px
- [ ] Texture audit: all maps at spec resolution, sRGB diffuse, linear normal
- [ ] Drape audit: pose matches intended style (hero/flat-lay/on-model)
- [ ] LOD audit: all three LODs render correctly, swap distance tuned
- [ ] GLB validation: passes `gltf-validator` with zero errors, ≤1 warning
- [ ] USDZ validation: passes `usdchecker` with zero errors
- [ ] Viewer integration: loads in `LuxuryProductViewer` without console errors
- [ ] AR test: loads on iOS Safari Quick Look + Android Scene Viewer
- [ ] Performance: LOD0 < 16ms/frame on M1 Mac Safari, < 33ms on iPhone 13

---

## 10. Files this agent reads / writes

**Reads:**
- `frontend/lib/meshy/client.ts`
- `frontend/lib/pipeline-config/pipelines/virtual-tryon.ts`
- `src/collections/*Experience.ts`
- `wordpress-theme/skyyrose-flagship/assets/images/products/*.png|.jpg|.jpeg` (reference photos)
- `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`

**Writes:**
- `wordpress-theme/skyyrose-flagship/assets/3d/{sku}/{lod}.glb` — LOD0/1/2 GLB per SKU
- `wordpress-theme/skyyrose-flagship/assets/3d/{sku}/model.usdz` — iOS AR
- `logs/3d/{sku}-<ts>.json` — topology audit + LOD report

**Never touches:** Frontend React components directly — hands implementation briefs to `FRONTEND_DEV_SPEC`.
