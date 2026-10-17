"""Tests for the Figure 3 scorers and the round-2 protocol generator. Run: python -m unittest discover -s . -p 'test_*.py'"""
import csv
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import tifffile

from common.paths import REPO_ROOT
from fig3.round2 import make_scenarios, score_round2
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
        """Held-out reference counts stated in STRATEGY.md: 233 nuclei, 51 cancer cells, 181 endothelial cells."""
        empty = np.zeros_like(reference("cancer"))
        counts = {task: score_heldout(task, empty)["n_ref"] for task in TASKS}
        self.assertEqual(counts, {"nuclei": 233, "cancer": 51, "endo": 181})

    def test_wrong_shape_raises(self):
        with self.assertRaises(ValueError):
            score("cancer", np.zeros((10, 10), int))


class ScoreRound2Tests(unittest.TestCase):
    def _run_dir(self, meta: dict) -> Path:
        run_dir = Path(tempfile.mkdtemp())
        (run_dir / "meta.json").write_text(json.dumps(meta))
        return run_dir

    def test_code_run_with_perfect_labels(self):
        run_dir = self._run_dir({"row": "code_python", "task": "cancer", "condition": "box1"})
        tifffile.imwrite(run_dir / "labels.tif", reference("cancer").astype(np.int32))
        self.assertEqual(score_round2.score_run(run_dir)["f1_heldout"], 1.0)

    def test_missing_labels_is_a_crash(self):
        run_dir = self._run_dir({"row": "code_fiji", "task": "nuclei", "condition": "generic"})
        self.assertEqual(score_round2.score_run(run_dir), {"crashed": True, "f1_heldout": 0.0})

    def test_direct_answer_invalid_outlines_and_missing_count(self):
        run_dir = self._run_dir({"row": "direct", "task": "cancer", "condition": "box1"})
        (run_dir / "reply.json").write_text(json.dumps({"cells": [{"points": [[1, 1]]}, {"points": [[600, 100], [640, 100], [640, 140]]}]}))
        result = score_round2.score_run(run_dir)
        self.assertEqual((result["n_invalid_outlines"], result["count_error"]), (1, None))


class ProtocolTests(unittest.TestCase):
    def test_prompts_are_complete_and_paired(self):
        prompts = make_scenarios.build_prompts()
        self.assertEqual(len(prompts), 30)
        for prompt_id, text in prompts.items():
            if not prompt_id.startswith("direct"):
                self.assertNotIn("[", text.replace("[[x, y], ...]", ""), prompt_id)
        for task in make_scenarios.TASKS:
            for row in ("advice", "code_python", "code_fiji"):
                first_generic = prompts[f"{row}_generic_{task}"].split("\n")[0]
                self.assertTrue(prompts[f"{row}_box1_{task}"].startswith(first_generic), f"{row} {task}")

    def test_committed_scenarios_match_generator(self):
        """The committed prompt files and scenarios.csv are what the generator produces (nothing edited by hand)."""
        prompts = make_scenarios.build_prompts()
        for prompt_id, text in prompts.items():
            self.assertEqual((REPO_ROOT / "fig3/round2/prompts" / f"{prompt_id}.txt").read_text(), text + "\n", prompt_id)
        rows = list(csv.DictReader(open(REPO_ROOT / "fig3/round2/scenarios.csv")))
        self.assertEqual(len(rows), 162)
        self.assertEqual(len({r["scenario_id"] for r in rows}), 162)
        for r in rows:
            if r["row"].startswith("code"):
                self.assertTrue(r["attach"].startswith("image.tif <- "), r["scenario_id"])


if __name__ == "__main__":
    unittest.main()
