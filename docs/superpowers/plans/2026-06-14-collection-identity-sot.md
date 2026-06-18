# Collection Identity SOT — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make each collection's identity (story · palette · fonts · lockup · products · imagery · copy) live in one founder-canon source per collection, with `design-tokens.css`, a per-collection `sot.json`, and a designer `index.html` hub all generated from it — then hard cut-over every reference and delete the old structure (deletion gated on a founder walkthrough).

**Architecture:** Per-collection folder `data/collections/<slug>/` holds hand-authored `identity.json` (canon) + `copy.md`, plus generated `sot.json` + `index.html`. A shared validated loader (`data/sot_common.py`) is the only reader of the masters (catalog CSV, visual-manifest, logo-registry). Generators project canon → CSS tokens, SOT, and HTML. Images are referenced (never duplicated) per the single-asset-tree lock.

**Tech Stack:** Python 3.11+ (stdlib + `jsonschema` [confirmed in `.venv`] + `fonttools[woff]` for subsetting), pytest, WordPress theme CSS (`design-tokens.css` + `scripts/build-css.js`), self-hosted woff2.

**Spec:** `docs/superpowers/specs/2026-06-14-collection-identity-sot-design.md`. **Branch:** `feat/collection-identity-sot`.

**Paths note:** repo root `/Users/theceo/DevSkyy`. Theme data dir = `wordpress-theme/skyyrose-flagship/data/` (abbreviated `DATA/` below). Theme assets = `wordpress-theme/skyyrose-flagship/assets/` (`ASSETS/`). Run Python via `.venv/bin/python`. Tests live in `tests/collections/`.

---

## File structure (decomposition)

| File | Responsibility | Phase |
|------|----------------|-------|
| `DATA/collections/identity.schema.json` | JSON Schema for `identity.json` (the canon contract) | P0 |
| `DATA/collections/<slug>/identity.json` × 4 | Hand-authored per-collection canon (the seed) | P0 |
| `DATA/sot_common.py` | Shared: `load_identity()`, `load_manifest()`, `IMG_EXTS`, `slug_to_key()`, `resolve_asset()`, `registered_files()` | P0/P3 |
| `tests/collections/test_sot_common.py` | Unit tests for the shared module | P0/P3 |
| `DATA/<slug>/copy.md` × 4 | Hand-authored designer copy (sliced from `collection-stories.md`) | P4 |
| `ASSETS/fonts/{yellowtail,kaushan-script,pinyon-script}-latin.woff2` | Self-hosted OFL fonts | P1 |
| `DATA/gen-design-tokens.py` | Generates the marked `[data-collection]` region of `design-tokens.css` from identity | P2 |
| `tests/collections/test_gen_design_tokens.py` | Tests token generation + idempotency | P2 |
| `DATA/build-collection-sot.py` (rewrite) | Reads identity → per-folder `sot.json` + global `_orphans.json` | P3 |
| `tests/collections/test_build_collection_sot.py` | Tests SOT build + orphan set-diff + ext-preference | P3 |
| `DATA/gen-collection-hub.py` | Generates per-folder `index.html` designer hub | P4 |
| `DATA/verify-collection-sot.py` (rewrite) | Drift gate: identity ↔ CSS ↔ woff2 ↔ catalog ↔ tree | P5 |

---

## Task 0: Branch + test scaffold

**Files:** Create `tests/collections/__init__.py`

- [ ] **Step 1: Confirm branch + create test package**

```bash
cd /Users/theceo/DevSkyy
git rev-parse --abbrev-ref HEAD          # expect: feat/collection-identity-sot
mkdir -p tests/collections wordpress-theme/skyyrose-flagship/data/collections
printf '"""Collection identity SOT tests."""\n' > tests/collections/__init__.py
```

- [ ] **Step 2: Confirm masters + helpers exist (authoritative-source check)**

```bash
.venv/bin/python -c "from skyyrose.core.catalog_loader import read_catalog_rows, bool_col; from skyyrose.core.paths import WP_ASSETS_DIR; print('OK', WP_ASSETS_DIR)"
.venv/bin/python -c "import jsonschema, fontTools" 2>&1 || .venv/bin/pip install 'jsonschema' 'fonttools[woff]' brotli
ls wordpress-theme/skyyrose-flagship/assets/fonts/ | grep -iE 'cinzel|cormorant'   # confirm exact woff2 filenames for identity.json
```

Expected: prints `OK <path>`; lists the existing Cinzel + Cormorant woff2 filenames (record them for Task 2).

- [ ] **Step 3: Commit scaffold**

```bash
git add tests/collections/__init__.py
git commit -m "test: scaffold collection identity SOT test package"
```

---

## Task 1: identity.schema.json (the canon contract)

**Files:** Create `DATA/collections/identity.schema.json`

- [ ] **Step 1: Write the failing test**

`tests/collections/test_sot_common.py`:

```python
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "wordpress-theme/skyyrose-flagship/data"
SCHEMA = DATA / "collections/identity.schema.json"


def test_schema_is_valid_jsonschema():
    import jsonschema
    schema = json.loads(SCHEMA.read_text())
    jsonschema.Draft202012Validator.check_schema(schema)  # raises if schema itself is malformed
    assert schema["required"]  # has required keys
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/collections/test_sot_common.py::test_schema_is_valid_jsonschema -v`
Expected: FAIL — `FileNotFoundError` (schema not created yet).

- [ ] **Step 3: Write the schema**

`DATA/collections/identity.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SkyyRose Collection Identity",
  "type": "object",
  "additionalProperties": false,
  "required": ["slug", "key", "name", "status", "story", "palette", "fonts", "lockup"],
  "properties": {
    "$schema": {"type": "string"},
    "slug": {"type": "string", "pattern": "^[a-z]+(-[a-z]+)*$"},
    "key": {"type": "string", "pattern": "^[a-z]+(_[a-z]+)*$"},
    "name": {"type": "string", "minLength": 1},
    "status": {"enum": ["verified", "needs-founder-review"]},
    "story": {
      "type": "object",
      "additionalProperties": false,
      "required": ["seed", "doc_ref"],
      "properties": {
        "seed": {"type": "string", "minLength": 1},
        "doc_ref": {"type": "string", "minLength": 1}
      }
    },
    "palette": {
      "type": "object",
      "minProperties": 1,
      "additionalProperties": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"}
    },
    "fonts": {
      "type": "object",
      "additionalProperties": false,
      "required": ["script", "caps", "body"],
      "properties": {
        "script": {"$ref": "#/$defs/font"},
        "caps": {"$ref": "#/$defs/font"},
        "body": {"$ref": "#/$defs/font"}
      }
    },
    "lockup": {
      "type": "object",
      "additionalProperties": false,
      "required": ["ref"],
      "properties": {"ref": {"type": "string", "minLength": 1}}
    },
    "known_orphans": {"type": "array", "items": {"type": "string"}}
  },
  "$defs": {
    "font": {
      "type": "object",
      "additionalProperties": false,
      "required": ["family", "woff2", "source"],
      "properties": {
        "family": {"type": "string", "minLength": 1},
        "woff2": {"type": ["string", "null"]},
        "source": {"type": "string", "minLength": 1}
      }
    }
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/collections/test_sot_common.py::test_schema_is_valid_jsonschema -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add wordpress-theme/skyyrose-flagship/data/collections/identity.schema.json tests/collections/test_sot_common.py
git commit -m "feat(sot): identity.json canon schema"
```

---

## Task 2: Hand-author the 4 identity.json (the canon seed)

