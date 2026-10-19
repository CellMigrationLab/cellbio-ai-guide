"""Task references and the shared task scorer (fig3/scoring/tasks.py); v2 harness tests are in test_v2_harness.py."""
import unittest

import numpy as np

from common.paths import REPO_ROOT
from fig3.scoring.tasks import TASKS, reference, score, score_heldout


class TaskScorerTests(unittest.TestCase):
    def test_reference_scores_one(self):
        """Cancer and endothelial references scored against themselves give F1 1."""
        for task in ("cancer", "endo"):
            self.assertEqual(score(task, reference(task))["f1"], 1.0)
            self.assertEqual(score_heldout(task, reference(task))["f1"], 1.0)

    def test_nuclei_perfect_prediction_scores_one(self):
        """Round-2 rule: the full manual reference (441 nuclei, incl. 17 under cancer cells) is always used; a perfect
        prediction scores F1 1 on the whole field and on the held-out half."""
        self.assertEqual(score("nuclei", reference("nuclei"))["f1"], 1.0)
        self.assertEqual(score_heldout("nuclei", reference("nuclei"))["f1"], 1.0)

    def test_nuclei_round1_rule_ceiling(self):
        """Round-1 rule (drop before matching) loses the 17 annotated nuclei under cancer cells: F1 0.98."""
        result = score("nuclei", reference("nuclei"), nuclei_rule="drop_first")
        self.assertEqual((result["fn"], result["f1"]), (17, 0.98))

    def test_unmatched_cancer_nuclei_are_not_false_positives(self):
        """An extra predicted object inside a cancer cell (an unannotated cancer-cell nucleus) is ignored."""
        pred = reference("nuclei").copy()
        ys, xs = np.nonzero(reference("cancer") > 0)
        free = (reference("nuclei")[ys, xs] == 0)
        y, x = ys[free][0], xs[free][0]
        pred[y, x] = pred.max() + 1
        self.assertEqual(score("nuclei", pred)["fp"], 0)

    def test_heldout_counts_match_strategy(self):
        """Round-1 held-out halves (right half of field 104): 233 nuclei, 51 cancer cells, 181 endothelial cells."""
        empty = np.zeros_like(reference("cancer"))
        counts = {task: score_heldout(task, empty)["n_ref"] for task in TASKS}
        self.assertEqual(counts, {"nuclei": 233, "cancer": 51, "endo": 181})

    def test_wrong_shape_raises(self):
        with self.assertRaises(ValueError):
            score("cancer", np.zeros((10, 10), int))


class AssetTests(unittest.TestCase):
    def test_test_annotation_is_never_an_asset(self):
        """No asset hands a model the test-field (209) annotation."""
        assets = {p.name for p in (REPO_ROOT / "fig3/v2/assets").iterdir()}
        self.assertFalse([a for a in assets if a.startswith("test_") and "annotation" in a])


if __name__ == "__main__":
    unittest.main()


class HeldoutHalf(unittest.TestCase):
    """Protocol v2 rows B and C are scored on the right half (x >= 512) of fields 104 and 209."""

    def test_reference_scores_one_on_both_fields(self):
        from fig3.scoring.tasks import reference, score_heldout
        for field in (104, 209):
            for task in ("nuclei", "cancer", "endo"):
                self.assertEqual(score_heldout(task, reference(task, field), field=field)["f1"], 1.0, (task, field))

    def test_mosaic_annotation_is_the_left_halves(self):
        import numpy as np
        import tifffile
        from common.paths import REPO_ROOT
        from fig3.scoring.tasks import HALF_X, reference
        for task in ("nuclei", "cancer", "endo"):
            mosaic = tifffile.imread(REPO_ROOT / "fig3" / "v2" / "assets" / f"halfdev_{task}_annotation.tif")
            self.assertTrue(np.array_equal(mosaic[:, :HALF_X] > 0, reference(task, 104)[:, :HALF_X] > 0))
            self.assertTrue(np.array_equal(mosaic[:, HALF_X:] > 0, reference(task, 209)[:, :HALF_X] > 0))
