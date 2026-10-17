"""Edge cases of common.matching (audit P1.9): IoU exactly at the threshold, empty images, ties, and greedy = optimal.

Why greedy matching is optimal here: label images do not overlap within themselves, so for IoU > 0.5 each reference
object can have at most one prediction with IoU > 0.5 (and vice versa); the candidate pairs then form a matching
already, and any order of acceptance gives the same result. At exactly 0.5 two candidates per object are possible in
principle; the tie test documents the deterministic choice.
"""
import itertools
import unittest

import numpy as np

from common.matching import f1_score, match


def boxes(spec, shape=(20, 40)):
    """Label image from {label: (y0, y1, x0, x1)} rectangles."""
    out = np.zeros(shape, dtype=np.int32)
    for lab, (y0, y1, x0, x1) in spec.items():
        out[y0:y1, x0:x1] = lab
    return out


def optimal_tp(gt, pr, thr):
    """Maximum number of one-to-one pairs with IoU >= thr, by brute force (small images only)."""
    g_ids, p_ids = [i for i in np.unique(gt) if i], [i for i in np.unique(pr) if i]
    ok = {(g, p) for g in g_ids for p in p_ids
          if (n := np.sum((gt == g) & (pr == p))) and n / (np.sum(gt == g) + np.sum(pr == p) - n) >= thr}
    best = 0
    for k in range(min(len(g_ids), len(p_ids)), 0, -1):
        for gs in itertools.combinations(g_ids, k):
            for ps in itertools.permutations(p_ids, k):
                if all((g, p) in ok for g, p in zip(gs, ps)):
                    return k
    return best


class EdgeCases(unittest.TestCase):
    def test_iou_exactly_at_threshold_is_a_match(self):
        gt = boxes({1: (0, 10, 0, 10)})            # 100 px
        pr = boxes({1: (0, 10, 0, 15)})            # 150 px, overlap 100 -> IoU 100/150 = 0.667
        self.assertEqual(len(match(gt, pr, 0.5)[0]), 1)
        pr = boxes({1: (0, 10, 0, 20)})            # 200 px, overlap 100 -> IoU exactly 0.5
        matched, fn, fp = match(gt, pr, 0.5)
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0][2], 0.5)

    def test_empty_images(self):
        empty = np.zeros((20, 40), dtype=np.int32)
        one = boxes({1: (0, 10, 0, 10)})
        self.assertEqual(match(empty, empty), ([], set(), set()))
        self.assertEqual(f1_score(empty, one)["fp"], 1)
        self.assertEqual(f1_score(one, empty)["fn"], 1)
        self.assertEqual(f1_score(empty, empty)["f1"], 0.0)  # documented convention: no objects -> F1 0

    def test_tie_is_resolved_deterministically(self):
        gt = boxes({1: (0, 10, 0, 20)})            # 200 px
        pr = boxes({1: (0, 10, 0, 10), 2: (0, 10, 10, 20)})  # each half: IoU exactly 0.5
        first = match(gt, pr, 0.5)
        self.assertEqual(len(first[0]), 1)
        self.assertEqual(first, match(gt, pr, 0.5))

    def test_greedy_equals_optimal_on_random_layouts(self):
        rng = np.random.default_rng(0)
        for _ in range(200):
            gt = boxes({k + 1: (int(y), int(y) + 6, int(x), int(x) + 6)
                        for k, (y, x) in enumerate(zip(rng.integers(0, 14, 4), rng.integers(0, 34, 4)))})
            pr = boxes({k + 1: (int(y), int(y) + 6, int(x), int(x) + 6)
                        for k, (y, x) in enumerate(zip(rng.integers(0, 14, 4), rng.integers(0, 34, 4)))})
            for thr in (0.5, 0.6):
                self.assertEqual(len(match(gt, pr, thr)[0]), optimal_tp(gt, pr, thr))


if __name__ == "__main__":
    unittest.main()
