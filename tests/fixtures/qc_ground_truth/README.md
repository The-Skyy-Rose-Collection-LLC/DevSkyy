# Imagery QC ground truth
The labeled set is `renders/oai/_review/review-state.json` (81 founder labels:
approved & not flagged -> pass; flagged -> fail). Most original render PNGs were deleted
2026-06-09, so calibration runs only on labels whose image still exists on disk. Re-render
a small subset, label it on the :8944 board, then run:
  python scripts/oai-render-qc-eval.py --yes
Output: kappa + recommended mode -> set QC_JUDGE_PROVIDER=anthropic and the hard/soft mode.
