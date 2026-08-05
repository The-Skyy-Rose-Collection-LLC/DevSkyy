#!/usr/bin/env python3
"""Run the mandatory SkyyRose visual product asset gate.

Exit codes:
  0  approved
  2  rejected or requires founder review
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Direct script execution puts ``scripts/`` on sys.path, not the repository
# root. Keep the CLI usable from release automation without requiring PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skyyrose.elite_studio.platform.fidelity.asset_gate import (
    AssetVerificationRequest,
    verify_visual_asset,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sku", required=True)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--references", required=True, type=Path)
    parser.add_argument("--provenance", required=True, type=Path)
    parser.add_argument("--trust-manifest", required=True, type=Path)
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--report-root", type=Path, default=Path("renders/fidelity-reports"))
    parser.add_argument("--threshold", type=float, default=0.95)
    args = parser.parse_args()

    report = verify_visual_asset(
        AssetVerificationRequest(
            sku=args.sku,
            model_path=args.model,
            reference_root=args.references,
            provenance_path=args.provenance,
            trust_manifest_path=args.trust_manifest,
            approval_path=args.approval,
            report_root=args.report_root,
            threshold=args.threshold,
        )
    )
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.disposition.value == "approved" else 2


if __name__ == "__main__":
    raise SystemExit(main())
