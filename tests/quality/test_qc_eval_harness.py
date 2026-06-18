import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("qc_eval", Path("scripts/oai-render-qc-eval.py"))
qc_eval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qc_eval)


def test_compute_kappa_from_pairs():
    judge = [1, 0, 1, 1, 0]
    human = [1, 0, 1, 0, 0]
    k = qc_eval.kappa_from_pairs(judge, human)
    assert -1.0 <= k <= 1.0
    assert qc_eval.mode_for(k) in ("hard_gate", "soft_signal")
