"""Tests for the Figure 3 scorers and the round-2 protocol generator. Run: python -m unittest discover -s . -p 'test_*.py'"""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import tifffile

from common.paths import REPO_ROOT
from fig3.v2 import score as v2score
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


class ScoreRound2Tests(unittest.TestCase):
    """Round 2 scores the test field (209) against its manual annotation and never crashes on bad outputs."""

    def _run_dir(self, meta: dict) -> Path:
        run_dir = Path(tempfile.mkdtemp())
        (run_dir / "meta.json").write_text(json.dumps(meta))
        return run_dir

    def test_code_run_with_perfect_labels(self):
        run_dir = self._run_dir({"row": "code_python", "task": "cancer", "condition": "box1"})
        tifffile.imwrite(run_dir / "labels.tif", reference("cancer", 209).astype(np.int32))
        self.assertEqual(v2score.score_run(run_dir)["f1"], 1.0)

    def test_dev_field_labels_score_low_on_test_field(self):
        """Labels of the development field are not a solution for the test field."""
        run_dir = self._run_dir({"row": "optimise", "task": "cancer", "condition": "generic"})
        tifffile.imwrite(run_dir / "labels.tif", reference("cancer", 104).astype(np.int32))
        self.assertLess(v2score.score_run(run_dir)["f1"], 0.2)

    def test_missing_labels_is_a_crash(self):
        run_dir = self._run_dir({"row": "code_fiji", "task": "nuclei", "condition": "generic"})
        self.assertEqual(v2score.score_run(run_dir), {"status": "crashed", "f1": 0.0})

    def test_manual_counts_come_from_annotations(self):
        self.assertEqual({t: v2score.manual_count(t) for t in TASKS}, {"nuclei": 473, "cancer": 163, "endo": 388})

    def test_direct_outlines_audit(self):
        run_dir = self._run_dir({"row": "direct", "task": "cancer", "condition": "box1"})
        square = [[600, 100], [640, 100], [640, 140], [600, 140]]
        (run_dir / "reply.json").write_text(json.dumps(
            {"count": 5, "cells": [{"points": [[1, 1]]}, {"points": square}, {"points": square},
                                   {"points": [[5000, 5000], [5010, 5000], [5010, 5010]]}]}))
        r = v2score.score_run(run_dir)
        self.assertEqual((r["n_invalid"], r["n_empty_or_outside"], r["n_valid"], r["stated_minus_valid_outlines"]), (1, 1, 2, 3))
        self.assertGreater(r["overlap_px"], 0)

    def test_malformed_direct_outputs_are_recorded(self):
        run_dir = self._run_dir({"row": "direct", "task": "endo", "condition": "box1"})
        (run_dir / "reply.json").write_text("{not json")
        self.assertEqual(v2score.score_run(run_dir)["status"], "invalid_json")
        run_dir = self._run_dir({"row": "direct", "task": "endo", "condition": "generic"})
        (run_dir / "stated_count.txt").write_text("about three hundred")
        self.assertEqual(v2score.score_run(run_dir)["status"], "invalid_count")
        (run_dir / "stated_count.txt").write_text("300-340")
        self.assertEqual(v2score.score_run(run_dir)["stated_count"], 320)


class AssetTests(unittest.TestCase):
    def test_test_annotation_is_never_an_asset(self):
        """No asset hands a model the test-field (209) annotation."""
        assets = {p.name for p in (REPO_ROOT / "fig3/v2/assets").iterdir()}
        self.assertFalse([a for a in assets if a.startswith("test_") and "annotation" in a])


if __name__ == "__main__":
    unittest.main()