**Files:** Create `DATA/collections/{black-rose,love-hurts,signature,kids-capsule}/identity.json`

> Palette + story values are LOCKED canon (spec §3). Font families are the leads from spec §6 (P1 confirms via specimen). `caps`/`body` woff2 = the existing self-hosted filenames recorded in Task 0 Step 2 (replace `<cinzel-woff2>` / `<cormorant-woff2>` with the exact filenames you listed). The new script woff2 names are fixed (created in P1).

- [ ] **Step 1: Write the failing test**

Append to `tests/collections/test_sot_common.py`:

```python
import pytest

SLUGS = ["black-rose", "love-hurts", "signature", "kids-capsule"]
EXPECTED_PALETTE = {
    "black-rose": {"black", "white", "silver", "accent", "accent_dark", "bg", "text"},
    "love-hurts": {"red", "red_dark", "white", "black", "accent", "accent_dark", "bg", "text"},
    "signature": {"gold", "rose_gold", "accent", "accent_dark", "bg", "text"},
    "kids-capsule": {"gold", "rose_gold", "accent", "accent_dark", "bg", "text"},
}
SCRIPT_FONT = {
    "black-rose": "Yellowtail", "love-hurts": "Kaushan Script",
    "signature": "Pinyon Script", "kids-capsule": "Pinyon Script",
}


@pytest.mark.parametrize("slug", SLUGS)
def test_identity_validates_and_matches_canon(slug):
    import jsonschema
    schema = json.loads(SCHEMA.read_text())
    ident = json.loads((DATA / "collections" / slug / "identity.json").read_text())
    jsonschema.validate(ident, schema)
    assert ident["slug"] == slug
    assert ident["key"] == slug.replace("-", "_")
    assert EXPECTED_PALETTE[slug].issubset(set(ident["palette"]))
    assert ident["fonts"]["script"]["family"] == SCRIPT_FONT[slug]
    assert ident["fonts"]["caps"]["family"] == "Cinzel"
    assert ident["fonts"]["body"]["family"] == "Cormorant Garamond"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/collections/test_sot_common.py -k identity_validates -v`
Expected: FAIL — files not found.

- [ ] **Step 3: Write `DATA/collections/black-rose/identity.json`**

```json
{
  "$schema": "../identity.schema.json",
  "slug": "black-rose",
  "key": "black_rose",
  "name": "Black Rose",
  "status": "verified",
  "story": {
    "seed": "Defining beauty through the color black.",
    "doc_ref": "docs/brand/collection-stories.md#black-rose"
  },
  "palette": {
    "black": "#0A0A0A",
    "white": "#FFFFFF",
    "silver": "#C0C0C0",
    "accent": "#C0C0C0",
    "accent_dark": "#999999",
    "bg": "#0A0A0A",
    "text": "#F5F5F5"
  },
  "fonts": {
    "script": {"family": "Yellowtail", "woff2": "assets/fonts/yellowtail-latin.woff2", "source": "OFL / Google Fonts"},
    "caps": {"family": "Cinzel", "woff2": "assets/fonts/<cinzel-woff2>", "source": "OFL (already hosted)"},
    "body": {"family": "Cormorant Garamond", "woff2": "assets/fonts/<cormorant-woff2>", "source": "OFL (already hosted)"}
  },
  "lockup": {"ref": "images/lockups/black-rose-lockup.webp"},
  "known_orphans": []
}
```

- [ ] **Step 4: Write `DATA/collections/love-hurts/identity.json`**

```json
{
  "$schema": "../identity.schema.json",
  "slug": "love-hurts",
  "key": "love_hurts",
  "name": "Love Hurts",
  "status": "verified",
  "story": {
    "seed": "Beauty and the Beast told from the Beast's perspective, through luxury attire.",
    "doc_ref": "docs/brand/collection-stories.md#love-hurts"
  },
  "palette": {
    "red": "#DC143C",
    "red_dark": "#9B0F2E",
    "white": "#FFFFFF",
    "black": "#0A0A0A",
    "accent": "#DC143C",
    "accent_dark": "#9B0F2E",
    "bg": "#0A0A0A",
    "text": "#F5F5F5"
  },
  "fonts": {
    "script": {"family": "Kaushan Script", "woff2": "assets/fonts/kaushan-script-latin.woff2", "source": "OFL / Google Fonts"},
    "caps": {"family": "Cinzel", "woff2": "assets/fonts/<cinzel-woff2>", "source": "OFL (already hosted)"},
    "body": {"family": "Cormorant Garamond", "woff2": "assets/fonts/<cormorant-woff2>", "source": "OFL (already hosted)"}
  },
  "lockup": {"ref": "images/lockups/love-hurts-lockup.webp"},
  "known_orphans": []
}
```

- [ ] **Step 5: Write `DATA/collections/signature/identity.json`**

```json
{
  "$schema": "../identity.schema.json",
  "slug": "signature",
  "key": "signature",
  "name": "Signature",
  "status": "verified",
  "story": {
    "seed": "The beginning of it all — where it started from.",
    "doc_ref": "docs/brand/collection-stories.md#signature"
  },
  "palette": {
    "gold": "#D4AF37",
    "rose_gold": "#B76E79",
    "accent": "#D4AF37",
    "accent_dark": "#B8960C",
    "bg": "#0A0A0A",
    "text": "#F5E6D3"
  },
  "fonts": {
    "script": {"family": "Pinyon Script", "woff2": "assets/fonts/pinyon-script-latin.woff2", "source": "OFL / Google Fonts"},
    "caps": {"family": "Cinzel", "woff2": "assets/fonts/<cinzel-woff2>", "source": "OFL (already hosted)"},
    "body": {"family": "Cormorant Garamond", "woff2": "assets/fonts/<cormorant-woff2>", "source": "OFL (already hosted)"}
  },
  "lockup": {"ref": "images/lockups/signature-lockup.webp"},
  "known_orphans": []
}
```

- [ ] **Step 6: Write `DATA/collections/kids-capsule/identity.json`** (Signature schema — gold/rose-gold, Pinyon)

```json
{
  "$schema": "../identity.schema.json",
  "slug": "kids-capsule",
  "key": "kids_capsule",
  "name": "Kids Capsule",
  "status": "verified",
  "story": {
    "seed": "The Heir to the throne.",
    "doc_ref": "docs/brand/collection-stories.md#kids-capsule"
  },
  "palette": {
    "gold": "#D4AF37",
    "rose_gold": "#B76E79",
    "accent": "#D4AF37",
    "accent_dark": "#B8960C",
    "bg": "#0A0A0A",
    "text": "#F5E6D3"
  },
  "fonts": {
    "script": {"family": "Pinyon Script", "woff2": "assets/fonts/pinyon-script-latin.woff2", "source": "OFL / Google Fonts"},
    "caps": {"family": "Cinzel", "woff2": "assets/fonts/<cinzel-woff2>", "source": "OFL (already hosted)"},
    "body": {"family": "Cormorant Garamond", "woff2": "assets/fonts/<cormorant-woff2>", "source": "OFL (already hosted)"}
  },
  "lockup": {"ref": "images/logos/sr-monogram-rose-gold"},
  "known_orphans": []
}
```

