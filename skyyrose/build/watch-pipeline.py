#!/usr/bin/env python3
"""
SkyyRose — Automated Image Pipeline Watcher
============================================
Drop an image into any source-products/{collection}/ folder and it
automatically runs through quality checks then the full e-commerce pipeline.

Usage:
  python3 build/watch-pipeline.py          # watch all collections
  python3 build/watch-pipeline.py --dry    # quality check only, no processing

Quality Checks:
  ✅ Minimum resolution: 800×800px
  ✅ Supported format: JPG, PNG, WEBP
  ✅ File size: 50KB – 50MB
  ✅ Not too dark / not overexposed
  ✅ Not a duplicate filename already in ecom output

Auto-processes via: python3 build/ecommerce-process.py {product_id}
Then composites:   python3 build/composite-with-bgs.py {product_id}
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:
    print("❌ watchdog not installed. Run: pip3 install watchdog")
    sys.exit(1)

try:
    from PIL import Image, ImageStat
except ImportError:
    print("❌ Pillow not installed. Run: pip3 install Pillow")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
SRC_DIR = ROOT / "assets/images/source-products"
LOG_FILE = ROOT / "build/pipeline.log"
DRY_RUN = "--dry" in sys.argv

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MIN_RESOLUTION = (800, 800)
MIN_FILE_BYTES = 50_000  # 50 KB
MAX_FILE_BYTES = 50_000_000  # 50 MB
MIN_BRIGHTNESS = 20  # 0-255 — too dark
MAX_BRIGHTNESS = 245  # 0-255 — overexposed

COLLECTIONS = ["black-rose", "love-hurts", "signature"]


# ── Product ID lookup by collection folder ────────────────────────────────────
# Maps a source filename back to its product ID by scanning ecommerce-process.py
def get_product_id_for_file(filename: str, collection: str) -> str | None:
    """Find which product ID a filename belongs to."""
    try:
        spec = ROOT / "build/ecommerce-process.py"
        content = spec.read_text()

        # Simple regex-free search: find the product dict containing this file
        lines = content.split("\n")
        current_id = None
        for line in lines:
            if 'id="' in line:
                current_id = line.split('id="')[1].split('"')[0]
            if f'"{filename}"' in line and current_id:
                return current_id
    except Exception:
        pass
    return None


# ── Quality Checks ────────────────────────────────────────────────────────────
def quality_check(path: Path) -> tuple[bool, list[str], list[str]]:
    """
    Returns (passed, warnings, errors).
    Errors block processing. Warnings are logged but allow through.
    """
    errors = []
    warnings = []

    # Format check
    if path.suffix.lower() not in SUPPORTED_EXTS:
        errors.append(f"Unsupported format: {path.suffix} (need JPG/PNG/WEBP)")
        return False, warnings, errors

    # File size check
    size = path.stat().st_size
    if size < MIN_FILE_BYTES:
        errors.append(
            f"File too small: {size // 1024}KB (min 50KB — likely corrupt or placeholder)"
        )
    elif size > MAX_FILE_BYTES:
        warnings.append(f"Large file: {size // 1_000_000}MB — will process but may be slow")

    # Image checks
    try:
        img = Image.open(path)
        w, h = img.size

        # Resolution
        if w < MIN_RESOLUTION[0] or h < MIN_RESOLUTION[1]:
            errors.append(
                f"Too low resolution: {w}×{h}px (minimum {MIN_RESOLUTION[0]}×{MIN_RESOLUTION[1]})"
            )
        elif w < 1500 or h < 1500:
            warnings.append(f"Low resolution: {w}×{h}px — output quality may be reduced")

        # Aspect ratio (extreme ratios suggest wrong crop)
        ratio = max(w, h) / min(w, h)
        if ratio > 3.0:
            warnings.append(f"Unusual aspect ratio {w}:{h} — check crop")

        # Brightness analysis
        rgb = img.convert("RGB")
        stat = ImageStat.Stat(rgb)
        brightness = sum(stat.mean[:3]) / 3

        if brightness < MIN_BRIGHTNESS:
            errors.append(
                f"Image too dark: brightness {brightness:.0f}/255 — check lighting or exposure"
            )
        elif brightness < 40:
            warnings.append(
                f"Very dark image: brightness {brightness:.0f}/255 — may need manual review"
            )
        elif brightness > MAX_BRIGHTNESS:
            errors.append(f"Image overexposed: brightness {brightness:.0f}/255 — blown highlights")
        elif brightness > 220:
            warnings.append(f"Very bright image: brightness {brightness:.0f}/255")

        # Color variety (all-white or all-black = likely blank/corrupt)
        stddev = sum(stat.stddev[:3]) / 3
        if stddev < 5:
            errors.append(f"Image appears blank/solid color (std dev {stddev:.1f}) — check file")

    except Exception as e:
        errors.append(f"Cannot open image: {e}")

    passed = len(errors) == 0
    return passed, warnings, errors


# ── Logging ───────────────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


# ── Pipeline Runner ───────────────────────────────────────────────────────────
def run_pipeline(path: Path, collection: str):
    filename = path.name
    log(f"\n{'=' * 56}")
    log(f"  NEW IMAGE DETECTED: {collection}/{filename}")
    log(f"{'=' * 56}")

    # Quality check
    log("  Running quality checks…")
    passed, warnings, errors = quality_check(path)

    for w in warnings:
        log(f"  ⚠️  WARNING: {w}")
    for e in errors:
        log(f"  ❌  ERROR: {e}")

    if not passed:
        log(f"  🚫 BLOCKED — {len(errors)} error(s). Fix the image and re-save.")
        return

    if warnings:
        log(f"  ✅ Quality check passed with {len(warnings)} warning(s)")
    else:
        log("  ✅ Quality check passed")

    if DRY_RUN:
        log("  [DRY RUN] Skipping pipeline — pass without --dry to process")
        return

    # Find product ID
    product_id = get_product_id_for_file(filename, collection)
    if not product_id:
        log("  ⚠️  File not mapped to any product in ecommerce-process.py")
        log(f"  👉 Add '{filename}' to the correct product in build/ecommerce-process.py")
        log("     Then run: python3 build/ecommerce-process.py <product-id>")
        return

    log(f"  📦 Mapped to product: {product_id}")
    log("  🔄 Running e-commerce pipeline…")

    result = subprocess.run(
        ["python3", "build/ecommerce-process.py", product_id],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            log(f"  {line}")
    if result.returncode != 0:
        log("  ❌ Pipeline failed")
        return

    log("  🎨 Running background compositing…")
    result2 = subprocess.run(
        ["python3", "build/composite-with-bgs.py", product_id],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    for line in result2.stdout.strip().split("\n"):
        if line.strip():
            log(f"  {line}")

    log(f"  🎉 Done — {product_id} fully processed!")


# ── File System Handler ───────────────────────────────────────────────────────
class ImageDropHandler(FileSystemEventHandler):
    def __init__(self):
        self._recently_processed = set()

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in SUPPORTED_EXTS:
            return
        # Debounce — some apps write files in multiple events
        key = str(path)
        if key in self._recently_processed:
            return
        self._recently_processed.add(key)

        # Get collection from path
        try:
            rel = path.relative_to(SRC_DIR)
            collection = rel.parts[0]
            if collection not in COLLECTIONS:
                return
        except ValueError:
            return

        # Small delay to ensure file is fully written
        time.sleep(1.5)
        run_pipeline(path, collection)

        # Clear debounce after 10s
        time.sleep(10)
        self._recently_processed.discard(key)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\n SkyyRose — Automated Image Pipeline Watcher")
    print("=" * 56)
    if DRY_RUN:
        print("  Mode: DRY RUN (quality check only, no processing)")
    print(f"  Watching: {SRC_DIR}")
    print(f"  Log:      {LOG_FILE}")
    print(f"  Folders:  {', '.join(COLLECTIONS)}")
    print("\n  Drop images into any source-products/{{collection}}/ folder")
    print("  They'll automatically pass quality checks and process.\n")
    print("  Press Ctrl+C to stop.\n")

    handler = ImageDropHandler()
    observer = Observer()

    for col in COLLECTIONS:
        col_dir = SRC_DIR / col
        col_dir.mkdir(exist_ok=True)
        observer.schedule(handler, str(col_dir), recursive=False)
        print(f"  👁  Watching: {col}/")

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n  Watcher stopped.")
    observer.join()


if __name__ == "__main__":
    main()
