# Vendored assets

Fetched from official upstream releases, git-ignored, bootstrapped on demand —
mirrors the repo-root `vendor/` convention (see `scripts/setup_trellis.sh`).

| File | Source | Pinned version |
|------|--------|----------------|
| `FBX2glTF-linux-x64` | https://github.com/facebookincubator/FBX2glTF/releases | v0.9.7 |
| `FBX2glTF-darwin-x64` | https://github.com/facebookincubator/FBX2glTF/releases | v0.9.7 (no darwin-arm64 release exists; runs under Rosetta 2 on Apple Silicon) |
| `three.r128.min.js` | https://github.com/mrdoob/three.js/tree/r128/build | r128 |
| `GLTFLoader.r128.js` | https://github.com/mrdoob/three.js/tree/r128/examples/js/loaders | r128 |
| `OrbitControls.r128.js` | https://github.com/mrdoob/three.js/tree/r128/examples/js/controls | r128 |

To bootstrap:

```bash
bash scripts/setup_character_pipeline_vendor.sh
```

`convert.py` and `package.py` fail with an explicit, actionable error naming
this script if any of these files are missing.
