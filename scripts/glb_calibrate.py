#!/usr/bin/env python3
"""
GLB lighting-calibration sweep.

For each verdict=fail SKU in renders/3d/qc/fidelity_report.json, renders a
tone-mapping x exposure grid and records the best-achieving ΔE. Classifies each
SKU as LIGHTING_CORRECTABLE (some combo gets it under threshold) or TRUE_MISMATCH
(no combo does — the GLB itself needs a real fix, not a harness tweak).

Separately picks a *single* global harness-default candidate: the one combo that
rescues the most failing SKUs. Because a combo that fixes light garments could
regress the already-passing dark ones, the candidate is re-rendered against the
currently-passing SKUs before it is recommended — the metric that matters is net
passes across the whole fleet, not rescues among the failures alone.

Grid renders are written to renders/3d/qc/_calib/ and NEVER touch the canonical
{sku}_front.png screenshots or fidelity_report.json — those stay glb_fidelity.py's.

Writes:
    renders/3d/qc/calibration_report.json    — full per-SKU per-combo sweep
    renders/3d/qc/remediation_manifest.json  — TRUE_MISMATCH queue (output only,
                                                never executes a paid fix)

Usage:
    python scripts/glb_calibrate.py                # full 9-combo grid, all fails
    python scripts/glb_calibrate.py --sku sg-006    # one SKU
    python scripts/glb_calibrate.py --limit 3       # first 3 failing SKUs
    python scripts/glb_calibrate.py --grid-small    # 2-combo grid (fast/dev)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import glb_fidelity as gf  # noqa: E402

# ── grid ─────────────────────────────────────────────────────────────────────
_TONE_MAPPINGS: tuple[str, ...] = ("neutral", "aces", "agx")
_EXPOSURES: tuple[float, ...] = (0.7, 1.0, 1.3)
_SMALL_TONE_MAPPINGS: tuple[str, ...] = ("neutral",)
_SMALL_EXPOSURES: tuple[float, ...] = (0.7, 1.3)
_FULL_GRID_ORDER: list[tuple[str, float]] = [(t, e) for t in _TONE_MAPPINGS for e in _EXPOSURES]

Combo = tuple[str, float]  # (tone_mapping, exposure)

CALIB_DIR: Path = gf.QC_DIR / "_calib"

# Above this ΔE, even the best lighting combo leaves the render implausible as a
# lighting-only issue — classified TRUE_MISMATCH and routed to a heavier fix.
_SEVERE_MISMATCH_DELTA_E = 40.0
# meshy_retexture cost is a known per-unit estimate; mesh_regen has no verified
# price in this repo — leave it unpriced rather than invent a number.
_ACTION_COSTS: dict[str, float | None] = {
    "meshy_retexture": 0.50,
    "mesh_regen": None,
}


def build_grid(small: bool = False) -> list[Combo]:
    """Return the (tone_mapping, exposure) combinations to sweep."""
    tones = _SMALL_TONE_MAPPINGS if small else _TONE_MAPPINGS
    exposures = _SMALL_EXPOSURES if small else _EXPOSURES
    return [(t, e) for t in tones for e in exposures]


def combo_label(combo: Combo) -> str:
    tone, exposure = combo
    return f"{tone}_{exposure}"


def classify(best_delta_e: float | None, threshold: float = gf._COLOR_DELTA_E_MAX) -> str:
    """Classify a SKU by its best-achievable ΔE across the grid."""
    if best_delta_e is None:
        return "UNSCORABLE"
    return "LIGHTING_CORRECTABLE" if best_delta_e <= threshold else "TRUE_MISMATCH"


def recommended_action(best_delta_e: float) -> str:
    """Heuristic remediation route for a TRUE_MISMATCH SKU."""
    return "mesh_regen" if best_delta_e >= _SEVERE_MISMATCH_DELTA_E else "meshy_retexture"


def _combo_sort_key(combo: Combo) -> int:
    try:
        return _FULL_GRID_ORDER.index(combo)
    except ValueError:
        return len(_FULL_GRID_ORDER)


def pick_candidate_combo(
    grid_results: dict[str, dict[Combo, float | None]],
    threshold: float = gf._COLOR_DELTA_E_MAX,
) -> tuple[Combo | None, dict[Combo, int]]:
    """
    Pick the single combo that rescues (ΔE <= threshold) the most failing SKUs.

    Returns (best_combo, {combo: rescue_count}). best_combo is None if no combo
    rescues anyone. Ties are broken deterministically by grid order (first
    combo tried wins), not by dict/hash iteration order.
    """
    rescue_counts: dict[Combo, int] = {}
    for combo_scores in grid_results.values():
        for combo, de in combo_scores.items():
            if de is not None and de <= threshold:
                rescue_counts[combo] = rescue_counts.get(combo, 0) + 1
    if not rescue_counts:
        return None, rescue_counts
    best = max(rescue_counts, key=lambda c: (rescue_counts[c], -_combo_sort_key(c)))
    return best, rescue_counts


# ── result shapes ────────────────────────────────────────────────────────────


@dataclass
class SkuCalibration:
    sku: str
    master: str | None
    baseline_delta_e: float | None
    grid: dict[str, float | None]  # combo_label -> delta_e (None if unscoreable)
    best_combo: Combo | None
    best_delta_e: float | None
    classification: str  # LIGHTING_CORRECTABLE | TRUE_MISMATCH | UNSCORABLE


def classify_sweep(
    sku: str,
    master: str | None,
    baseline_delta_e: float | None,
    combo_scores: dict[Combo, float | None],
    *,
    threshold: float = gf._COLOR_DELTA_E_MAX,
) -> SkuCalibration:
    """Reduce one SKU's raw grid scores into a best-combo classification."""
    scored = {c: de for c, de in combo_scores.items() if de is not None}
    if scored:
        best_combo = min(scored, key=lambda c: scored[c])
        best_delta_e = scored[best_combo]
    else:
        best_combo = None
        best_delta_e = None
    return SkuCalibration(
        sku=sku,
        master=master,
        baseline_delta_e=baseline_delta_e,
        grid={combo_label(c): de for c, de in combo_scores.items()},
        best_combo=best_combo,
        best_delta_e=best_delta_e,
        classification=classify(best_delta_e, threshold=threshold),
    )


