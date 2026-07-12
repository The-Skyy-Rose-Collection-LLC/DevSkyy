"""WS7 — GLB variants (hero/widget) + self-contained widget/inspector HTML assembly.

Surgical texture swap keeps the texture chunk LAST in the binary blob (an
invariant weights.write_rigged_glb() already establishes) so a widget-resolution
re-encode only splices bytes at the tail — it never rebuilds bufferViews or
accessors for the rest of the file. Template assembly is a literal string
replace on `@@THREE@@`/`@@GLTFLOADER@@`/`@@ORBIT@@`/`@@GLB64@@` placeholders
(asserted gone afterward), then syntax-gated with `node --check` before it
ever ships — a broken vendored JS pin should fail the build, not the browser.
"""

from __future__ import annotations

import base64
import io
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image
from pygltflib import GLTF2

from .config import TEX
from .convert import PipelineError

_VENDOR_DIR = Path(__file__).parent / "vendor"
_TEMPLATES_DIR = Path(__file__).parent / "templates"
_SCRIPT_RE = re.compile(r"<script[^>]*>(.*?)</script>", re.DOTALL)

# Anchors patched for the external-GLB variant (spec section 7.4). Asserted to
# exist before replacement so template drift fails loudly instead of silently
# shipping a broken external loader.
_PARSE_CALL_ANCHOR = 'new THREE.GLTFLoader().parse(b64ToArrayBuffer(GLB_B64), "", function(gltf){'
_PARSE_CALL_EXTERNAL = 'new THREE.GLTFLoader().parse(window.__SRW_GLB_BUFFER__, "", function(gltf){'
_BOOTSTRAP_ANCHOR = (
    'if ("requestIdleCallback" in window) requestIdleCallback(init3D, {timeout:2500});\n'
    "else setTimeout(init3D, 800);"
)


def _read_vendor(name: str) -> str:
    path = _VENDOR_DIR / name
    if not path.exists():
        raise PipelineError(
            f"vendored asset missing at {path}. Run scripts/setup_character_pipeline_vendor.sh "
            "to fetch vendored assets."
        )
    return path.read_text()


def make_widget_glb(rigged_glb_path: str | Path, out_path: str | Path) -> Path:
    """Surgical texture swap: re-encodes the basecolor texture to widget
    resolution and splices ONLY the trailing texture chunk. Requires the
    texture chunk to already be the last buffer chunk.
    """
    gltf = GLTF2().load(str(rigged_glb_path))
    blob = gltf.binary_blob()
    img_bv_index = gltf.images[0].bufferView
    if img_bv_index != len(gltf.bufferViews) - 1:
        raise PipelineError(
            "texture bufferView is not the last buffer chunk — surgical swap requires this invariant"
        )
    tex_bv = gltf.bufferViews[img_bv_index]
    old_texture = blob[tex_bv.byteOffset : tex_bv.byteOffset + tex_bv.byteLength]

    im = Image.open(io.BytesIO(old_texture)).convert("RGB")
    max_dim, quality = TEX["widget"]
    im = im.resize((max_dim, max_dim), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality)
    new_texture = buf.getvalue()

    new_blob = blob[: tex_bv.byteOffset] + new_texture
    gltf.bufferViews[img_bv_index].byteLength = len(new_texture)
    gltf.buffers[0].byteLength = len(new_blob)
    gltf.set_binary_blob(new_blob)

    out_path = Path(out_path)
    gltf.save(str(out_path))
    return out_path


def _syntax_check_scripts(html: str) -> None:
    if shutil.which("node") is None:
        raise PipelineError(
            "node is required to syntax-gate assembled widget/inspector scripts (not found on PATH)"
        )
    for i, match in enumerate(_SCRIPT_RE.finditer(html)):
        code = match.group(1)
        if not code.strip():
            continue
        proc = subprocess.run(["node", "--check"], input=code, capture_output=True, text=True)
        if proc.returncode != 0:
            raise PipelineError(
                f"generated <script> block {i} failed `node --check`: {proc.stderr.strip()}"
            )


