"""Tests for common.matching on synthetic label images with known answers. Run: python -m unittest discover common"""
import unittest

import numpy as np

from common.matching import f1_score, match


def discs(centres, radius, shape=(100, 100)):
    """Label image with one disc per centre (labels 1..n)."""
    yy, xx = np.mgrid[: shape[0], : shape[1]]
    out = np.zeros(shape, dtype=np.int32)
    for k, (cy, cx) in enumerate(centres, start=1):
        out[(yy - cy) ** 2 + (xx - cx) ** 2 <= radius ** 2] = k
    return out


class MatchingTests(unittest.TestCase):
    def test_identical_images_give_f1_one(self):
        gt = discs([(20, 20), (60, 60)], 8)
        self.assertEqual(f1_score(gt, gt)["f1"], 1.0)

    def test_relabelling_does_not_change_score(self):
        gt = discs([(20, 20), (60, 60)], 8)
        pr = np.where(gt > 0, 3 - gt, 0)
        self.assertEqual(f1_score(gt, pr)["tp"], 2)

    def test_missed_and_false_objects(self):
        gt = discs([(20, 20), (60, 60)], 8)
        pr = discs([(20, 20), (80, 20)], 8)
        s = f1_score(gt, pr)
        self.assertEqual((s["tp"], s["fn"], s["fp"]), (1, 1, 1))
        self.assertAlmostEqual(s["f1"], 0.5)

    def test_iou_below_threshold_is_not_a_match(self):
        gt = discs([(50, 50)], 10)
        pr = discs([(50, 62)], 10)  # shifted by more than one radius: IoU < 0.5
        self.assertEqual(len(match(gt, pr)[0]), 0)

    def test_one_to_one(self):
        gt = discs([(50, 45), (50, 55)], 5)
        pr = np.where(gt > 0, 1, 0)  # one predicted object covering both references
        self.assertLessEqual(len(match(gt, pr)[0]), 1)

    def test_shape_mismatch_raises(self):
        with self.assertRaises(ValueError):
            match(np.zeros((5, 5), int), np.zeros((6, 5), int))


if __name__ == "__main__":
    unittest.main()
