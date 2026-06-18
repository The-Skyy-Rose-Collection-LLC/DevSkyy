from evaluation.calibration import cohen_kappa, decide_mode


def test_perfect():
    assert cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0


def test_chance():
    assert cohen_kappa([1, 1, 1, 1], [1, 0, 1, 0]) <= 0.0


def test_mode():
    assert decide_mode(0.70) == "hard_gate"
    assert decide_mode(0.65) == "hard_gate"
    assert decide_mode(0.64) == "soft_signal"
