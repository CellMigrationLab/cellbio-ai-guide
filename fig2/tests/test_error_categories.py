"""Synthetic cases for the heuristic error categories of fig2/code/errors.py (audit P1.12)."""
import importlib.util
import unittest

import numpy as np

from common.paths import REPO_ROOT

_spec = importlib.util.spec_from_file_location("fig2_errors", REPO_ROOT / "fig2/code/errors.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
errors = _mod.errors


def boxes(spec, shape=(30, 60)):
    out = np.zeros(shape, dtype=np.int32)
    for lab, (y0, y1, x0, x1) in spec.items():
        out[y0:y1, x0:x1] = lab
    return out


REF = boxes({1: (0, 10, 0, 10), 2: (0, 10, 12, 22), 3: (15, 25, 0, 20), 4: (15, 25, 40, 50)})


class ErrorCategories(unittest.TestCase):
    def test_merge_split_missed_false(self):
        pred = boxes({1: (0, 10, 0, 22),        # covers references 1 and 2 -> one merge
                      2: (15, 25, 0, 9), 3: (15, 25, 11, 20),    # two parts of reference 3 (IoU 0.45 each) -> one split
                      4: (0, 10, 40, 50)})      # nothing there -> false; reference 4 not found -> missed
        counts, ids = errors(pred, REF)
        self.assertEqual((counts["merges"], counts["splits"], counts["missed"], counts["false"]), (1, 1, 1, 1))
        self.assertEqual(ids, {"missed": [4], "false": [4], "merged": [1], "split": [3]})
        self.assertEqual(counts["tp"], 0)

    def test_split_part_at_iou_half_is_also_a_match(self):
        """Documented overlap of the two rules: a part covering exactly half a reference object has IoU 0.5, so it is
        a true positive for F1, while the reference object is still counted as split."""
        pred = boxes({1: (15, 25, 0, 10), 2: (15, 25, 10, 20)})
        counts, ids = errors(pred, REF)
        self.assertEqual((counts["tp"], counts["splits"]), (1, 1))

    def test_perfect_prediction_has_no_errors(self):
        counts, _ = errors(REF.copy(), REF)
        self.assertEqual((counts["f1"], counts["merges"], counts["splits"], counts["missed"], counts["false"]),
                         (1.0, 0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
