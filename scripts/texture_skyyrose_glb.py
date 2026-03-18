"""
Texture the SkyyRose GLB model using Meshy Text-to-Texture API.

Workflow:
  1. Encode local GLB as base64 Data URI → model_url
  2. POST /openapi/v1/retexture with SkyyRose prompt
  3. Poll until complete
  4. Download textured GLB + PBR maps to assets/

Usage:
    python scripts/texture_skyyrose_glb.py
    python scripts/texture_skyyrose_glb.py --glb /path/to/other.glb
"""

import argparse
import base64
import os
import sys
import time
import urllib.request
from pathlib import Path

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv(Path(__file__).parent.parent / ".env")

API_KEY = os.getenv("MESHY_API_KEY", "")
BASE_URL = "https://api.meshy.ai"

DEFAULT_GLB = Path.home() / "Downloads" / "Meshy_AI_SkyyRose_Curly_Haired_0313231945_generate.glb"
OUTPUT_DIR = (
    Path(__file__).parent.parent
    / "wordpress-theme"
    / "skyyrose-flagship"
    / "assets"
    / "images"
    / "mascot"
)

TEXTURE_PROMPT = (
    "Young Black girl, Pixar 3D style. "
    "Skin: rich warm brown, melanin-rich, luminous soft glow, NOT gray or flat. "
    "Face: smooth healthy complexion, warm rosy undertone on cheeks, full lips natural brown-pink. "
    "Hair: voluminous curly afro, deep dark brown-black. "
    "Eyes: bright white sclera, dark brown irises, sparkle catchlight highlight, thick dark lashes. "
    "Varsity jacket: WHITE satin body, BLACK patent leather sleeves, black ribbed waistband and cuffs. "
    "White jogger pants, black side stripes, small red logo on left thigh. "
    "Jordan 1 patent sneakers: white patent base, black overlays, tiny red ankle detail, white laces. "
    "Pixar cartoon realism, clean vibrant colors."
)

NEGATIVE_PROMPT = (
    "red jacket, red hoodie, red varsity jacket, red body, red chest panel, red torso, "
    "red front panel, red back panel, red fabric on jacket, "
    "gray skin, pale skin, ashy skin, flat shading, photorealistic skin, "
    "blurry textures, low quality, watermark"
)

POLL_INTERVAL = 15  # seconds
MAX_WAIT = 900  # 15 minutes max


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def headers() -> dict:
    return {"Authorization": f"Bearer {API_KEY}"}


def json_headers() -> dict:
    return {**headers(), "Content-Type": "application/json"}


def check_auth() -> None:
    if not API_KEY:
        sys.exit("[ERROR] MESHY_API_KEY not set in .env")

    # Quick auth check — list recent tasks
    r = requests.get(f"{BASE_URL}/openapi/v2/text-to-3d", headers=headers(), timeout=10)
    if r.status_code == 401:
        sys.exit("[ERROR] Meshy API key invalid or expired")
    print("[OK] Authenticated with Meshy API")


