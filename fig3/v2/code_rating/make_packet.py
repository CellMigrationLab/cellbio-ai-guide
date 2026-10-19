"""Blind packet for rating the readability and debuggability of the row B scripts (an optional, exploratory analysis).

Copies each returned script (code_as_returned.py, unchanged) to script_01.py ... script_NN.py in a fixed-seed random order,
writes the rubric and a rater prompt, and zips them (scripts_for_rating.zip). The key that maps script numbers back to
scenario, condition and task is written to key.csv, outside the zip.
Usage: PYTHONPATH=. python fig3/v2/code_rating/make_packet.py
"""
import csv
import json
import random
import zipfile

from common.paths import REPO_ROOT

RUNS = REPO_ROOT / "fig3" / "v2" / "runs"
OUT = REPO_ROOT / "fig3" / "v2" / "code_rating"
SEED = 20261019
RUBRIC = """Rate each script from 1 (poor) to 5 (excellent) on each item. Judge only what you can read; do not run the code.

1. Readability: can you follow the steps from input to output without effort?
2. Visible parameters: are the important choices (pixel size, model, diameters, thresholds, size limits) named and easy to find and change?
3. Debuggability: if the result were wrong, how easily could you find which step is responsible (separate steps, intermediate outputs, logging)?
4. Error handling: does it check its inputs and fail with an informative message, rather than silently continuing or guessing?
5. Testability: could you test or replace one step on its own?
6. Overall complexity (1 = far more complicated than needed, 5 = as simple as the task allows).
"""
PROMPT = """You are an experienced scientific Python reviewer. Each file script_NN.py is a Python script that segments cells in a
microscopy image and writes labels.tif and measurements.csv (one row per object: label, area in um^2, aspect ratio).
Score every script on the six items of rubric.md, from 1 to 5. Do not run the code and do not try to guess who wrote it.
Return one CSV table with the columns: script, readability, visible_parameters, debuggability, error_handling, testability,
overall_complexity, and one sentence of justification per script. Score all scripts with the same standard.
"""


def main() -> None:
    items = []
    for run in sorted(RUNS.glob("code_*")):
        script = run / "code_as_returned.py"
        if script.exists() and (run / "meta.json").exists():
            meta = json.loads((run / "meta.json").read_text())
            items.append((run.name, meta["condition"], meta["task"], script))
    random.Random(SEED).shuffle(items)
    for old in OUT.glob("script_*.py"):
        old.unlink()
    zip_path = OUT / "scripts_for_rating.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z, (OUT / "key.csv").open("w", newline="") as handle:
        key = csv.writer(handle, lineterminator="\n")
        key.writerow(["script", "scenario_id", "condition", "task"])
        for i, (sid, cond, task, script) in enumerate(items, start=1):
            name = f"script_{i:02d}.py"
            z.writestr(name, script.read_text())
            key.writerow([name, sid, cond, task])
        z.writestr("rubric.md", RUBRIC)
        z.writestr("prompt.txt", PROMPT)
    print(len(items), "scripts ->", zip_path.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