def _assemble_html(template_name: str, replacements: dict[str, str], out_path: Path) -> Path:
    html = (_TEMPLATES_DIR / template_name).read_text()
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)
    remaining = {p for p in ("@@THREE@@", "@@GLTFLOADER@@", "@@ORBIT@@", "@@GLB64@@") if p in html}
    if remaining:
        raise PipelineError(f"template assembly left unresolved placeholders: {remaining}")
    _syntax_check_scripts(html)
    out_path.write_text(html)
    return out_path


def make_widget_html(widget_glb_path: str | Path, out_path: str | Path) -> Path:
    """Self-contained widget HTML with the GLB embedded as base64. Zero network
    dependencies at load time — this is the default embed path (spec 7.2)."""
    glb_b64 = base64.b64encode(Path(widget_glb_path).read_bytes()).decode()
    replacements = {
        "@@THREE@@": _read_vendor("three.r128.min.js"),
        "@@GLTFLOADER@@": _read_vendor("GLTFLoader.r128.js"),
        "@@GLB64@@": glb_b64,
    }
    return _assemble_html("widget.html", replacements, Path(out_path))


def make_widget_html_external(out_path: str | Path) -> Path:
    """Widget HTML that fetches the GLB from `data-glb-src` on its own
    `<script>` tag instead of embedding it — for site-wide deploy where the
    GLB ships as a cacheable theme asset (spec section 7.4: ~1KB embed block
    vs. ~5.7MB base64). Patches the widget script's parse call site + bootstrap
    with a small fetch-then-init shim; both patch anchors are asserted present
    so template drift fails the build instead of silently shipping a loader
    that never resolves.
    """
    template = (_TEMPLATES_DIR / "widget.html").read_text()
    replacements = {
        "@@THREE@@": _read_vendor("three.r128.min.js"),
        "@@GLTFLOADER@@": _read_vendor("GLTFLoader.r128.js"),
        "@@GLB64@@": "",
    }
    html = template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    if _PARSE_CALL_ANCHOR not in html:
        raise PipelineError("widget template drifted: external-GLB parse-call anchor not found")
    if _BOOTSTRAP_ANCHOR not in html:
        raise PipelineError("widget template drifted: external-GLB bootstrap anchor not found")

    fetch_shim = (
        "var __srwGlbSrc = (document.currentScript && document.currentScript.getAttribute('data-glb-src')) "
        "|| window.SKYYROSE_WIDGET_GLB_SRC;\n"
        "var __srwGlbReady = __srwGlbSrc ? fetch(__srwGlbSrc).then(function(r){ return r.arrayBuffer(); }) "
        ": Promise.resolve(new ArrayBuffer(0));\n"
    )
    deferred_bootstrap = (
        "__srwGlbReady.then(function(buf){\n"
        "  window.__SRW_GLB_BUFFER__ = buf;\n"
        '  if ("requestIdleCallback" in window) requestIdleCallback(init3D, {timeout:2500});\n'
        "  else setTimeout(init3D, 800);\n"
        "});"
    )
    html = html.replace(_PARSE_CALL_ANCHOR, _PARSE_CALL_EXTERNAL)
    html = html.replace(_BOOTSTRAP_ANCHOR, fetch_shim + deferred_bootstrap)

    remaining = {p for p in ("@@THREE@@", "@@GLTFLOADER@@", "@@ORBIT@@", "@@GLB64@@") if p in html}
    if remaining:
        raise PipelineError(f"template assembly left unresolved placeholders: {remaining}")
    _syntax_check_scripts(html)
    out_path = Path(out_path)
    out_path.write_text(html)
    return out_path


def make_inspector_html(rigged_glb_path: str | Path, out_path: str | Path) -> Path:
    """Self-contained QA inspector HTML (orbit/skeleton/wireframe/wave)."""
    glb_b64 = base64.b64encode(Path(rigged_glb_path).read_bytes()).decode()
    replacements = {
        "@@THREE@@": _read_vendor("three.r128.min.js"),
        "@@GLTFLOADER@@": _read_vendor("GLTFLoader.r128.js"),
        "@@ORBIT@@": _read_vendor("OrbitControls.r128.js"),
        "@@GLB64@@": glb_b64,
    }
    return _assemble_html("inspector.html", replacements, Path(out_path))