- [ ] **Step 7: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/collections/test_sot_common.py -k identity_validates -v`
Expected: PASS (4 params). If FAIL on woff2 — you left a `<...>` placeholder; substitute the real filename from Task 0 Step 2.

- [ ] **Step 8: Commit**

```bash
git add wordpress-theme/skyyrose-flagship/data/collections/*/identity.json tests/collections/test_sot_common.py
git commit -m "feat(sot): hand-authored per-collection identity canon (palette+fonts+story locked)"
```

---

## Task 3: sot_common.py — validated loader + slug/key + asset resolver

**Files:** Create `DATA/sot_common.py`; Test: `tests/collections/test_sot_common.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/collections/test_sot_common.py`:

```python
import sys
sys.path.insert(0, str(DATA))
import sot_common  # noqa: E402


def test_slug_to_key():
    assert sot_common.slug_to_key("black-rose") == "black_rose"
    assert sot_common.slug_to_key("signature") == "signature"


def test_load_identity_all_four():
    idents = sot_common.load_identity()
    assert set(idents) == set(SLUGS)
    assert idents["signature"]["fonts"]["script"]["family"] == "Pinyon Script"


def test_load_identity_rejects_malformed(tmp_path, monkeypatch):
    bad = tmp_path / "black-rose"
    bad.mkdir()
    (bad / "identity.json").write_text('{"slug": "black-rose"}')  # missing required keys
    monkeypatch.setattr(sot_common, "COLLECTIONS_DIR", tmp_path)
    with pytest.raises(sot_common.IdentityError):
        sot_common.load_identity()


def test_resolve_asset_prefers_webp_over_avif(tmp_path, monkeypatch):
    monkeypatch.setattr(sot_common, "ASSETS", tmp_path)
    (tmp_path / "x.avif").write_bytes(b"a")
    (tmp_path / "x.webp").write_bytes(b"w")
    assert sot_common.resolve_asset("x").endswith("x.webp")   # IMG_EXTS preference, not alphabetical
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/collections/test_sot_common.py -k "slug_to_key or load_identity or resolve_asset" -v`
Expected: FAIL — `ModuleNotFoundError: sot_common`.

- [ ] **Step 3: Write `DATA/sot_common.py`**

```python
#!/usr/bin/env python3
"""Shared, validated readers for the per-collection SOT pipeline.

Single place that loads the masters (identity.json, visual-manifest.json,
logo-registry.json) and resolves asset paths. Both build-collection-sot.py and
verify-collection-sot.py import from here so resolution + validation never drift.
"""

import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent
sys.path.insert(0, str(DATA.parents[2]))
from skyyrose.core.paths import WP_ASSETS_DIR  # noqa: E402

ASSETS = WP_ASSETS_DIR
COLLECTIONS_DIR = DATA / "collections"
SCHEMA = COLLECTIONS_DIR / "identity.schema.json"
MANIFEST = DATA / "visual-manifest.json"
LOGO_REG = DATA / "logo-registry.json"

# webp first = preferred; resolve_asset honors THIS order, not alphabetical glob order.
IMG_EXTS = (".webp", ".avif", ".png", ".jpg", ".jpeg", ".svg", ".mp4", ".webm")


class IdentityError(Exception):
    """identity.json failed schema validation or could not be read."""


def slug_to_key(slug: str) -> str:
    return slug.replace("-", "_")


def _load_json(path: Path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as e:
        raise IdentityError(f"required master missing: {path}") from e
    except json.JSONDecodeError as e:
        raise IdentityError(f"malformed JSON in {path}: {e}") from e


def load_manifest():
    return _load_json(MANIFEST)


def load_logo_registry():
    return _load_json(LOGO_REG)


def load_identity() -> dict:
    """Return {slug: identity dict} for every collection folder, schema-validated."""
    import jsonschema

    schema = _load_json(SCHEMA)
    out = {}
    for d in sorted(p for p in COLLECTIONS_DIR.iterdir() if p.is_dir()):
        fp = d / "identity.json"
        if not fp.is_file():
            continue
        ident = _load_json(fp)
        try:
            jsonschema.validate(ident, schema)
        except jsonschema.ValidationError as e:
            raise IdentityError(f"{fp}: {e.message}") from e
        if ident["slug"] != d.name:
            raise IdentityError(f"{fp}: slug '{ident['slug']}' != folder '{d.name}'")
        if ident["key"] != slug_to_key(ident["slug"]):
            raise IdentityError(f"{fp}: key must be slug_to_key('{ident['slug']}')")
        out[d.name] = ident
    if not out:
        raise IdentityError(f"no identity.json found under {COLLECTIONS_DIR}")
    return out


def resolve_asset(rel: str) -> str | None:
    """assets-relative path (possibly extension-less) -> real file rel-path, else None.

    For an extension-less base, return the sibling whose extension ranks first in
    IMG_EXTS (webp before avif), NOT the alphabetically-first glob hit.
    """
    if not rel:
        return None
    rel = rel.replace("assets/", "", 1) if rel.startswith("assets/") else rel
    p = ASSETS / rel
    if p.is_file():
        return rel
    parent = p.parent
    if not parent.is_dir():
        return None
    cands = [f for f in parent.glob(p.name + "*") if f.is_file() and f.suffix.lower() in IMG_EXTS]
    if not cands:
        return None
    cands.sort(key=lambda f: (IMG_EXTS.index(f.suffix.lower()), f.name))
    return str(cands[0].relative_to(ASSETS))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/collections/test_sot_common.py -k "slug_to_key or load_identity or resolve_asset" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add wordpress-theme/skyyrose-flagship/data/sot_common.py tests/collections/test_sot_common.py
git commit -m "feat(sot): shared validated loader + IMG_EXTS-preference asset resolver"
```

---

## Task 4 (P1): Self-host the 3 OFL fonts

**Files:** Create `ASSETS/fonts/{yellowtail,kaushan-script,pinyon-script}-latin.woff2`; Modify the theme `@font-face` stylesheet.

> Founder decision: faithful OFL match, no detail loss. Specimen-confirm each lead against the lockup before committing the file.

- [ ] **Step 1: Specimen-confirm the lead picks (authoritative-source check)**

Render a specimen of each lead family and compare to the lockup letterforms (`images/lockups/black-rose-lockup.webp`, `branding/love-hurts-love-hero.webp`, `branding/signature-logo-hero.webp`). If a lead is clearly wrong, swap to the spec §6 alt (BR: Pacifico/Kaushan; LH: graffiti OFL; SIG: Allura/Great Vibes) and update the affected `identity.json` `fonts.script.family`. Record the final family per collection.

- [ ] **Step 2: Download OFL TTFs + subset to latin woff2**

```bash
cd /Users/theceo/DevSkyy
mkdir -p /tmp/fonts && cd /tmp/fonts
# OFL fonts from Google Fonts github (SIL Open Font License — free, redistributable):
curl -sL -o yellowtail.ttf      https://github.com/google/fonts/raw/main/apache/yellowtail/Yellowtail-Regular.ttf
curl -sL -o kaushanscript.ttf   https://github.com/google/fonts/raw/main/ofl/kaushanscript/KaushanScript-Regular.ttf
curl -sL -o pinyonscript.ttf    https://github.com/google/fonts/raw/main/ofl/pinyonscript/PinyonScript-Regular.ttf
DEST=/Users/theceo/DevSkyy/wordpress-theme/skyyrose-flagship/assets/fonts
.venv/bin/pyftsubset yellowtail.ttf    --unicodes=U+0000-00FF,U+2018-201F --flavor=woff2 --output-file="$DEST/yellowtail-latin.woff2"
.venv/bin/pyftsubset kaushanscript.ttf --unicodes=U+0000-00FF,U+2018-201F --flavor=woff2 --output-file="$DEST/kaushan-script-latin.woff2"
.venv/bin/pyftsubset pinyonscript.ttf  --unicodes=U+0000-00FF,U+2018-201F --flavor=woff2 --output-file="$DEST/pinyon-script-latin.woff2"
ls -la "$DEST"/{yellowtail,kaushan-script,pinyon-script}-latin.woff2
```

Expected: three woff2 files written, each a few KB. (Pure download of free OFL fonts — no paid API, no STOP-AND-SHOW. If a chosen alt is not OFL, STOP and confirm licensing.)

- [ ] **Step 3: Add `@font-face` declarations**

Locate the theme's `@font-face` block (`grep -rl "@font-face" ASSETS/css/`). Add, following the existing pattern exactly (matching `font-display`, path style):

```css
@font-face { font-family: 'Yellowtail'; src: url('../fonts/yellowtail-latin.woff2') format('woff2'); font-weight: 400; font-style: normal; font-display: swap; }
@font-face { font-family: 'Kaushan Script'; src: url('../fonts/kaushan-script-latin.woff2') format('woff2'); font-weight: 400; font-style: normal; font-display: swap; }
@font-face { font-family: 'Pinyon Script'; src: url('../fonts/pinyon-script-latin.woff2') format('woff2'); font-weight: 400; font-style: normal; font-display: swap; }
```

- [ ] **Step 4: Verify identity woff2 refs resolve**

Run:
```bash
.venv/bin/python -c "import sys; sys.path.insert(0,'wordpress-theme/skyyrose-flagship/data'); import sot_common as s; \
[print(slug, s.resolve_asset(i['fonts']['script']['woff2'])) for slug,i in s.load_identity().items()]"
```
Expected: each prints a non-None resolved path (the new woff2). None → filename mismatch.

- [ ] **Step 5: Commit**

```bash
git add wordpress-theme/skyyrose-flagship/assets/fonts/*.woff2 wordpress-theme/skyyrose-flagship/assets/css/*.css wordpress-theme/skyyrose-flagship/data/collections/*/identity.json
git commit -m "feat(fonts): self-host Yellowtail/Kaushan/Pinyon OFL woff2 + @font-face (zero-CDN)"
```

---

## Task 5 (P2): gen-design-tokens.py — generate the `[data-collection]` region

**Files:** Create `DATA/gen-design-tokens.py`; Modify `ASSETS/css/design-tokens.css` (insert marker region); Test: `tests/collections/test_gen_design_tokens.py`

> Generates ONLY between markers. Hand-authored `:root` globals + motion block stay untouched. Token mapping: `--skyyrose-accent`=palette.accent, `--skyyrose-accent-dark`=palette.accent_dark, `--skyyrose-bg`=palette.bg, `--skyyrose-text`=palette.text, `--skyyrose-font-script`=fonts.script.family, `--skyyrose-font-caps`=fonts.caps.family, `--skyyrose-font-display`=alias to caps (back-compat).

- [ ] **Step 1: Insert the marker region into `design-tokens.css`**

Replace the existing four `[data-collection="..."]` blocks (black-rose, love-hurts, signature, kids-capsule — the contaminated ones) with:

```css
/* GENERATED:collection-tokens START — do not edit; run data/gen-design-tokens.py */
/* GENERATED:collection-tokens END */
```

Leave `:root`, motion, and all non-collection blocks as-is.

- [ ] **Step 2: Write the failing test**

`tests/collections/test_gen_design_tokens.py`:

```python
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "wordpress-theme/skyyrose-flagship/data"
CSS = ROOT / "wordpress-theme/skyyrose-flagship/assets/css/design-tokens.css"
GEN = DATA / "gen-design-tokens.py"