def build_remediation_manifest(
    classifications: list[SkuCalibration],
    *,
    threshold: float = gf._COLOR_DELTA_E_MAX,
) -> dict[str, Any]:
    """
    Shape TRUE_MISMATCH SKUs into an output-only remediation queue.

    OUTPUT ONLY — never dispatches a paid fix. A human reviews this manifest and
    triggers remediation (subject to the project's STOP-AND-SHOW money gate)
    separately.
    """
    entries: list[dict[str, Any]] = []
    for c in classifications:
        if c.classification != "TRUE_MISMATCH":
            continue
        action = recommended_action(c.best_delta_e)  # best_delta_e is not None here
        entries.append(
            {
                "sku": c.sku,
                "best_delta_e": c.best_delta_e,
                "best_settings": (
                    {"tone_mapping": c.best_combo[0], "exposure": c.best_combo[1]}
                    if c.best_combo
                    else None
                ),
                "recommended_action": action,
                "est_cost_usd": _ACTION_COSTS[action],
                "reference_master": c.master,
            }
        )
    priced = [e["est_cost_usd"] for e in entries if e["est_cost_usd"] is not None]
    return {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": (
            "OUTPUT ONLY — a remediation queue, not an execution plan. This script "
            "makes zero paid API calls. mesh_regen has no verified per-unit price; "
            "get a fresh quote before dispatch."
        ),
        "threshold": threshold,
        "entries": entries,
        "summary": {
            "count": len(entries),
            "est_total_cost_usd": round(sum(priced), 2) if priced else 0.0,
            "unpriced_count": sum(1 for e in entries if e["est_cost_usd"] is None),
        },
    }


# ── report I/O ───────────────────────────────────────────────────────────────


def _load_fidelity_report() -> dict[str, Any]:
    path = gf.QC_DIR / "fidelity_report.json"
    if not path.exists():
        sys.exit(f"No fidelity_report.json at {path} — run scripts/glb_fidelity.py first")
    return json.loads(path.read_text(encoding="utf-8"))


def _score_against_master(screenshot: Path, master: Path | None) -> float | None:
    """Return color ΔE for one screenshot vs the hub master, or None if unscoreable."""
    if master is None or not screenshot.exists():
        return None
    color_spec = gf._color_spec_from_image(master)
    if not color_spec:
        return None
    from skyyrose.elite_studio.fidelity import check_color  # noqa: PLC0415

    result = check_color(screenshot, color_spec, delta_e_max=gf._COLOR_DELTA_E_MAX)
    return result.score if result.available else None


