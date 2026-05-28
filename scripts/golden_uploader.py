"""Local single-file FastAPI app for uploading replacement SKU golden photos.

Use case: the SKU-to-golden alignment audit flagged mismatched goldens
(e.g. lh-005 catalog says bomber jacket, but the on-disk golden is a fanny
pack). Use this app to drag-and-drop the correct product photo for each
mismatched SKU; it overwrites
``skyyrose/elite_studio/assets/golden/{sku}/front.jpg`` and backs up the
prior file as ``front.jpg.bak.<unix-ts>``.

Run:
    .venv/bin/python scripts/golden_uploader.py
    open http://127.0.0.1:8765

Stop with Ctrl-C. No external services; pure local FastAPI.
"""

from __future__ import annotations

import logging
import shutil
import sys
import time
from io import BytesIO
from pathlib import Path

# Bootstrap project root onto sys.path so this standalone script can import
# from skyyrose.core.* — only needed because uploader runs via
# `.venv/bin/python scripts/golden_uploader.py`, not as `python -m`.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile  # noqa: E402
from fastapi.responses import HTMLResponse, JSONResponse  # noqa: E402
from PIL import Image  # noqa: E402

from skyyrose.core.paths import (
    CATALOG_CSV,
)
from skyyrose.core.paths import DOSSIERS_DIR as DOSSIER_ROOT  # noqa: E402
from skyyrose.core.paths import GOLDEN_DIR as GOLDEN_ROOT
from skyyrose.core.paths import (
    golden_path,
)

logger = logging.getLogger(__name__)

REPO_ROOT = _REPO_ROOT

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_PIL_FORMATS = {"JPEG", "PNG", "WEBP"}
PORT = 8765

app = FastAPI(title="SkyyRose Golden Uploader", version="1.0.0")


def _list_skus() -> list[str]:
    """Return sorted list of SKU folder names under the golden root."""
    if not GOLDEN_ROOT.is_dir():
        return []
    return sorted(p.name for p in GOLDEN_ROOT.iterdir() if p.is_dir())