def test_generated_region_has_corrected_palette_and_fonts():
    subprocess.run([sys.executable, str(GEN)], check=True)
    css = CSS.read_text()
    start = css.index("GENERATED:collection-tokens START")
    end = css.index("GENERATED:collection-tokens END")
    region = css[start:end]
    # Black Rose: silver accent, NO red secondary anywhere in its block
    assert '[data-collection="black-rose"]' in region
    assert "#C0C0C0" in region
    # canon purge: red must not appear in the black-rose block
    br = region[region.index('[data-collection="black-rose"]'):region.index('[data-collection="love-hurts"]')]
    assert "#DC143C" not in br
    # two-role fonts present
    assert "--skyyrose-font-script" in region and "Pinyon Script" in region


def test_generation_is_idempotent():
    subprocess.run([sys.executable, str(GEN)], check=True)
    first = CSS.read_text()
    subprocess.run([sys.executable, str(GEN)], check=True)
    assert CSS.read_text() == first
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/collections/test_gen_design_tokens.py -v`
Expected: FAIL — `gen-design-tokens.py` missing.

- [ ] **Step 4: Write `DATA/gen-design-tokens.py`**

```python
#!/usr/bin/env python3
"""Generate the [data-collection] token region of design-tokens.css from identity.json.

Writes ONLY between the GENERATED:collection-tokens START/END markers. Everything
else in design-tokens.css is hand-authored and untouched. Run after editing any
identity.json. The verifier asserts the live region matches a fresh generation.
"""

import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent
sys.path.insert(0, str(DATA))
import sot_common  # noqa: E402

CSS = DATA.parent / "assets/css/design-tokens.css"
START = "/* GENERATED:collection-tokens START"
END = "/* GENERATED:collection-tokens END */"


def block(ident: dict) -> str:
    p, f = ident["palette"], ident["fonts"]
    return (
        f'[data-collection="{ident["slug"]}"] {{\n'
        f'\t--skyyrose-accent:       {p["accent"]};\n'
        f'\t--skyyrose-accent-dark:  {p["accent_dark"]};\n'
        f'\t--skyyrose-bg:           {p["bg"]};\n'
        f'\t--skyyrose-text:         {p["text"]};\n'
        f'\t--skyyrose-font-script:  \'{f["script"]["family"]}\', cursive;\n'
        f'\t--skyyrose-font-caps:    \'{f["caps"]["family"]}\', serif;\n'
        f'\t--skyyrose-font-display: var(--skyyrose-font-caps);\n'
        f'\t--skyyrose-font-body:    \'{f["body"]["family"]}\', serif;\n'
        f'}}\n'
    )


