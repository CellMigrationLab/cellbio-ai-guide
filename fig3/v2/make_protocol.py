"""Generate the protocol-v2 prompts, row table and scenario list (fig3/PROTOCOL_V2.md, sections 3-5).

Single source of the Box 1 text: box1/box1_final.md. Writes, in fig3/v2/:
  prompts/<prompt_id>.txt   first message of every scenario type (without the framing, which depends on the folder)
  rows.csv                  per row: tools of the headless subject session, offered tools, framing sentence (used by framing, audit, metadata)
  scenarios.csv             one row per subject run, in a randomised order fixed by SEED
Usage: PYTHONPATH=. python fig3/v2/make_protocol.py
"""
from __future__ import annotations

import csv
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "fig3" / "v2"
SEED = 20261018
REPLICATES = 3
TASKS = {
    "nuclei": dict(objects="endothelial nuclei", one="endothelial nucleus", channels="1 (DAPI)", size="13–17 µm",
                   images="widefield fluorescence images of a DAPI-stained endothelial monolayer (cancer cells sit on top)"),
    "cancer": dict(objects="cancer cells", one="cancer cell", channels="1 (brightfield)", size="15–25 µm",
                   images="brightfield images of cancer cells sitting on top of a confluent endothelial monolayer"),
    "endo": dict(objects="endothelial cells", one="endothelial cell", channels="1 (brightfield)", size="25–50 µm",
                 images="brightfield images of a confluent endothelial monolayer (some cancer cells sit on top)"),
}
HELP = {"advice": "choose an analysis approach.", "code": "write the analysis as a Python script.",
        "optimise": "run and optimise the workflow."}
SOFTWARE = {"advice": "Python 3.13", "code": "Python 3.13",
            "optimise": "Python 3.13 with numpy, scipy, scikit-image, tifffile and Cellpose 4.2"}
CODE_IO = ("The image is image.tif; the script should read it from the working directory and save the label image as "
           "labels.tif and a table with one row per object (label, area in µm², aspect ratio) as measurements.csv.")
OPTIMISE_REQUEST = ("Please write a Python script for this analysis, run it on image.tif in this folder, look at the "
                    "result and improve the script until you are satisfied. Save the final script as pipeline.py so "
                    "that it runs unchanged as `python pipeline.py <input.tif> <labels.tif> <measurements.csv>`, list "
                    "any other file it needs in runtime_manifest.json, keep a log of each change in log.txt and report "
                    "your final result.")
# phrases of Box 1 that mention the annotation; removed in the by-eye arm of row C (the only difference between arms)
ANNOTATION_PHRASES = (" I can provide a manual annotation of this image (a label image).",
                      " Include a test I can run on my annotated example and tell me what result would mean that the "
                      "analysis failed.")
WEB = "You can search the web (WebSearch and WebFetch; load them with ToolSearch if they are not listed)."
ROWS = {  # row: (tools given to the headless subject session, tools offered, framing; {folder} filled per scenario)
    "advice": ("WebSearch,WebFetch", "web", f"{WEB} You cannot run code."),
    "code": ("Read,WebSearch,WebFetch", "web; view attachment",
             f"{WEB} The user attached a file, which you can view: {{folder}}/image.png. You cannot run code; the user "
             "will run your script."),
    "optimise": ("Read,Write,Edit,Bash,Glob,Grep,WebSearch,WebFetch", "web; shell in its folder",
                 f"{WEB} You can run shell commands in the folder {{folder}} only."),
    "direct": ("Read", "view attachment",
               "The user attached a file, which you can view: {folder}/image.png. You cannot run code."),
}
FRAMING = "You are an AI assistant chatting with a user. {tools} Reply to the user as you normally would."


def task_sentence(task: str) -> str:
    t = TASKS[task]
    return (f"I want to segment and count the {t['objects']} and measure their shape (area and aspect ratio) from "
            f"{t['images']}.")


def box1_template() -> str:
    text = (ROOT / "box1" / "box1_final.md").read_text()
    return re.search(r"```text\n(.*?)```", text, re.S).group(1).replace("➕", "").strip()


def fill_box1(task: str, row: str, arm: str = "") -> str:
    """Box 1 filled for a task and row ('advice', 'code' or 'optimise'); arm 'by_eye' removes the annotation phrases."""
    t = TASKS[task]
    box, optimisation = box1_template().split("\n\nIf you are allowed to optimise")
    replacements = {
        "[biological question or measurement] from [type of microscopy images]": task_sentence(task)[len("I want to "):-1],
        "[choose an analysis approach / write the analysis / run or optimise the workflow].": HELP[row],
        "[2D/3D/time series]": "2D", "[e.g. T, Z, C, Y, X]": "Y, X", "[channels]": t["channels"],
        "[dtype]": "uint16 (12-bit values)", "[X µm]": "0.65 µm", "[X–Y µm]": t["size"],
        "[software and version]": SOFTWARE[row], "[hardware]": "a laptop CPU (no GPU)",
        "[measurement/output]": (f"a label image with one integer per {t['one']} (0 = background) and a table with the "
                                 f"area (µm²) and aspect ratio of each {t['one']}"),
        "[representative images/annotations/reference measurements / expected outputs]":
            "a manual annotation of this image (a label image)",
    }
    for key, value in replacements.items():
        if key not in box:
            raise KeyError(f"{key!r} not found while filling Box 1")
        box = box.replace(key, value)
    if row == "optimise":
        dev = ("image.tif and its annotation annotation.tif in this folder" if arm == "labels"
               else "image.tif in this folder")
        opt = ("If you are allowed to optimise" + optimisation).replace("[development data]", dev) \
            .replace("[held-out data]", "any other image (my other images are held out and not in this folder)") \
            .replace("[working folder]", "this folder")
        box += "\n\n" + opt + "\nYou are allowed to optimise the workflow. " + OPTIMISE_REQUEST
    if arm == "by_eye":
        for phrase in ANNOTATION_PHRASES:
            if phrase not in box:
                raise KeyError(f"annotation phrase not found: {phrase!r}")
            box = box.replace(phrase, "")
    if "[" in box:
        raise ValueError(f"unfilled placeholder in Box 1 for {task}/{row}: {re.findall(r'\[[^]]*\]', box)}")
    return box