def model_url_from_file(glb_path: Path) -> str:
    """
    Encode a local GLB as a base64 Data URI.
    Meshy accepts this directly in model_url — no upload endpoint needed.
    """
    size_kb = glb_path.stat().st_size // 1024
    print(f"[1/4] Encoding {glb_path.name} ({size_kb} KB) as base64 Data URI...")
    with open(glb_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    data_uri = f"data:model/gltf-binary;base64,{encoded}"
    print(f"[OK] Encoded ({len(data_uri) // 1024} KB payload)")
    return data_uri


def create_texture_task(model_url: str) -> str:
    """Submit the text-to-texture job and return the task ID."""
    print("[2/4] Submitting text-to-texture task...")

    payload = {
        "model_url": model_url,
        "text_style_prompt": TEXTURE_PROMPT,
        "negative_prompt": NEGATIVE_PROMPT,
        "ai_model": "meshy-6",
        "enable_original_uv": True,
        "enable_pbr": True,  # albedo + metallic/roughness + normal maps
    }

    r = requests.post(
        f"{BASE_URL}/openapi/v1/retexture",
        headers=json_headers(),
        json=payload,
        timeout=120,  # large base64 payload needs extra time
    )

    if r.status_code not in (200, 201, 202):
        sys.exit(f"[ERROR] text-to-texture failed ({r.status_code}): {r.text[:300]}")

    task_id = r.json().get("result") or r.json().get("id", "")
    if not task_id:
        sys.exit(f"[ERROR] No task ID in response: {r.json()}")

    print(f"[OK] Task created: {task_id}")
    return task_id


def poll_task(task_id: str) -> dict:
    """Poll until SUCCEEDED or FAILED."""
    print(
        f"[3/4] Waiting for textures (up to {MAX_WAIT // 60} min, polling every {POLL_INTERVAL}s)..."
    )

    elapsed = 0
    while elapsed < MAX_WAIT:
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

        r = requests.get(
            f"{BASE_URL}/openapi/v1/retexture/{task_id}",
            headers=headers(),
            timeout=15,
        )
        if r.status_code != 200:
            print(f"  [WARN] Status check returned {r.status_code}, retrying...")
            continue

        data = r.json()
        status = data.get("status", "PENDING")
        progress = data.get("progress", 0)

        print(f"  [{elapsed:>4}s] {status} — {progress}%")

        if status == "SUCCEEDED":
            return data
        if status in ("FAILED", "EXPIRED"):
            error = data.get("task_error", {})
            sys.exit(f"[ERROR] Task {status}: {error}")

    sys.exit("[ERROR] Timed out waiting for texture task")


def download_outputs(task_data: dict, glb_path: Path) -> None:
    """Download textured GLB and PBR maps to OUTPUT_DIR."""
    print("[4/4] Downloading textured model...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = "skyyrose-mascot-3d"

    model_urls: dict = task_data.get("model_urls", {})
    texture_urls: dict = task_data.get("texture_urls", [])
    thumbnail_url: str = task_data.get("thumbnail_url", "")

    def download(url: str, dest: Path) -> None:
        if not url:
            return
        try:
            urllib.request.urlretrieve(url, dest)
            print(f"  Saved: {dest.name} ({dest.stat().st_size // 1024} KB)")
        except Exception as e:
            print(f"  [WARN] Could not download {dest.name}: {e}")

    # Textured GLB (primary output)
    glb_url = model_urls.get("glb", "")
    download(glb_url, OUTPUT_DIR / f"{stem}-textured.glb")

    # FBX if available
    fbx_url = model_urls.get("fbx", "")
    if fbx_url:
        download(fbx_url, OUTPUT_DIR / f"{stem}-textured.fbx")

    # PBR texture maps
    if isinstance(texture_urls, list):
        for i, tex in enumerate(texture_urls):
            base_color = tex.get("base_color", "")
            roughness = tex.get("roughness", "")
            normal = tex.get("normal", "")
            metallic = tex.get("metallic", "")
            download(base_color, OUTPUT_DIR / f"{stem}-albedo.png")
            download(roughness, OUTPUT_DIR / f"{stem}-roughness.png")
            download(normal, OUTPUT_DIR / f"{stem}-normal.png")
            download(metallic, OUTPUT_DIR / f"{stem}-metallic.png")

    # Thumbnail preview
    if thumbnail_url:
        download(thumbnail_url, OUTPUT_DIR / f"{stem}-preview.png")

    print(f"\n[DONE] Files saved to: {OUTPUT_DIR}/")
    print(f"  Main model: {stem}-textured.glb")
    print("  Use in Three.js with GLTFLoader — MeshStandardMaterial auto-picks PBR maps")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Texture SkyyRose GLB via Meshy")
    parser.add_argument("--glb", type=Path, default=DEFAULT_GLB, help="Path to source GLB")
    args = parser.parse_args()

    glb_path: Path = args.glb
    if not glb_path.exists():
        sys.exit(f"[ERROR] GLB not found: {glb_path}")

    check_auth()
    model_url = model_url_from_file(glb_path)
    task_id = create_texture_task(model_url)
    task_data = poll_task(task_id)
    download_outputs(task_data, glb_path)


if __name__ == "__main__":
    main()