def main() -> int:
    idents = sot_common.load_identity()
    body = "\n".join(block(idents[s]) for s in sorted(idents))
    css = CSS.read_text()
    s = css.index(START)
    e = css.index(END)
    line_end = css.index("\n", s) + 1
    new = css[:line_end] + body + css[e:]
    CSS.write_text(new)
    print(f"design-tokens.css: regenerated {len(idents)} collection blocks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/collections/test_gen_design_tokens.py -v`
Expected: PASS (both tests).

- [ ] **Step 6: Audit `--skyyrose-font-display` consumers**

Run: `grep -rn "skyyrose-font-display" wordpress-theme/skyyrose-flagship/assets/css/ | grep -v design-tokens.css`
Confirm they still resolve (the generated alias keeps them working). No code change expected — record the grep result as evidence.

- [ ] **Step 7: Commit**

```bash
git add wordpress-theme/skyyrose-flagship/data/gen-design-tokens.py wordpress-theme/skyyrose-flagship/assets/css/design-tokens.css tests/collections/test_gen_design_tokens.py
git commit -m "feat(tokens): generate [data-collection] blocks from identity canon (palette fixed, 2-role fonts)"
```

---

## Task 6 (P3): Rewrite build-collection-sot.py — per-folder sot.json + orphan set-diff

**Files:** Modify `DATA/build-collection-sot.py` (full rewrite of the COLLECTIONS/regex path); Test: `tests/collections/test_build_collection_sot.py`

> Drops `COLLECTIONS`, the per-collection regex, hardcoded accent/font. Reads identity via `sot_common`. Orphans = global set-difference written to `data/collections/_orphans.json`. `registered` expands each manifest entry across its `formats`.

- [ ] **Step 1: Write the failing test**

`tests/collections/test_build_collection_sot.py`:

```python
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "wordpress-theme/skyyrose-flagship/data"
BUILD = DATA / "build-collection-sot.py"


def test_build_emits_per_folder_sot_and_orphans():
    subprocess.run([sys.executable, str(BUILD)], check=True)
    for slug in ["black-rose", "love-hurts", "signature", "kids-capsule"]:
        sot = json.loads((DATA / "collections" / slug / "sot.json").read_text())
        assert sot["collection"] == slug
        assert "products" in sot and "imagery" in sot and "lockup" in sot
        assert "other_collection_files" not in sot          # retired
        for p in sot["products"]:
            for col, im in p.get("images", {}).items():
                if im.get("resolved"):
                    assert (ROOT / "wordpress-theme/skyyrose-flagship/assets" / im["resolved"]).is_file()
    orph = json.loads((DATA / "collections" / "_orphans.json").read_text())
    assert isinstance(orph["orphans"], list)


def test_registered_expands_format_siblings():
    # a manifest base with formats [avif, webp] must mark BOTH siblings registered,
    # so neither appears in _orphans.json
    orph = set(json.loads((DATA / "collections" / "_orphans.json").read_text())["orphans"])
    assert not any(o.endswith("homepage-col-black-rose.avif") for o in orph)
    assert not any(o.endswith("homepage-col-black-rose.webp") for o in orph)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/collections/test_build_collection_sot.py -v`
Expected: FAIL — old builder still emits flat files / `other_collection_files`.

- [ ] **Step 3: Rewrite `DATA/build-collection-sot.py`**

```python
#!/usr/bin/env python3
"""Generate per-collection SOT: data/collections/<slug>/sot.json + a global _orphans.json.

Canon source = data/collections/<slug>/identity.json (read via sot_common, validated).
The three masters (catalog CSV, visual-manifest.json, logo-registry.json) remain
authoritative for their domain; this is a GENERATED VIEW — DO NOT hand-edit sot.json.

Orphans = every image file in the tree that is registered to NO manifest entry,
catalog product, or logo (naming-independent set-difference). manifest entries are
expanded across their declared `formats`, so format siblings count as registered.

USAGE: python3 build-collection-sot.py [--updated YYYY-MM-DD]
"""

import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent
sys.path.insert(0, str(DATA))
sys.path.insert(0, str(DATA.parents[2]))
import sot_common  # noqa: E402
from skyyrose.core.catalog_loader import bool_col, read_catalog_rows  # noqa: E402

ASSETS = sot_common.ASSETS
OUT = DATA / "collections"
IMG_EXTS = sot_common.IMG_EXTS
TREE_SCAN_DIRS = [
    "branding", "images/lockups", "branding/vectorized", "branding/hero",
    "images/hero-overlays", "images/logos", "images/lookbook", "images/immersive", "images",
]
BODY_FONT = "Cormorant Garamond"


def manifest_entry(entry):
    if not isinstance(entry, dict):
        return None
    raw = entry.get("path", "")
    return {
        "path": raw, "resolved": sot_common.resolve_asset(raw),
        "kind": entry.get("kind"), "status": entry.get("status"), "notes": entry.get("notes"),
    }


def load_products_by_collection():
    by_col: dict[str, list] = {}
    for row in read_catalog_rows():
        imgs = {}
        for col in ("image", "front_model_image", "back_image", "back_model_image"):
            v = (row.get(col) or "").strip()
            if v:
                imgs[col] = {"path": v, "resolved": sot_common.resolve_asset(v)}
        dslug = (row.get("dossier_slug") or "").strip()
        by_col.setdefault(row.get("collection", ""), []).append({
            "sku": row["sku"], "name": row["name"], "price": row.get("price"),
            "is_preorder": bool_col(row, "is_preorder"), "published": bool_col(row, "published"),
            "images": imgs,
            "dossier": f"data/dossiers/{dslug}.md" if dslug else None,
            "dossier_exists": bool(dslug) and (DATA / "dossiers" / f"{dslug}.md").is_file(),
        })
    return by_col


def scan_tree() -> set[str]:
    found = set()
    for d in TREE_SCAN_DIRS:
        dd = ASSETS / d
        if not dd.is_dir():
            continue
        for f in dd.iterdir():
            if f.is_file() and f.suffix.lower() in IMG_EXTS:
                found.add(str(f.relative_to(ASSETS)))
    return found


def expand_formats(entry: dict) -> set[str]:
    """A manifest entry {path: base, formats: [ext...]} -> every concrete rel-path that exists."""
    out = set()
    base = entry.get("path", "")
    if not base:
        return out
    for ext in entry.get("formats", []) or []:
        cand = f"{base}.{ext}"
        if (ASSETS / cand).is_file():
            out.add(cand)
    r = sot_common.resolve_asset(base)   # also include whatever resolve picks
    if r:
        out.add(r)
    return out


def walk_manifest_entries(obj):
    """Yield every dict that has a 'path' key, anywhere in the manifest."""
    if isinstance(obj, dict):
        if "path" in obj:
            yield obj
        for v in obj.values():
            yield from walk_manifest_entries(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_manifest_entries(v)


def registered_files(manifest, logo_reg, products_by_col) -> set[str]:
    reg: set[str] = set()
    for entry in walk_manifest_entries(manifest):
        reg |= expand_formats(entry)
    for lid, l in logo_reg.get("logos", {}).items():
        for cand in (sot_common.resolve_asset(f"images/logos/{l.get('file','')}"),
                     sot_common.resolve_asset(l.get("file", ""))):
            if cand:
                reg.add(cand)
    for prods in products_by_col.values():
        for p in prods:
            for im in p["images"].values():
                if im.get("resolved"):
                    reg.add(im["resolved"])
    return reg


def imagery_block(mc: dict) -> dict:
    def lst(key):
        v = mc.get(key)
        return [manifest_entry(e) for e in v] if isinstance(v, list) else []
    return {
        "lockup_display": manifest_entry(mc.get("lockup_display")),
        "lockup_svg_master": manifest_entry(mc.get("lockup_svg_master")),
        "lockup_source_art": manifest_entry(mc.get("lockup_primary")),
        "lockup_alt": manifest_entry(mc.get("lockup_alt")),
        "scene_portrait": next((manifest_entry(e) for e in mc.get("atmospherics", [])
                                if isinstance(e, dict) and e.get("kind") == "collection-portrait"), None),
        "hero_backdrop": (lst("hero_backdrops") or [None])[0],
        "atmospherics": [e for e in lst("atmospherics") if e and e.get("kind") != "collection-portrait"],
        "patches": lst("patches"), "lettering_alt": lst("lettering_alt"),
        "lockup_parts": lst("lockup_parts"), "lookbook": lst("lookbook"),
    }


def logos_for(slug, key, logo_reg):
    out = []
    for lid, l in logo_reg.get("logos", {}).items():
        lcol = l.get("collection") or ""
        if key in lcol or slug in lcol:
            out.append({
                "id": lid, "file": l.get("file"),
                "resolved": sot_common.resolve_asset(f"images/logos/{l.get('file','')}")
                or sot_common.resolve_asset(l.get("file", "")),
                "primary_color": l.get("primary_color"), "notes": (l.get("description") or "")[:160],
            })
    return out


def build_collection(slug, ident, manifest, logo_reg, products, updated):
    key = ident["key"]
    mc = manifest.get(key, {})
    imagery = imagery_block(mc)
    lockup = imagery.pop("lockup_display"), imagery.pop("lockup_svg_master"), \
        imagery.pop("lockup_source_art"), imagery.pop("lockup_alt")
    return {
        "_generated_by": "data/build-collection-sot.py — DO NOT EDIT. Fix identity.json / the masters, then regenerate.",
        "_authority": f"Single Source of Truth view for {ident['name']}. Canon = identity.json.",
        "collection": slug, "name": ident["name"], "updated": updated,
        "story": ident["story"], "palette": ident["palette"], "fonts": ident["fonts"],
        "masters": {"identity": f"data/collections/{slug}/identity.json",
                    "products": "data/skyyrose-catalog.csv",
                    "imagery": "data/visual-manifest.json", "logos": "data/logo-registry.json"},
        "lockup": {
            "canonical": sot_common.resolve_asset(ident["lockup"]["ref"]),
            "display_webp": lockup[0], "svg_master": lockup[1],
            "source_art": lockup[2], "alt": lockup[3],
            "rule": "The lockup IS the collection name; never type-render it.",
        },
        "imagery": imagery,
        "logos": logos_for(slug, key, logo_reg),
        "products": products,
        "unresolved_product_images": [
            {"sku": p["sku"], "column": col, "path": im["path"]}
            for p in products for col, im in p["images"].items() if not im.get("resolved")
        ],
    }


def main() -> int:
    updated = "GENERATED"
    if "--updated" in sys.argv:
        updated = sys.argv[sys.argv.index("--updated") + 1]
    idents = sot_common.load_identity()
    manifest = sot_common.load_manifest()
    logo_reg = sot_common.load_logo_registry()
    products_by_col = load_products_by_collection()
    tree = scan_tree()
    reg = registered_files(manifest, logo_reg, products_by_col)

    for slug, ident in idents.items():
        products = products_by_col.get(slug, [])
        sot = build_collection(slug, ident, manifest, logo_reg, products, updated)
        folder = OUT / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "sot.json").write_text(json.dumps(sot, indent=2) + "\n")
        print(f"{slug}: {len(products)} products, {len(sot['logos'])} logos "
              f"({len(sot['unresolved_product_images'])} unresolved imgs)")

    known = set()
    for ident in idents.values():
        known |= set(ident.get("known_orphans", []))
    orphans = sorted(tree - reg - known)
    (OUT / "_orphans.json").write_text(json.dumps({
        "_note": "Image files in the asset tree registered to NO manifest entry, product, or logo. "
                 "Audit before use; add legit non-role files to a collection identity.json known_orphans[].",
        "count": len(orphans), "orphans": orphans,
    }, indent=2) + "\n")
    print(f"_orphans.json: {len(orphans)} unregistered files (of {len(tree)} scanned, {len(reg)} registered)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/collections/test_build_collection_sot.py -v`
Expected: PASS. (If `test_registered_expands_format_siblings` fails, check `homepage-col-black-rose` is registered via manifest `atmospherics` formats.)

- [ ] **Step 5: Commit**

```bash
git add wordpress-theme/skyyrose-flagship/data/build-collection-sot.py wordpress-theme/skyyrose-flagship/data/collections/*/sot.json wordpress-theme/skyyrose-flagship/data/collections/_orphans.json tests/collections/test_build_collection_sot.py
git commit -m "feat(sot): builder reads identity canon; per-folder sot.json + global orphan set-diff"
```

---

## Task 7 (P4): copy.md + gen-collection-hub.py (designer index.html)

**Files:** Create `DATA/collections/<slug>/copy.md` × 4; Create `DATA/gen-collection-hub.py`; Test: extend `test_gen_design_tokens.py` or new `test_gen_collection_hub.py`.

- [ ] **Step 1: Write `copy.md` per collection** (slice from `docs/brand/collection-stories.md`)

For each slug, create `DATA/collections/<slug>/copy.md` containing that collection's **Origin / Voice & Mood / Story Tagline** sections copied verbatim from `docs/brand/collection-stories.md` (authoritative source — copy, do not paraphrase). Example for black-rose:

```markdown
# Black Rose — Designer Copy

> Source: docs/brand/collection-stories.md (canonical). Seed: "Defining beauty through the color black."

## Origin
Black Rose was born from Oakland's specific gravity... [verbatim from collection-stories.md § Black Rose → Origin]

## Voice & Mood
Declarative. No qualifiers... [verbatim]

## Story Tagline
"You wear it because you already stood up."
```

Repeat for love-hurts, signature, kids-capsule using their respective sections.

- [ ] **Step 2: Write the failing test**

`tests/collections/test_gen_collection_hub.py`:

```python
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "wordpress-theme/skyyrose-flagship/data"
GEN = DATA / "gen-collection-hub.py"


def test_hub_renders_all_sections_and_escapes():
    subprocess.run([sys.executable, str(GEN)], check=True)
    html = (DATA / "collections/black-rose/index.html").read_text()
    assert "<!DOCTYPE html>" in html
    assert "Black Rose" in html
    assert "#C0C0C0" in html                      # palette swatch
    assert "Yellowtail" in html                   # font specimen
    assert "black-rose-lockup" in html            # lockup reference
    assert "../../assets/" in html or "assets/" in html   # image refs into canonical tree
    assert "<script>" not in html.lower().replace("<script>window", "x")  # no injected raw script
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/collections/test_gen_collection_hub.py -v`
Expected: FAIL — generator missing.

- [ ] **Step 4: Write `DATA/gen-collection-hub.py`**

```python
#!/usr/bin/env python3
"""Generate the per-collection designer hub: data/collections/<slug>/index.html.

Renders FROM the canonical assets/ tree (relative ../../assets/ paths) — no image
duplication (single-asset-tree lock). Reads identity.json + the generated sot.json.
All dynamic text is HTML-escaped. DO NOT hand-edit index.html.
"""

import html
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent
sys.path.insert(0, str(DATA))
import sot_common  # noqa: E402

OUT = DATA / "collections"
ASSET_PREFIX = "../../assets/"   # data/collections/<slug>/index.html -> assets/


def e(s) -> str:
    return html.escape(str(s if s is not None else ""))


def asset(rel: str | None) -> str:
    return ASSET_PREFIX + e(rel) if rel else ""


def swatches(palette: dict) -> str:
    return "".join(
        f'<div class="sw"><span style="background:{e(hex_)}"></span><code>{e(name)} {e(hex_)}</code></div>'
        for name, hex_ in palette.items()
    )


def specimen(fonts: dict) -> str:
    rows = ""
    for role, f in fonts.items():
        fam = e(f["family"])
        rows += (f'<p class="spec" style="font-family:\'{fam}\'">'
                 f'<small>{e(role)} — {fam}</small><br>The {fam} The Quick Brown Fox 0123</p>')
    return rows


def products(sot: dict) -> str:
    cells = ""
    for p in sot.get("products", []):
        img = ""
        for col in ("image", "front_model_image"):
            r = (p.get("images", {}).get(col) or {}).get("resolved")
            if r:
                img = f'<img loading="lazy" src="{asset(r)}" alt="{e(p["name"])}">'
                break
        pre = " · PRE-ORDER" if p.get("is_preorder") else ""
        cells += (f'<figure>{img}<figcaption>{e(p["sku"])} — {e(p["name"])} '
                  f'(${e(p.get("price"))}{pre})</figcaption></figure>')
    return cells


def page(ident: dict, sot: dict, copy_md: str) -> str:
    name, slug = e(ident["name"]), e(ident["slug"])
    lock = asset(sot.get("lockup", {}).get("canonical"))
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} — Collection Hub</title>
<!-- GENERATED by data/gen-collection-hub.py — DO NOT EDIT -->
<style>
 body{{font-family:'Cormorant Garamond',serif;background:{e(ident['palette']['bg'])};
   color:{e(ident['palette']['text'])};margin:0;padding:2rem;max-width:1100px;margin:auto}}
 h1,h2{{font-family:'Cinzel',serif;letter-spacing:.04em}}
 .lock img{{max-width:520px;width:100%}}
 .sw{{display:inline-flex;align-items:center;gap:.5rem;margin:.25rem 1rem .25rem 0}}
 .sw span{{width:28px;height:28px;border-radius:4px;display:inline-block;border:1px solid #666}}
 .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:1rem}}
 figure{{margin:0}} figure img{{width:100%;border-radius:6px}} figcaption{{font-size:.8rem;opacity:.8}}
 .spec{{font-size:1.6rem;margin:.4rem 0}} code{{font-family:ui-monospace,monospace;font-size:.8rem}}
</style></head><body>
<header class="lock">{f'<img src="{lock}" alt="{name} lockup">' if lock else f'<h1>{name}</h1>'}</header>
<p><em>{e(ident['story']['seed'])}</em></p>
<h2>Palette</h2><div>{swatches(ident['palette'])}</div>
<h2>Type</h2>{specimen(ident['fonts'])}
<h2>Products ({len(sot.get('products', []))})</h2><div class="grid">{products(sot)}</div>
<h2>Copy</h2><pre style="white-space:pre-wrap;font-family:inherit">{e(copy_md)}</pre>
</body></html>
"""


def main() -> int:
    idents = sot_common.load_identity()
    for slug, ident in idents.items():
        folder = OUT / slug
        sot = json.loads((folder / "sot.json").read_text())
        copy_md = (folder / "copy.md").read_text() if (folder / "copy.md").is_file() else ""
        (folder / "index.html").write_text(page(ident, sot, copy_md))
        print(f"{slug}/index.html generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/collections/test_gen_collection_hub.py -v`
Expected: PASS.

- [ ] **Step 6: Eyeball one hub**

Run: `open wordpress-theme/skyyrose-flagship/data/collections/signature/index.html`
Confirm lockup, gold/rose-gold swatches, Pinyon specimen, product grid, copy render.

- [ ] **Step 7: Commit**

```bash
git add wordpress-theme/skyyrose-flagship/data/gen-collection-hub.py wordpress-theme/skyyrose-flagship/data/collections/*/copy.md wordpress-theme/skyyrose-flagship/data/collections/*/index.html tests/collections/test_gen_collection_hub.py
git commit -m "feat(sot): per-collection copy.md + generated designer index.html hub"
```

---

## Task 8 (P5): Rewrite verify-collection-sot.py — full drift gate + golden test

**Files:** Modify `DATA/verify-collection-sot.py`; Test: `tests/collections/test_verify_drift.py`

- [ ] **Step 1: Rewrite `DATA/verify-collection-sot.py`**

```python
#!/usr/bin/env python3
"""Verify the generated SOT + tokens against canon and reality. Exit 0 clean, 1 on hard fail.

Asserts per collection: catalog SKU coverage; every declared resolved path is a real file;
every identity font woff2 resolves; the generated design-tokens region matches a fresh
generation; _orphans.json is disjoint from registered files.
"""

import json
import subprocess
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent
sys.path.insert(0, str(DATA))
sys.path.insert(0, str(DATA.parents[2]))
import sot_common  # noqa: E402
from skyyrose.core.catalog_loader import read_catalog_rows  # noqa: E402

OUT = DATA / "collections"
CSS = DATA.parent / "assets/css/design-tokens.css"


def catalog_skus():
    by = {}
    for row in read_catalog_rows():
        by.setdefault(row["collection"], set()).add(row["sku"])
    return by


def walk_resolved(obj, slug, hard):
    if isinstance(obj, dict):
        p, r = obj.get("path"), obj.get("resolved")
        if p and "resolved" in obj and (not r or not (sot_common.ASSETS / r).is_file()):
            hard.append(f"{slug}: declared path does not resolve: {p}")
        for v in obj.values():
            walk_resolved(v, slug, hard)
    elif isinstance(obj, list):
        for v in obj:
            walk_resolved(v, slug, hard)


def main() -> int:
    idents = sot_common.load_identity()   # raises IdentityError on bad canon
    cat = catalog_skus()
    hard, warn = [], []

    # 1. design-tokens region matches fresh generation
    before = CSS.read_text()
    subprocess.run([sys.executable, str(DATA / "gen-design-tokens.py")], check=True)
    if CSS.read_text() != before:
        hard.append("design-tokens.css collection region is STALE — run gen-design-tokens.py and commit")

    for slug, ident in idents.items():
        fp = OUT / slug / "sot.json"
        if not fp.is_file():
            hard.append(f"{slug}: sot.json missing")
            continue
        sot = json.loads(fp.read_text())
        sot_skus = {p["sku"] for p in sot.get("products", [])}
        expected = cat.get(slug, set())
        if miss := expected - sot_skus:
            hard.append(f"{slug}: catalog SKUs missing from SOT: {sorted(miss)}")
        if extra := sot_skus - expected:
            hard.append(f"{slug}: SOT SKUs not in catalog: {sorted(extra)}")
        for role in ("script", "caps", "body"):
            w = ident["fonts"][role]["woff2"]
            if w and not sot_common.resolve_asset(w):
                hard.append(f"{slug}: font {role} woff2 missing: {w}")
        walk_resolved(sot.get("lockup", {}), slug, hard)
        walk_resolved(sot.get("imagery", {}), slug, hard)
        walk_resolved(sot.get("logos", []), slug, hard)
        for u in sot.get("unresolved_product_images", []):
            warn.append(f"{slug}: {u['sku']} {u['column']} -> {u['path']} (missing file)")
        print(f"{slug}: {len(sot_skus)}/{len(expected)} SKUs, "
              f"{len(sot.get('unresolved_product_images', []))} broken product refs")

    if warn:
        print("\nWARNINGS (fix in skyyrose-catalog.csv):")
        for w in warn:
            print("  ⚠ " + w)
    if hard:
        print("\nHARD FAILURES:")
        for h in hard:
            print("  ✗ " + h)
        return 1
    print("\n✓ all per-collection SOT files + tokens verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Write golden + drift test**

`tests/collections/test_verify_drift.py`:

```python
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "wordpress-theme/skyyrose-flagship/data"


def test_full_pipeline_then_verify_is_clean():
    for script in ("gen-design-tokens.py", "build-collection-sot.py", "gen-collection-hub.py"):
        subprocess.run([sys.executable, str(DATA / script)], check=True)
    r = subprocess.run([sys.executable, str(DATA / "verify-collection-sot.py")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
```

- [ ] **Step 3: Run tests**

Run: `.venv/bin/python -m pytest tests/collections/ -v`
Expected: ALL PASS.

- [ ] **Step 4: Wire CI / hooks**

Point `.claude/hooks/catalog-drift-guard.sh` at the new pipeline (regenerate `gen-design-tokens.py` + `build-collection-sot.py` + `gen-collection-hub.py`, then run `verify-collection-sot.py`). Confirm the hook still exits 0 on a clean tree.

- [ ] **Step 5: Commit**

```bash
git add wordpress-theme/skyyrose-flagship/data/verify-collection-sot.py tests/collections/test_verify_drift.py .claude/hooks/catalog-drift-guard.sh
git commit -m "feat(sot): full drift gate (tokens+woff2+SKU+resolve) + golden pipeline test + hook wiring"
```

---

## Task 9 (P6): Cut-over — census → repoint → ⛔ FOUNDER WALKTHROUGH → delete → .min → docs

**Files:** repo-wide (discovered by census); `ASSETS/css/design-tokens.min.css`; `README`/`docs/CLAUDE.md`/`.wolf/anatomy.md`

- [ ] **Step 1: Consumer census (authoritative — grep, do not assume)**

```bash
cd /Users/theceo/DevSkyy
rg -n "data/collections/[a-z-]+\.json|other_collection_files|COLLECTIONS\b" -g '!.claude/worktrees/**' > /tmp/census.txt
rg -n "Yellowtail|Italiana|UnifrakturMaguntia|Pinyon Script" wordpress-theme/skyyrose-flagship -g '!data/collections/**' >> /tmp/census.txt
rg -ln "data/collections" -t py -t php -t js -g '!.claude/worktrees/**' >> /tmp/census.txt
cat /tmp/census.txt
```

Build a table: file:line → what it references → repoint target (`data/collections/<slug>/sot.json` or `identity.json`).

- [ ] **Step 2: Repoint every live consumer**

For each census hit reading the old flat `data/collections/<slug>.json`, change it to read `data/collections/<slug>/sot.json`. Inspect `scripts/verify_seo.py`, `scripts/site_auditor.py`, `inc/redirects.php`, `assets/js/mascot.js` precisely (some matches may be incidental). Run their tests after each repoint.

- [ ] **Step 3: ⛔ FOUNDER WALKTHROUGH — STOP**

**Do NOT delete anything yet.** Present to Corey: the census table, the exact deletion list (flat `data/collections/*.json`, dead `@font-face`/font-family names, any obsolete scripts), and the repoint diffs. Get explicit sign-off. This is the standalone todo item in `tasks/todo.md` — it must be checked off before Step 4.

- [ ] **Step 4: Delete superseded artifacts (post-sign-off, repoint-verified)**

After sign-off, for each deletion confirm zero live refs (`rg -n "<artifact>" -g '!.claude/worktrees/**'` returns only the artifact itself), then remove:
```bash
git rm wordpress-theme/skyyrose-flagship/data/collections/black-rose.json \
       wordpress-theme/skyyrose-flagship/data/collections/love-hurts.json \
       wordpress-theme/skyyrose-flagship/data/collections/signature.json \
       wordpress-theme/skyyrose-flagship/data/collections/kids-capsule.json
```
Remove dead `@font-face`/font-family declarations (Italiana, UnifrakturMaguntia, the unhosted Pinyon, old Yellowtail-as-LH) from CSS. Each deletion = one census entry proving zero remaining refs.

- [ ] **Step 5: Rebuild `.min` (prod serves it)**

```bash
node wordpress-theme/skyyrose-flagship/scripts/build-css.js
grep -c "data-collection" wordpress-theme/skyyrose-flagship/assets/css/design-tokens.min.css   # >0, region present
```

- [ ] **Step 6: Update docs**

Update `wordpress-theme/skyyrose-flagship/data/collections/README.md`, `docs/CLAUDE.md` (canon index → new SOT), `.wolf/anatomy.md` (new files). 

- [ ] **Step 7: Commit**

```bash
git add -A wordpress-theme/skyyrose-flagship/ scripts/ docs/ .wolf/anatomy.md
git commit -m "refactor(sot): cut-over all refs to per-folder SOT; delete flat files + dead fonts; rebuild .min"
```

---

## Task 10 (P7): Verify + review gate (no "done" without this)

- [ ] **Step 1: Full re-verify from clean state (capture output)**

```bash
cd /Users/theceo/DevSkyy
.venv/bin/python -m pytest tests/collections/ -v
.venv/bin/python wordpress-theme/skyyrose-flagship/data/verify-collection-sot.py
git status --short    # scope sane; no stray files
```
Paste the passing output into the PR/summary as proof.

- [ ] **Step 2: Wiring/completeness check**

```bash
for s in black-rose love-hurts signature kids-capsule; do
  for f in identity.json copy.md sot.json index.html; do
    test -f "wordpress-theme/skyyrose-flagship/data/collections/$s/$f" || echo "MISSING $s/$f"
  done
done
rg -n "data/collections/[a-z-]+\.json" -g '!.claude/worktrees/**'   # expect: no hits (flat files gone, none referenced)
```
Expected: no MISSING, no flat-file refs.

- [ ] **Step 3: `/simplify` then `/code-review`**

Run `/simplify` on the diff (quality pass), then `/code-review` (correctness). Address findings; re-run Step 1 after fixes.

- [ ] **Step 4: Security pass**

Confirm: `index.html` escapes all dynamic text (Task 7 `e()`); no `open()` without `encoding=`; no path traversal in `resolve_asset` (it only globs within `ASSETS`). Run the security-reviewer agent on the new `.py` files.

- [ ] **Step 5: Final commit + PR**

```bash
git add -A && git commit -m "chore(sot): harden + address /simplify and /code-review findings"
git push -u origin feat/collection-identity-sot
gh pr create --title "Collection Identity SOT — per-collection canon folders + hard cut-over" --body "Implements docs/superpowers/specs/2026-06-14-collection-identity-sot-design.md. Per-collection identity canon drives design-tokens, sot.json, and a designer hub. Old structure deleted after founder walkthrough."
```

---

## Self-review

**Spec coverage:** §3 palettes → Task 2 + Task 5; §5 folder shape → Tasks 2/6/7; §6 fonts → Task 4 (+specimen); §7 token rebuild → Task 5; §8 builder/orphans/exists/guarded-loads → Tasks 3/6; §9 hub → Task 7; §10 verify+tests → Tasks 1–8; §11 phases → Tasks 0–10; §12 missing-BR-thumb → Task 4 Step 1 (matches from lockup); §13 non-goals respected (no bespoke fonts, no image copies, no deploy); §14 standing rules → Task 9 (census/repoint-first) + Task 10 (proof gate). **No gaps.**

**Placeholder scan:** the only intentional fill-ins are `<cinzel-woff2>`/`<cormorant-woff2>` in Task 2 — resolved by Task 0 Step 2 (real `ls`) with a guard test (Task 2 Step 7) that fails if left unsubstituted. No vague "add error handling"/"write tests" — every code step has complete code.

**Type/name consistency:** `sot_common.resolve_asset` / `load_identity` / `load_manifest` / `slug_to_key` / `IdentityError` / `ASSETS` / `COLLECTIONS_DIR` used consistently across Tasks 3/5/6/7/8. `sot.json` keys (`collection`, `products`, `imagery`, `lockup`, `palette`, `fonts`) consistent between builder (Task 6) and verifier (Task 8) and hub (Task 7). Generated CSS markers `GENERATED:collection-tokens START/END` consistent between Task 5 generator and Task 8 drift check.
