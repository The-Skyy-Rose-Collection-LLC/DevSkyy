"""Guard: every image path referenced by an SOT surface must be a *tracked* git blob.

"File exists on disk" and "file exists after a checkout / clean-tree deploy" are
different claims: ``.gitignore`` blanket-ignores theme webp (rule
``wordpress-theme/skyyrose-flagship/assets/**/*.webp``), so a repoint can reference
a binary that deploys fine from a dirty working tree and 404s from a clean one
(bug-175: ``br-014-giants-back.webp`` was referenced by PR #724 but never tracked).
This census closes that class for data/sot-images.json, every collection sot.json,
and the catalog CSV. New binaries must land with ``git add -f``.
"""

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
THEME = "wordpress-theme/skyyrose-flagship"
IMG_RE = re.compile(r"assets/images/[^\"',|\s]+\.(?:webp|avif|jpe?g|png|gif|svg)", re.I)


def _tracked_files() -> set[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return {p for p in out.split("\0") if p}


def _referenced_paths() -> dict[str, set[str]]:
    """Theme-relative image paths per SOT surface that serves them."""
    surfaces = [
        REPO / "data" / "sot-images.json",
        REPO / THEME / "data" / "skyyrose-catalog.csv",
        *sorted((REPO / THEME / "data" / "collections").glob("*/sot.json")),
    ]
    return {
        str(f.relative_to(REPO)): set(IMG_RE.findall(f.read_text(encoding="utf-8")))
        for f in surfaces
    }


def test_every_referenced_image_is_git_tracked():
    tracked = _tracked_files()
    missing = [
        (source, path)
        for source, paths in sorted(_referenced_paths().items())
        for path in sorted(paths)
        if f"{THEME}/{path}" not in tracked
    ]
    assert not missing, (
        "Image paths referenced by SOT surfaces but NOT tracked in git — they would "
        "404 after a clean-tree deploy. Land the binaries with `git add -f` "
        "(.gitignore ignores theme webp):\n" + "\n".join(f"  {src}: {p}" for src, p in missing)
    )


def test_census_covers_all_surfaces_and_finds_paths():
    """The census must actually be looking at something — an empty sweep can't fail."""
    refs = _referenced_paths()
    assert "data/sot-images.json" in refs
    assert f"{THEME}/data/skyyrose-catalog.csv" in refs
    collection_surfaces = [s for s in refs if s.endswith("/sot.json")]
    assert (
        len(collection_surfaces) >= 4
    ), f"expected >=4 collection sot.json, got {collection_surfaces}"
    total = sum(len(p) for p in refs.values())
    assert total >= 100, f"census found only {total} image refs — extraction regressed"


def test_census_would_catch_an_untracked_reference():
    """Prove the check can go red: a fabricated path must be flagged as untracked."""
    tracked = _tracked_files()
    ghost = "assets/images/products/__census-selftest-ghost__.webp"
    assert IMG_RE.findall(f'{{"front": "{ghost}"}}') == [ghost]
    assert f"{THEME}/{ghost}" not in tracked
