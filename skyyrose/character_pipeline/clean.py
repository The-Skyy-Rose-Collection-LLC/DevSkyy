"""WS2 — static cleanup pass: bake node transform, ground+center, PBR fix, texture opt.

Generalizes clean_static.py's hardcoded `V *= 100.0` + `-90deg X` bake: reads
the ACTUAL node TRS chain (composed from scene root down to the mesh node,
handling `matrix`-form nodes too) instead of assuming Meshy's specific export
transform (spec WS2 known-delta #2). Everything downstream — grounding, the
degenerate-triangle gate, PBR correction, texture re-encode — matches the
reference script's validated logic.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image
from pygltflib import (
    ARRAY_BUFFER,
    ELEMENT_ARRAY_BUFFER,
    GLTF2,
    Asset,
    Attributes,
    Buffer,
)
from pygltflib import Image as GImage
from pygltflib import (
    Material,
    Mesh,
    Node,
    PbrMetallicRoughness,
    Primitive,
    Sampler,
    Scene,
    Texture,
    TextureInfo,
)

from . import _glb_io
from .config import PBR, TEX
from .convert import PipelineError


@dataclass
class CleanResult:
    glb_path: Path
    report: dict = field(default_factory=dict)


def _quat_to_matrix(q: tuple[float, float, float, float]) -> np.ndarray:
    x, y, z, w = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )


def _node_local_matrix(node: Node) -> np.ndarray:
    if node.matrix:
        # glTF stores node.matrix column-major; reshape+transpose to row-major 4x4.
        return np.array(node.matrix, dtype=np.float64).reshape(4, 4).T
    t = np.array(node.translation or [0, 0, 0], dtype=np.float64)
    r = _quat_to_matrix(node.rotation or [0, 0, 0, 1])
    s = np.array(node.scale or [1, 1, 1], dtype=np.float64)
    m = np.eye(4)
    m[:3, :3] = r @ np.diag(s)
    m[:3, 3] = t
    return m


def _find_node_chain(gltf: GLTF2, mesh_index: int) -> list[Node]:
    """Nodes from scene root down to (and including) the node referencing
    `mesh_index`, so their TRS can be composed into one net transform."""

    def walk(node_idx: int, chain: list[Node]) -> list[Node] | None:
        node = gltf.nodes[node_idx]
        chain = [*chain, node]
        if node.mesh == mesh_index:
            return chain
        for child_idx in node.children or []:
            found = walk(child_idx, chain)
            if found:
                return found
        return None

    scene = gltf.scenes[gltf.scene or 0]
    for root_idx in scene.nodes:
        found = walk(root_idx, [])
        if found:
            return found
    raise PipelineError(f"no node chain found for mesh index {mesh_index}")


def _combined_transform(gltf: GLTF2, mesh_index: int) -> np.ndarray:
    """Composes every ancestor node's TRS (root -> mesh node) into one 4x4,
    instead of assuming a single flat S=100/-90degX node."""
    m = np.eye(4)
    for node in _find_node_chain(gltf, mesh_index):
        m = m @ _node_local_matrix(node)
    return m


def _bake_transform(
    V: np.ndarray, N: np.ndarray, transform: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    homog = np.concatenate([V, np.ones((len(V), 1))], axis=1)
    v_out = (homog @ transform.T)[:, :3]
    # Normals transform by the inverse-transpose of the linear part (the
    # "normal matrix"), not the linear part itself — identical for rotations,
    # but a non-uniformly-scaled ancestor node would otherwise tilt normals
    # the wrong way with no error, visible only as broken lighting at runtime.
    lin = transform[:3, :3]
    try:
        normal_mat = np.linalg.inv(lin).T
    except np.linalg.LinAlgError as exc:
        raise PipelineError("mesh node transform is singular (zero scale on some axis)") from exc
    n_out = N @ normal_mat.T
    n_out /= np.linalg.norm(n_out, axis=1, keepdims=True) + 1e-12
    return v_out, n_out


def _ground_and_center(V: np.ndarray) -> np.ndarray:
    V = V.copy()
    V[:, 1] -= V[:, 1].min()
    V[:, 0] -= (V[:, 0].min() + V[:, 0].max()) / 2
    V[:, 2] -= (V[:, 2].min() + V[:, 2].max()) / 2
    return V


def _degenerate_triangle_count(V: np.ndarray, F: np.ndarray) -> int:
    tri = V[F.reshape(-1, 3)]
    areas = 0.5 * np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    return int((areas < 1e-12).sum())


def _is_dead_emissive(image_bytes: bytes) -> bool:
    im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return int(np.array(im).max()) < PBR["dead_emissive_max"]


def _reencode_basecolor(image_bytes: bytes, max_dim: int, quality: int) -> bytes:
    im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    im = im.resize((max_dim, max_dim), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality)
    return buf.getvalue()


def clean_static(
    input_glb: str | Path, out_path: str | Path, target_height: float | None = None
) -> CleanResult:
    """WS2: bakes the mesh's real node transform into positions/normals, grounds
    feet at y=0 and centers x/z, fixes PBR (metallic 0, roughness 0.65, drops
    dead emissive), re-encodes the basecolor texture to the hero spec, and
    writes a single clean-node GLB with no outstanding node transforms.
    """
    gltf = GLTF2().load(str(input_glb))
    blob = gltf.binary_blob()
    mesh_index = 0
    prim = gltf.meshes[mesh_index].primitives[0]

    V = _glb_io.read_accessor(gltf, blob, prim.attributes.POSITION).astype(np.float64)
    N = _glb_io.read_accessor(gltf, blob, prim.attributes.NORMAL).astype(np.float64)
    UV = _glb_io.read_accessor(gltf, blob, prim.attributes.TEXCOORD_0).astype(np.float32)
    F = _glb_io.read_accessor(gltf, blob, prim.indices).astype(np.uint32)

    transform = _combined_transform(gltf, mesh_index)
    V, N = _bake_transform(V, N, transform)
    V = _ground_and_center(V)
    height = float(V[:, 1].max())
    if target_height:
        V = V * (target_height / height)
        height = target_height

    degenerate = _degenerate_triangle_count(V, F)
    v32, n32 = V.astype(np.float32), N.astype(np.float32)

    if prim.material is None:
        raise PipelineError("primitive has no material to read baseColorTexture from")
    material = gltf.materials[prim.material]
    if not (material.pbrMetallicRoughness and material.pbrMetallicRoughness.baseColorTexture):
        raise PipelineError("no baseColorTexture found on primitive material")
    basecolor_image_index = gltf.textures[
        material.pbrMetallicRoughness.baseColorTexture.index
    ].source

    basecolor_bytes = _glb_io.image_bytes(gltf, blob, basecolor_image_index)
    max_dim, quality = TEX["hero"]
    tex_bytes = _reencode_basecolor(basecolor_bytes, max_dim, quality)

    dropped_emissive = False
    if material.emissiveTexture:
        emissive_index = gltf.textures[material.emissiveTexture.index].source
        dropped_emissive = _is_dead_emissive(_glb_io.image_bytes(gltf, blob, emissive_index))

    writer = _glb_io.GLBWriter()
    a_pos = writer.add_accessor(
        v32.tobytes(),
        ARRAY_BUFFER,
        5126,
        len(v32),
        "VEC3",
        (v32.min(0).tolist(), v32.max(0).tolist()),
    )
    a_nrm = writer.add_accessor(n32.tobytes(), ARRAY_BUFFER, 5126, len(n32), "VEC3")
    a_uv = writer.add_accessor(UV.tobytes(), ARRAY_BUFFER, 5126, len(UV), "VEC2")
    a_idx = writer.add_accessor(F.tobytes(), ELEMENT_ARRAY_BUFFER, 5125, len(F), "SCALAR")
    img_view = writer.add_image(tex_bytes)
    bin_blob = writer.finalize()

    out = GLTF2(
        asset=Asset(version="2.0", generator="SkyyRose character_pipeline"),
        scenes=[Scene(nodes=[0])],
        scene=0,
        nodes=[Node(name="CleanedMesh", mesh=0)],
        meshes=[
            Mesh(
                name="CleanedMesh",
                primitives=[
                    Primitive(
                        attributes=Attributes(POSITION=a_pos, NORMAL=a_nrm, TEXCOORD_0=a_uv),
                        indices=a_idx,
                        material=0,
                    )
                ],
            )
        ],
        materials=[
            Material(
                name="CleanedMesh_mat",
                pbrMetallicRoughness=PbrMetallicRoughness(
                    baseColorTexture=TextureInfo(index=0),
                    metallicFactor=PBR["metallic"],
                    roughnessFactor=PBR["roughness"],
                ),
                doubleSided=False,
            )
        ],
        textures=[Texture(source=0, sampler=0)],
        samplers=[Sampler(magFilter=9729, minFilter=9987, wrapS=10497, wrapT=10497)],
        images=[GImage(name="BaseColor", mimeType="image/jpeg", bufferView=img_view)],
        buffers=[Buffer(byteLength=len(bin_blob))],
        bufferViews=writer.views,
        accessors=writer.accessors,
    )
    out.set_binary_blob(bin_blob)
    out_path = Path(out_path)
    out.save(str(out_path))

    report = {
        "vert_count": int(len(v32)),
        "tri_count": int(len(F) // 3),
        "height_m": height,
        "degenerate_tris": degenerate,
        "dropped_dead_emissive": dropped_emissive,
        "output_bytes": out_path.stat().st_size,
        "input_bytes": Path(input_glb).stat().st_size,
    }
    return CleanResult(glb_path=out_path, report=report)
