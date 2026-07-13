# Export & Compression Pipeline (gltf-transform)

Applies `doctrine.md`'s numeric-gate and independent-verification rules throughout.

## The confirmed pipeline order — draco LAST, not first

Confirmed against the in-repo production baseline (`skyyrose-wp-platform`'s
`threejs-immersive.md`, and re-verified directly against the real production `skyy.glb` this
session via `npx @gltf-transform/cli inspect`):

```
resize  →  jpeg --formats png --quality 85  →  draco
```

Draco (geometry compression) runs LAST, after texture re-encoding — the reverse of a naive
"compress geometry first" assumption. Reordering this produces a technically-valid but
suboptimal file; verify the order every time, don't trust memory.

## The `--formats` gotcha, verbatim

The `jpeg` command defaults to reprocessing only textures that are ALREADY jpeg. Converting PNG
source textures requires explicitly passing `--formats png`, or PNG textures silently pass
through unconverted and unresized — a real, previously-hit mistake on this project, not a
hypothetical.

## No fourth stage

The in-repo production baseline names exactly three operations (resize, jpeg, draco). Do not
add a `gltf-transform optimize` stage on the strength of an unverified brief or a general
"more compression is better" instinct — if a future need for it arises, confirm it via Context7
plus a real CLI run before treating it as doctrine, the same way the three-stage baseline
itself was confirmed this session.

## The invocation itself — confirmed this session, don't assume the bare binary works

A bare `gltf-transform` command does not resolve in this environment — it maps to a different,
nonexistent npm package and fails immediately. The correct invocation, confirmed via a real run
against the production `skyy.glb` this session:

```bash
npx @gltf-transform/cli resize --width 1024 --height 1024 input.glb resized.glb
npx @gltf-transform/cli jpeg --formats png --quality 85 resized.glb jpeg.glb
npx @gltf-transform/cli draco jpeg.glb output.glb
```

Real output confirmed this session against the actual production asset
(`wordpress-theme/skyyrose-flagship/assets/models/skyy.glb`, via `main`'s committed blob):
1024×1024 JPEG texture at 217.74 KB, `KHR_draco_mesh_compression` present in
`extensionsRequired`. A stale local copy of the same nominal file inspected earlier in this
session showed 2048×2048 at 834.76 KB with no draco extension — a reminder that this pipeline's
output must be reconfirmed against the actual file in hand, not assumed from a filename or a
prior session's note about what the file "should" contain.

## Post-pipeline check

Parse the final GLB (`npx @gltf-transform/cli inspect`) to confirm the intended end state —
draco-compressed geometry present, textures at target format and dimensions — rather than
trusting the CLI's exit code alone. Chain all three stages as one invocation sequence and
inspect once at the end, not after every micro-step, per efficient-production discipline.