# ── main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="GLB lighting-calibration grid sweep")
    parser.add_argument("--sku", help="Calibrate a single SKU only (must be verdict=fail)")
    parser.add_argument("--limit", type=int, help="Process only the first N failing SKUs")
    parser.add_argument(
        "--grid-small", action="store_true", help="2-combo grid instead of 9 (fast/dev)"
    )
    args = parser.parse_args()

    report = _load_fidelity_report()
    sku_rows = {r["sku"]: r for r in report["skus"]}
    failing = sorted(sku for sku, r in sku_rows.items() if r["verdict"] == "fail")
    passing = sorted(sku for sku, r in sku_rows.items() if r["verdict"] == "pass")

    if not failing:
        sys.exit("No verdict=fail SKUs in fidelity_report.json — nothing to calibrate")

    if args.sku:
        if args.sku not in failing:
            sys.exit(f"SKU {args.sku!r} is not verdict=fail — calibration only targets failures")
        failing = [args.sku]
    if args.limit:
        failing = failing[: args.limit]

    grid = build_grid(small=args.grid_small)
    print(
        f"Calibration sweep — {len(failing)} failing SKU(s) x {len(grid)} combo(s) "
        f"= {len(failing) * len(grid)} render(s)",
        flush=True,
    )

    _serve_root, http_port, http_server = gf.setup_serve_root()
    CALIB_DIR.mkdir(parents=True, exist_ok=True)

    t_start = time.monotonic()
    per_sku_grid: dict[str, dict[Combo, float | None]] = {}
    per_sku_master: dict[str, str | None] = {}

    for sku in failing:
        row = sku_rows[sku]
        master = Path(row["master"]) if row["master"] else None
        per_sku_master[sku] = row["master"]
        per_sku_grid[sku] = {}
        print(f"\n[{sku}]", flush=True)

        for combo in grid:
            tone_mapping, exposure = combo
            label = combo_label(combo)
            out_path = CALIB_DIR / f"{sku}__{label}.png"
            html_name = f"_calib_{sku}__{label}.html"
            try:
                shot_ok, msg, _loaded, _errored = gf._screenshot_glb(
                    sku,
                    http_port,
                    out_path,
                    exposure=exposure,
                    tone_mapping=tone_mapping,
                    html_name=html_name,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"    {label:<14} screenshot=ERROR({exc})", flush=True)
                per_sku_grid[sku][combo] = None
                continue

            de = _score_against_master(out_path, master) if shot_ok else None
            per_sku_grid[sku][combo] = de
            de_str = f"{de:5.1f}" if de is not None else "  n/a"
            print(f"    {label:<14} shot={'ok' if shot_ok else 'FAIL':4} dE={de_str}", flush=True)

    # ── candidate default: which combo rescues the most failing SKUs? ────────
    candidate_combo, rescue_counts = pick_candidate_combo(per_sku_grid)

    # ── regression check: re-render currently-passing SKUs under the candidate,
    # so a combo that fixes light garments but breaks dark ones is caught. ────
    regression_checked: dict[str, float | None] = {}
    if candidate_combo is not None and passing:
        tone_mapping, exposure = candidate_combo
        print(
            f"\nCandidate default {combo_label(candidate_combo)} rescues "
            f"{rescue_counts[candidate_combo]}/{len(failing)} failing SKUs. "
            f"Re-checking {len(passing)} currently-passing SKU(s) for regressions…",
            flush=True,
        )
        for sku in passing:
            row = sku_rows[sku]
            master = Path(row["master"]) if row["master"] else None
            label = combo_label(candidate_combo)
            out_path = CALIB_DIR / f"{sku}__{label}.png"
            html_name = f"_calib_{sku}__{label}.html"
            try:
                shot_ok, _msg, _loaded, _errored = gf._screenshot_glb(
                    sku,
                    http_port,
                    out_path,
                    exposure=exposure,
                    tone_mapping=tone_mapping,
                    html_name=html_name,
                )
            except Exception:  # noqa: BLE001
                regression_checked[sku] = None
                continue
            de = _score_against_master(out_path, master) if shot_ok else None
            regression_checked[sku] = de
            de_str = f"{de:5.1f}" if de is not None else "  n/a"
            status = "REGRESSED" if (de is not None and de > gf._COLOR_DELTA_E_MAX) else "ok"
            print(f"    [{sku}]  dE={de_str}  {status}", flush=True)

    http_server.shutdown()
    total_elapsed = time.monotonic() - t_start

    # ── classify each swept SKU ────────────────────────────────────────────
    classifications = [
        classify_sweep(sku, per_sku_master[sku], sku_rows[sku]["color_delta_e"], per_sku_grid[sku])
        for sku in failing
    ]

    n_regressions = sum(
        1 for de in regression_checked.values() if de is not None and de > gf._COLOR_DELTA_E_MAX
    )
    net_new_passes = rescue_counts.get(candidate_combo, 0) if candidate_combo else 0
    recommend_default = candidate_combo is not None and net_new_passes > 0 and n_regressions == 0

    print("\n── Calibration Results ──────────────────────────────────────────────")
    for c in classifications:
        combo_str = combo_label(c.best_combo) if c.best_combo else "n/a"
        best_str = f"{c.best_delta_e:5.1f}" if c.best_delta_e is not None else "  n/a"
        base_str = f"{c.baseline_delta_e:5.1f}" if c.baseline_delta_e is not None else "  n/a"
        print(
            f"  {c.sku:<12} baseline_dE={base_str}  best_dE={best_str}  "
            f"best={combo_str:<16} {c.classification}"
        )
    n_correctable = sum(1 for c in classifications if c.classification == "LIGHTING_CORRECTABLE")
    n_mismatch = sum(1 for c in classifications if c.classification == "TRUE_MISMATCH")
    print(
        f"\n  LIGHTING_CORRECTABLE={n_correctable}  TRUE_MISMATCH={n_mismatch}  "
        f"UNSCORABLE={len(classifications) - n_correctable - n_mismatch}"
    )
    if candidate_combo:
        verdict = "RECOMMENDED" if recommend_default else "REJECTED (regressions)"
        print(
            f"  Candidate default: {combo_label(candidate_combo)} "
            f"({net_new_passes}/{len(failing)} rescued, {n_regressions} regression(s)) -> {verdict}"
        )
    else:
        print("  No combo rescued any failing SKU — no candidate default.")
    print(f"  Total time: {total_elapsed:.1f}s")

    # ── write calibration_report.json ─────────────────────────────────────
    gf.QC_DIR.mkdir(parents=True, exist_ok=True)
    calib_report = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "threshold": gf._COLOR_DELTA_E_MAX,
        "grid": [combo_label(c) for c in grid],
        "skus": [asdict(c) for c in classifications],
        "rescue_counts": {combo_label(c): n for c, n in rescue_counts.items()},
        "candidate_default": (
            {"tone_mapping": candidate_combo[0], "exposure": candidate_combo[1]}
            if candidate_combo
            else None
        ),
        "candidate_regression_check": {
            "checked_skus": list(regression_checked.keys()),
            "scores": dict(regression_checked.items()),
            "regressions": n_regressions,
        },
        "recommend_as_harness_default": recommend_default,
        "summary": {
            "failing_swept": len(failing),
            "lighting_correctable": n_correctable,
            "true_mismatch": n_mismatch,
            "unscorable": len(classifications) - n_correctable - n_mismatch,
            "elapsed_s": round(total_elapsed, 1),
        },
    }
    calib_path = gf.QC_DIR / "calibration_report.json"
    tmp_path = calib_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(calib_report, indent=2), encoding="utf-8")
    os.replace(tmp_path, calib_path)
    print(f"\n  Calibration report -> {calib_path}", flush=True)

    # ── write remediation_manifest.json ────────────────────────────────────
    manifest = build_remediation_manifest(classifications)
    manifest_path = gf.QC_DIR / "remediation_manifest.json"
    tmp_manifest_path = manifest_path.with_suffix(".json.tmp")
    tmp_manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    os.replace(tmp_manifest_path, manifest_path)
    print(
        f"  Remediation manifest -> {manifest_path} "
        f"({manifest['summary']['count']} SKU(s), "
        f"est ${manifest['summary']['est_total_cost_usd']})",
        flush=True,
    )


if __name__ == "__main__":
    main()
