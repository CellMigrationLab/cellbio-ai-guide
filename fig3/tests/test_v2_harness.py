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
        self.assertEqual(score.parse_count("I count roughly **110 cells**; the 2-3 clumps are hard.")["count"], 110)
        self.assertEqual(score.parse_count("1. **Count:** about 95 to 105 nuclei"), {"count": 100.0, "range": [95, 105]})


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


class Operator(unittest.TestCase):
    def test_answers_must_come_from_the_sheet(self):
        from fig3.v2.run_operator import from_answer_sheet
        self.assertTrue(from_answer_sheet("0.65 µm per pixel, from the metadata. I don't know."))
        self.assertFalse(from_answer_sheet("0.65 µm per pixel, from the metadata. Use Cellpose."))

    def test_script_selection_prefers_the_latest_complete_script(self):
        from fig3.v2.run_operator import analysis_block
        full = "```python\nsave('labels.tif'); save('measurements.csv')\n```"
        patch = "```python\nx = 1\n```"
        evaluation = "```python\nread('labels.tif')\n```"
        self.assertEqual(analysis_block([full + evaluation, patch])[:2], (0, 0))
        self.assertEqual(analysis_block([patch, evaluation])[:2], (1, 0))

    def test_pip_packages(self):
        from fig3.v2.run_operator import pip_packages
        text = "Run `pip install -U cellpose tifffile` then\npip install stardist==0.9.2"
        self.assertEqual(pip_packages(text), ["cellpose", "tifffile", "stardist==0.9.2"])

    def test_shell_paths(self):
        from fig3.v2.run_operator import environment_path, shell_paths_outside
        folder = Path("/home/user/sessions_v2/v001")
        self.assertEqual(shell_paths_outside("python a.py image.tif out.tif", folder), [])
        self.assertEqual(shell_paths_outside("cat ../v002/x.tif", folder), ["../v002/x.tif"])
        self.assertEqual(shell_paths_outside("ls ~/.cellpose/models", folder), [str(Path.home() / ".cellpose/models")])
        self.assertTrue(environment_path(str(Path.home() / ".cellpose/models")))
        self.assertEqual(shell_paths_outside("y = a / b + '/x.npy'", folder), [])
        self.assertIn("/home/user", shell_paths_outside("ls /home/user", folder))


class RuntimeManifest(unittest.TestCase):
    def test_any_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name in ("pipeline.py", "weights.npy", "annotation.tif", "image.tif"):
                (folder / name).write_text("x")
            (folder / "runtime_manifest.json").write_text(json.dumps(
                {"required_files": ["pipeline.py", "weights.npy"], "note": "a sentence, not a file", "x": ["annotation.tif", "image.tif"]}))
            self.assertEqual(runner.manifest_names(folder), ["pipeline.py", "weights.npy", "annotation.tif", "image.tif"])
            self.assertEqual([p.name for p in runner.runtime_files(folder)], ["weights.npy"])


if __name__ == "__main__":
    unittest.main()
