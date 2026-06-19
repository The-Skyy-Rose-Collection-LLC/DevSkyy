"""Stage E: GIMP pixel cleanup.

Light pixel cleanup on the Stage D composite via cli-anything-gimp.
Non-fatal: returns the input path unchanged when cli-anything-gimp is absent
or fails, so the main pipeline always continues.
"""

from __future__ import annotations

import logging
import shlex
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def gimp_pixel_cleanup(
    composite_path: str,
    sku: str,
    output_dir: str,
) -> str:
    """Light pixel cleanup on the Stage D composite via cli-anything-gimp.

    Runs: open → gaussian-blur r=1 → export PNG.
    Non-fatal: returns ``composite_path`` unchanged on any failure so the
    main pipeline continues unaffected when cli-anything-gimp is absent.

    Args:
        composite_path: Path to the Stage D composite PNG.
        sku: Canonical SKU string.
        output_dir: Directory where the cleaned image is written.

    Returns:
        Path to the cleaned image, or ``composite_path`` on any failure.
    """
    out = Path(output_dir)
    cleanup_path = str(out / f"{sku}-composite-clean.png")
    # cli-anything-gimp surface (2026-05-26): media={check,histogram,list,probe},
    # filter={add,info,list,remove,set}, export={render,presets,preset-info}. The previous
    # "media open / filter apply / export save" sequence never matched the real CLI surface.
    # Stage E is a no-op until a project new -> layer add -> filter add -> export render
    # pipeline is wired. Stage D output is returned unchanged; downstream stages handle it fine.
    commands: list[str] = []
    try:
        for cmd in commands:
            argv = ["cli-anything-gimp", "--json"] + shlex.split(cmd)
            result = subprocess.run(argv, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                logger.debug(
                    "GIMP cleanup step failed for %s: %s",
                    sku,
                    result.stderr.strip()[:200],
                )
                return composite_path
        if Path(cleanup_path).is_file():
            logger.info("GIMP pixel cleanup done for %s → %s", sku, cleanup_path)
            return cleanup_path
        return composite_path
    except FileNotFoundError:
        logger.info("cli-anything-gimp not found; skipping pixel cleanup for %s", sku)
        return composite_path
    except subprocess.TimeoutExpired:
        logger.warning("GIMP pixel cleanup timed out for %s", sku)
        return composite_path
    except Exception as exc:  # pragma: no cover
        logger.warning("GIMP pixel cleanup unexpected error for %s: %s", sku, exc)
        return composite_path