def _load_catalog() -> list[dict[str, str]]:
    """Return the full catalog as a list of ``{sku, name, collection, dossier_slug}`` dicts.

    Uses csv module to handle quoted name fields with embedded commas.
    Returns rows in catalog order so the UI mirrors the source file.
    """
    import csv

    if not CATALOG_CSV.is_file():
        return []
    out: list[dict[str, str]] = []
    with CATALOG_CSV.open("r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            sku = (row.get("sku") or "").strip()
            if not sku:
                continue
            out.append(
                {
                    "sku": sku,
                    "name": (row.get("name") or "").strip(),
                    "collection": (row.get("collection") or "").strip(),
                    "dossier_slug": (row.get("dossier_slug") or "").strip(),
                }
            )
    return out


def _current_front_path(sku: str) -> Path | None:
    """Return current front.jpg path for a SKU if present."""
    try:
        candidate = golden_path(sku)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def _safe_target_path(sku: str) -> Path:
    """Validate SKU directory name and return the canonical front.jpg path.

    Defense-in-depth: ``golden_path()`` rejects traversal payloads (``..``,
    ``/``, ``\\``); the extra alphanumeric check below also rejects empty
    strings and stray punctuation that would otherwise pass the helper's
    coarser guard. Creates the per-SKU directory as a side effect.
    """
    if not sku or not sku.replace("-", "").isalnum():
        raise HTTPException(400, f"invalid sku id: {sku!r}")
    try:
        target = golden_path(sku)
    except ValueError as exc:
        raise HTTPException(400, f"invalid sku id: {sku!r}") from exc
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _backup_existing(path: Path) -> Path | None:
    """Move existing file to .bak.<ts>; return the backup path."""
    if not path.is_file():
        return None
    ts = int(time.time())
    backup = path.with_suffix(f".jpg.bak.{ts}")
    shutil.copy2(path, backup)
    return backup


def _save_as_jpeg(image_bytes: bytes, dest: Path) -> tuple[int, int]:
    """Decode upload, save as JPEG at dest. Returns (width, height).

    PIL's detected ``image.format`` is checked against ``ALLOWED_PIL_FORMATS``
    before re-encode to defeat polyglot uploads (e.g., a renamed binary that
    extension-matches but PIL identifies as something else).
    """
    image = Image.open(BytesIO(image_bytes))
    if image.format not in ALLOWED_PIL_FORMATS:
        raise ValueError(
            f"image format {image.format!r} not in allowlist {sorted(ALLOWED_PIL_FORMATS)}"
        )
    if image.mode != "RGB":
        image = image.convert("RGB")
    image.save(dest, format="JPEG", quality=95, optimize=True)
    return image.size


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/skus")
def list_skus_with_catalog() -> JSONResponse:
    """Return every catalog SKU with name, collection, golden state, and dossier.

    Iterates the catalog (authoritative source) so SKUs without a
    ``golden/{sku}/`` directory still surface as upload-target tiles.
    """
    rows = []
    for entry in _load_catalog():
        sku = entry["sku"]
        rows.append(
            {
                "sku": sku,
                "name": entry["name"],
                "collection": entry["collection"],
                "dossier_slug": entry["dossier_slug"],
                "has_front": _current_front_path(sku) is not None,
                "has_dossier": (
                    (DOSSIER_ROOT / f"{entry['dossier_slug']}.md").is_file()
                    if entry["dossier_slug"]
                    else False
                ),
            }
        )
    return JSONResponse(rows)


@app.get("/api/dossier/{sku}")
def dossier(sku: str) -> Response:
    """Return the markdown body of the dossier for a SKU (or 404)."""
    for entry in _load_catalog():
        if entry["sku"] == sku and entry["dossier_slug"]:
            path = DOSSIER_ROOT / f"{entry['dossier_slug']}.md"
            if path.is_file():
                return Response(content=path.read_bytes(), media_type="text/markdown")
            break
    raise HTTPException(404, f"no dossier for {sku}")


@app.get("/api/preview/{sku}")
def preview(sku: str) -> Response:
    """Return the current front.jpg for a SKU (or 404)."""
    path = _current_front_path(sku)
    if path is None:
        raise HTTPException(404, f"no front.jpg for {sku}")
    return Response(content=path.read_bytes(), media_type="image/jpeg")


@app.post("/api/upload")
async def upload(
    sku: str = Form(...),
    file: UploadFile = File(...),
) -> JSONResponse:
    """Replace ``golden/{sku}/front.jpg`` with the uploaded image.

    The existing file is moved to ``front.jpg.bak.<unix-ts>`` so the prior
    state is recoverable. The upload is normalized to JPEG (quality 95).
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext and ext not in ALLOWED_EXT:
        raise HTTPException(415, f"unsupported file type: {ext} (allowed: {sorted(ALLOWED_EXT)})")

    body = await file.read()
    if not body:
        raise HTTPException(400, "empty file")
    if len(body) > 25 * 1024 * 1024:
        raise HTTPException(413, "file > 25 MB")

    dest = _safe_target_path(sku)
    backup = _backup_existing(dest)
    try:
        width, height = _save_as_jpeg(body, dest)
    except Exception as exc:
        if backup is not None:
            shutil.copy2(backup, dest)
        raise HTTPException(400, f"could not decode image: {exc}") from exc

    return JSONResponse(
        {
            "ok": True,
            "sku": sku,
            "dest": str(dest.relative_to(REPO_ROOT)),
            "backup": str(backup.relative_to(REPO_ROOT)) if backup else None,
            "size_bytes": dest.stat().st_size,
            "dimensions": [width, height],
        }
    )


# ---------------------------------------------------------------------------
# HTML UI
# ---------------------------------------------------------------------------


_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>SkyyRose Golden Uploader</title>
<style>
  :root {
    --bg: #0a0a0a;
    --panel: #141414;
    --border: #2a2a2a;
    --text: #f5f5f5;
    --muted: #999;
    --accent: #B76E79; /* rose gold */
    --ok: #6fcf97;
    --bad: #eb5757;
  }
  * { box-sizing: border-box; }
  body {
    background: var(--bg); color: var(--text); margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  }
  header { padding: 24px 32px; border-bottom: 1px solid var(--border); }
  h1 { margin: 0; font-weight: 500; letter-spacing: 0.02em; }
  .subtitle { color: var(--muted); font-size: 13px; margin-top: 6px; }
  main { padding: 24px 32px; max-width: 1200px; margin: 0 auto; }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }
  .card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  .card-img {
    aspect-ratio: 1;
    background: #1a1a1a no-repeat center / contain;
    border-bottom: 1px solid var(--border);
    position: relative;
  }
  .card-img.empty::before {
    content: "no golden on disk — upload";
    position: absolute; inset: 0;
    display: grid; place-items: center;
    color: var(--muted); font-size: 12px;
  }
  .card-img.empty { background-color: #1f1313; }
  .card-body { padding: 12px 14px; flex: 1; display: flex; flex-direction: column; }
  .sku-row { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
  .sku { color: var(--accent); font-family: ui-monospace, monospace; font-size: 13px; }
  .badge {
    font-size: 10px; padding: 2px 6px; border-radius: 3px;
    background: var(--border); color: var(--muted); text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .badge.black-rose { background: #2a1218; color: #d4a8b4; }
  .badge.love-hurts { background: #2a1212; color: #e89090; }
  .badge.signature { background: #2a2618; color: #e8c890; }
  .badge.kids { background: #18222a; color: #90b4d4; }
  .dossier-link {
    margin-top: 6px; font-size: 11px; color: var(--muted);
    text-decoration: none; display: inline-block;
  }
  .dossier-link:hover { color: var(--accent); }
  .dossier-link.missing { color: var(--bad); cursor: default; pointer-events: none; }
  .name { font-size: 13px; margin-top: 4px; color: var(--text); min-height: 32px; }
  .filter-bar {
    margin-bottom: 16px; display: flex; gap: 8px; flex-wrap: wrap;
    font-size: 12px;
  }
  .filter-btn {
    padding: 6px 12px; background: var(--panel); border: 1px solid var(--border);
    color: var(--muted); border-radius: 16px; cursor: pointer;
    font: inherit;
  }
  .filter-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
  .drop {
    margin-top: 10px;
    border: 1px dashed var(--border);
    border-radius: 6px;
    padding: 10px;
    text-align: center;
    font-size: 12px;
    color: var(--muted);
    cursor: pointer;
    transition: border-color .15s, color .15s;
  }
  .drop:hover, .drop.dragging { border-color: var(--accent); color: var(--accent); }
  .drop input { display: none; }
  .status { margin-top: 8px; font-size: 11px; min-height: 14px; }
  .status.ok { color: var(--ok); }
  .status.bad { color: var(--bad); }
</style>
</head>
<body>
<header>
  <h1>SkyyRose Golden Uploader</h1>
  <div class="subtitle">
    Drop a replacement photo on any tile to overwrite that SKU's <code>front.jpg</code>.
    Prior file is backed up to <code>front.jpg.bak.&lt;ts&gt;</code>.
  </div>
</header>
<main>
  <div class="filter-bar" id="filter-bar"></div>
  <div id="grid" class="grid"></div>
</main>
<script>
const grid = document.getElementById('grid');
const filterBar = document.getElementById('filter-bar');
let allRows = [];
let currentFilter = 'all';

const FILTERS = [
  { id: 'all',        label: 'All' },
  { id: 'no-golden',  label: 'Missing golden' },
  { id: 'black-rose', label: 'Black Rose' },
  { id: 'love-hurts', label: 'Love Hurts' },
  { id: 'signature',  label: 'Signature' },
  { id: 'kids-capsule', label: 'Kids' },
];

function applyFilter() {
  let rows = allRows;
  if (currentFilter === 'no-golden') {
    rows = rows.filter((r) => !r.has_front);
  } else if (currentFilter !== 'all') {
    rows = rows.filter((r) => r.collection === currentFilter);
  }
  grid.innerHTML = '';
  rows.forEach(renderTile);
}

function renderFilterBar() {
  filterBar.innerHTML = '';
  FILTERS.forEach((f) => {
    const btn = document.createElement('button');
    btn.className = 'filter-btn' + (f.id === currentFilter ? ' active' : '');
    btn.textContent = f.label;
    btn.onclick = () => { currentFilter = f.id; renderFilterBar(); applyFilter(); };
    filterBar.appendChild(btn);
  });
}

async function load() {
  const r = await fetch('/api/skus');
  allRows = await r.json();
  renderFilterBar();
  applyFilter();
}

function renderTile(row) {
  const card = document.createElement('div');
  card.className = 'card';

  const img = document.createElement('div');
  img.className = 'card-img' + (row.has_front ? '' : ' empty');
  if (row.has_front) {
    img.style.backgroundImage = `url('/api/preview/${row.sku}?t=${Date.now()}')`;
  }
  card.appendChild(img);

  const body = document.createElement('div');
  body.className = 'card-body';

  const collShort = (row.collection || '').replace('kids-capsule', 'kids');
  const collBadge = row.collection
    ? `<span class="badge ${row.collection.replace('-capsule','')}">${collShort}</span>`
    : '';
  const dossierClass = row.has_dossier ? '' : ' missing';
  const dossierHref = row.has_dossier ? `/api/dossier/${row.sku}` : '#';
  const dossierLabel = row.has_dossier
    ? `dossier: ${row.dossier_slug}`
    : 'no dossier';

  body.innerHTML =
    `<div class="sku-row"><div class="sku">${row.sku}</div>${collBadge}</div>` +
    `<div class="name">${row.name}</div>` +
    `<a class="dossier-link${dossierClass}" href="${dossierHref}" target="_blank" rel="noopener">${dossierLabel}</a>`;

  const drop = document.createElement('label');
  drop.className = 'drop';
  drop.textContent = 'drop image or click to upload';
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  drop.appendChild(input);

  const status = document.createElement('div');
  status.className = 'status';

  const upload = async (file) => {
    if (!file) return;
    status.textContent = 'uploading…';
    status.className = 'status';
    const fd = new FormData();
    fd.append('sku', row.sku);
    fd.append('file', file);
    try {
      const resp = await fetch('/api/upload', { method: 'POST', body: fd });
      const data = await resp.json();
      if (!resp.ok) {
        status.textContent = data.detail || 'upload failed';
        status.className = 'status bad';
        return;
      }
      status.textContent = `saved (${data.dimensions[0]}×${data.dimensions[1]}, ${(data.size_bytes/1024).toFixed(0)}KB)`;
      status.className = 'status ok';
      img.classList.remove('empty');
      img.style.backgroundImage = `url('/api/preview/${row.sku}?t=${Date.now()}')`;
    } catch (e) {
      status.textContent = 'network error';
      status.className = 'status bad';
    }
  };

  input.addEventListener('change', () => upload(input.files[0]));

  ['dragenter', 'dragover'].forEach((evt) =>
    drop.addEventListener(evt, (e) => {
      e.preventDefault();
      drop.classList.add('dragging');
    })
  );
  ['dragleave', 'drop'].forEach((evt) =>
    drop.addEventListener(evt, (e) => {
      e.preventDefault();
      drop.classList.remove('dragging');
    })
  );
  drop.addEventListener('drop', (e) => upload(e.dataTransfer.files[0]));

  body.appendChild(drop);
  body.appendChild(status);
  card.appendChild(body);
  grid.appendChild(card);
}

load();
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse(_INDEX_HTML)


def main() -> None:
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    print(f"SkyyRose Golden Uploader → http://127.0.0.1:{PORT}")
    print(f"Writing to: {GOLDEN_ROOT}")
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
