import numpy as np

from scripts.phase0_pose_calibration import silhouette_iou


def test_silhouette_iou_identical_is_one():
    mask = np.zeros((64, 64), dtype=bool)
    mask[16:48, 16:48] = True
    assert silhouette_iou(mask, mask) == 1.0


def test_silhouette_iou_disjoint_is_zero():
    a = np.zeros((64, 64), dtype=bool)
    a[0:10, 0:10] = True
    b = np.zeros((64, 64), dtype=bool)
    b[40:50, 40:50] = True
    assert silhouette_iou(a, b) == 0.0


def test_silhouette_iou_half_overlap():
    a = np.zeros((10, 10), dtype=bool)
    a[:, 0:5] = True
    b = np.zeros((10, 10), dtype=bool)
    b[:, 2:7] = True
    # intersection cols 2-4 (3 wide x 10 = 30), union cols 0-6 (7 wide x 10 = 70)
    assert round(silhouette_iou(a, b), 4) == round(30 / 70, 4)