def first_line(task: str, row: str) -> str:
    return f"{task_sentence(task)} Help me {HELP[row]}"


def build_prompts() -> dict[str, str]:
    prompts = {}
    for task, t in TASKS.items():
        prompts[f"advice_simple_{task}"] = first_line(task, "advice")
        prompts[f"advice_box1_{task}"] = fill_box1(task, "advice")
        prompts[f"code_simple_{task}"] = first_line(task, "code") + "\n" + CODE_IO
        prompts[f"code_box1_{task}"] = fill_box1(task, "code") + "\n" + CODE_IO
        for arm in ("by_eye", "labels"):
            prompts[f"optimise_{arm}_{task}"] = fill_box1(task, "optimise", arm)
        prompts[f"direct_turn1_{task}"] = f"How many {t['objects']} are in this image?"
        prompts[f"direct_turn2_{task}"] = ("What are their typical size and shape? Give the median area in µm² and the "
                                          "median aspect ratio. The pixel size is 0.65 µm.")
        prompts[f"direct_turn3_{task}"] = (
            f"Please draw an ellipse around every {t['one']} in this image and give, from your drawing, the count, the "
            "median area in µm² and the median aspect ratio. Give the ellipses as JSON in the pixel coordinates of the "
            'image (origin top-left, x to the right, y down): {"count": n, "median_area_um2": a, '
            '"median_aspect_ratio": r, "ellipses": [{"x": , "y": , "major": , "minor": , "angle_deg": }, ...]} '
            "(major and minor = full axis lengths in pixels).")
    return prompts


def build_scenarios() -> list[dict]:
    rows = []
    for task in TASKS:
        for rep in range(1, REPLICATES + 1):
            for cond in ("simple", "box1"):
                rows.append(dict(row="advice", condition=cond, task=task, field="", replicate=rep,
                                 prompt=f"advice_{cond}_{task}", folder_files=""))
                rows.append(dict(row="code", condition=cond, task=task, field="", replicate=rep,
                                 prompt=f"code_{cond}_{task}",
                                 folder_files=f"image.tif <- halfdev_{task}_image.tif; image.png <- halfdev_{task}_image.png"))
            for arm in ("by_eye", "labels"):
                files = f"image.tif <- halfdev_{task}_image.tif"
                if arm == "labels":
                    files += f"; annotation.tif <- halfdev_{task}_annotation.tif"
                rows.append(dict(row="optimise", condition=arm, task=task, field="", replicate=rep,
                                 prompt=f"optimise_{arm}_{task}", folder_files=files))
            for field in (104, 209):
                asset = f"dev_{task}_image.png" if field == 104 else f"test_{task}_image.png"
                rows.append(dict(row="direct", condition="three_turns", task=task, field=field, replicate=rep,
                                 prompt=f"direct_turn1_{task}", folder_files=f"image.png <- {asset}"))
    random.Random(SEED).shuffle(rows)
    for order, r in enumerate(rows, start=1):
        field = f"_f{r['field']}" if r["field"] else ""
        r["scenario_id"] = f"{r['row']}_{r['condition']}_{r['task']}{field}_r{r['replicate']}"
        r["run_order"] = order
    return rows


def main() -> None:
    (OUT / "prompts").mkdir(exist_ok=True)
    for prompt_id, text in build_prompts().items():
        (OUT / "prompts" / f"{prompt_id}.txt").write_text(text + "\n")
    with (OUT / "rows.csv").open("w", newline="") as handle:
        w = csv.writer(handle, lineterminator="\n")
        w.writerow(["row", "cli_tools", "tools", "framing"])
        for row, (cli_tools, tools, sentence) in ROWS.items():
            w.writerow([row, cli_tools, tools, FRAMING.format(tools=sentence)])
    scenarios = build_scenarios()
    fields = ["run_order", "scenario_id", "row", "condition", "task", "field", "replicate", "prompt", "folder_files"]
    with (OUT / "scenarios.csv").open("w", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows({k: r[k] for k in fields} for r in scenarios)
    print(len(build_prompts()), "prompts,", len(scenarios), "scenarios")


if __name__ == "__main__":
    main()
