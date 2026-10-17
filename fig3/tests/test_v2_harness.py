"""Protocol v2 runner and scorer on synthetic runs (crash, timeout, no output, perfect output, measurement table,
direct-answer ellipses)."""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import tifffile
from skimage.measure import regionprops

from fig3.scoring.tasks import reference
from fig3.v2 import runner, score
from fig3.v2.make_protocol import build_prompts, build_scenarios


def make_run(tmp: Path, script: str, task: str = "cancer") -> Path:
    run = tmp / f"code_simple_{task}_r1"
    run.mkdir()
    (run / "meta.json").write_text(json.dumps({"row": "code", "task": task}))
    (run / "code_as_returned.py").write_text(script)
    return run


def write_measurements(path: Path, labels: np.ndarray, area_factor: float = 1.0) -> None:
    rows = ["label,area_um2,aspect_ratio"]
    for r in regionprops(labels):
        ar = r.axis_major_length / r.axis_minor_length if r.axis_minor_length >= 2 else 1.0
        rows.append(f"{r.label},{r.area * 0.649614 ** 2 * area_factor},{ar}")
    path.write_text("\n".join(rows) + "\n")


class Runner(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self._root = runner.EXEC_ROOT
        runner.EXEC_ROOT = self.tmp / "exec"

    def tearDown(self):
        runner.EXEC_ROOT = self._root
        self._tmp.cleanup()

    def test_perfect_script_scores_one(self):
        ref = self.tmp / "ref.tif"
        tifffile.imwrite(ref, reference("cancer", 209).astype(np.uint16))
        run = make_run(self.tmp, f"import shutil\nshutil.copyfile({str(ref)!r}, 'labels.tif')\n")
        self.assertEqual(runner.run_field(run, 209)["status"], "ok")
        write_measurements(run / "measurements_f209.csv", reference("cancer", 209))
        s = score.score_field(run, "cancer", 209)
        self.assertEqual(s["f1"], 1.0)
        self.assertEqual(s["count_error"], 0)
        self.assertEqual(s["measurements_csv"]["status"], "consistent")
        write_measurements(run / "measurements_f209.csv", reference("cancer", 209), area_factor=1.1)
        self.assertEqual(score.score_field(run, "cancer", 209)["measurements_csv"]["status"], "inconsistent")

    def test_labels_written_then_crash_is_a_crash(self):
        ref = self.tmp / "ref.tif"
        tifffile.imwrite(ref, reference("cancer", 209).astype(np.uint16))
        run = make_run(self.tmp, f"import shutil, sys\nshutil.copyfile({str(ref)!r}, 'labels.tif')\nsys.exit(1)\n")
        self.assertEqual(runner.run_field(run, 209)["status"], "crashed")
        self.assertFalse((run / "labels_f209.tif").exists())
        self.assertEqual(score.score_field(run, "cancer", 209), {"status": "crashed", "f1": 0.0})

    def test_no_output_and_timeout(self):
        run = make_run(self.tmp, "print('nothing written')\n")
        self.assertEqual(runner.run_field(run, 104)["status"], "no_output")
        old = runner.TIMEOUT_S
        runner.TIMEOUT_S = 2
        try:
            run2 = make_run(self.tmp / "", "import time\nopen('labels.tif', 'w').write('x')\ntime.sleep(30)\n", task="nuclei")
            self.assertEqual(runner.run_field(run2, 104)["status"], "timeout")
            self.assertFalse((run2 / "labels_f104.tif").exists())
        finally:
            runner.TIMEOUT_S = old

    def test_invalid_labels(self):
        run = make_run(self.tmp, "import numpy as np, tifffile\ntifffile.imwrite('labels.tif', np.random.rand(1022, 1024).astype('float32'))\n")
        self.assertEqual(runner.run_field(run, 209)["status"], "ok")
        self.assertEqual(score.score_field(run, "cancer", 209)["status"], "invalid_labels")


class Direct(unittest.TestCase):
    def test_centres_at_reference_objects(self):
        centroids = [(r.centroid[1], r.centroid[0]) for r in regionprops(reference("cancer", 209))]
        m = score.match_centres("cancer", 209, centroids)
        self.assertEqual((m["tp"], m["fp"], m["fn"], m["f1"]), (len(centroids), 0, 0, 1.0))
        m = score.match_centres("cancer", 209, centroids + centroids[:5] + [(-5.0, -5.0)])
        self.assertEqual((m["fp"], m["fn"]), (6, 0))

    def test_parse_count_keeps_range(self):
        self.assertEqual(score.parse_count("between 300 and 340, roughly 300-340"), {"count": 320.0, "range": [300, 340]})
        self.assertEqual(score.parse_count("about 1,250 cells")["count"], 1250)


class Protocol(unittest.TestCase):
    def test_numbers_and_pairing(self):
        prompts, scenarios = build_prompts(), build_scenarios()
        self.assertEqual(len(scenarios), 72)
        self.assertEqual(len({s["scenario_id"] for s in scenarios}), 72)
        for p, text in prompts.items():
            self.assertNotIn("[", text.replace('[{"x"', "").replace("...]", ""), p)
        for task in ("nuclei", "cancer", "endo"):
            for row in ("advice", "code"):
                self.assertEqual(prompts[f"{row}_simple_{task}"].split("\n")[0], prompts[f"{row}_box1_{task}"].split("\n")[0])
            for phrase in ("manual annotation", "annotated example", "annotation.tif"):
                self.assertNotIn(phrase, prompts[f"optimise_by_eye_{task}"])
                self.assertIn(phrase, prompts[f"optimise_labels_{task}"])
        for s in scenarios:
            self.assertNotIn("test_" + s["task"] + "_annotation", s["folder_files"])
            if s["row"] in ("code", "optimise"):
                self.assertIn(f"dev_{s['task']}_image.tif", s["folder_files"])


if __name__ == "__main__":
    unittest.main()
