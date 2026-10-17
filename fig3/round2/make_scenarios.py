"""Generate the round-2 prompts and scenario list from box1/box1_final.md (single source of the Box 1 text).

Writes fig3/round2/prompts/<prompt_id>.txt and fig3/round2/scenarios.csv (one row per conversation, in a randomised
run order fixed by SEED). Usage: python fig3/round2/make_scenarios.py
"""
import csv
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "fig3" / "round2"
SEED = 20261017
REPLICATES = 3
ASSISTANTS = ("claude", "openai")
TASKS = {
    "nuclei": dict(question="count the endothelial nuclei and measure their area",
                   images="widefield fluorescence images of a DAPI-stained endothelial monolayer (cancer cells sit on top)",
                   objects="endothelial nuclei", one="endothelial nucleus", channels="1 (DAPI)", size="13–17 µm",
                   output="a label image with one integer per endothelial nucleus (0 = background) and a table of nuclear areas in µm²"),
    "cancer": dict(question="count the cancer cells attached to an endothelial monolayer and measure their area",
                   images="brightfield images of cancer cells sitting on top of a confluent endothelial monolayer",
                   objects="cancer cells", one="cancer cell", channels="1 (brightfield)", size="15–25 µm",
                   output="a label image with one integer per cancer cell (0 = background; the endothelial cells underneath are not labelled) and a table of cancer-cell areas in µm²"),
    "endo": dict(question="count the endothelial cells and measure their area",
                 images="brightfield images of a confluent endothelial monolayer (some cancer cells sit on top)",
                 objects="endothelial cells", one="endothelial cell", channels="1 (brightfield)", size="25–50 µm",
                 output="a label image with one integer per endothelial cell (0 = background) and a table of endothelial-cell areas in µm²"),
}
HELP = {"advice": "Help me choose an analysis approach.",
        "code_python": "Help me write the analysis as a Python script.",
        "code_fiji": "Help me write the analysis as a Fiji macro.",
        "optimise": "Help me run and optimise the workflow."}
SOFTWARE = {"advice": "Python 3 and a current Fiji", "code_python": "Python 3.13", "code_fiji": "a current Fiji installation",
            "optimise": "Python 3.13 with numpy, scipy, scikit-image, tifffile and Cellpose 4.2"}
CODE_IO = "The attached image is {file}. Read it from the working directory and save the label image as labels.tif."


def box1_template() -> str:
    """Box 1 text from box1/box1_final.md, without the edit marks."""
    text = (ROOT / "box1" / "box1_final.md").read_text()
    return re.search(r"```text\n(.*?)```", text, re.S).group(1).replace("➕", "").strip()


def fill_box1(task: str, row: str) -> str:
    """Box 1 filled in for a task and row; raises if a placeholder is missing or left unfilled."""
    t, box = TASKS[task], box1_template()
    if "\n\nIf you are allowed to optimise" not in box:
        raise ValueError("Optimisation paragraph not found in box1_final.md")
    box, optimisation = box.split("\n\nIf you are allowed to optimise")
    replacements = {
        "[biological question or measurement]": t["question"], "[type of microscopy images]": t["images"],
        "[choose an analysis approach / write the analysis / run or optimise the workflow].": HELP[row].removeprefix("Help me "),
        "[2D/3D/time series]": "2D", "[e.g. T, Z, C, Y, X]": "Y, X", "[channels]": t["channels"],
        "[dtype]": "uint16 (12-bit values)", "[X µm]": "0.65 µm", "[X–Y µm]": t["size"],
        "[software and version]": SOFTWARE[row], "[hardware]": "a laptop CPU (no GPU)",
        "[measurement/output]": t["output"],
        "[representative images/annotations/reference measurements / expected outputs]":
            "a manually annotated example (a label image of part of the field)",
    }
    for key, value in replacements.items():
        if key not in box:
            raise KeyError(f"Placeholder {key!r} not found in box1_final.md")
        box = box.replace(key, value)
    if row == "optimise":
        opt = "If you are allowed to optimise" + optimisation
        opt = (opt.replace("[development data]", "image_left.tif and its annotation annotation_left.tif in this folder")
                  .replace("[held-out data]", "any other image (the rest of the field is held out and not in this folder)")
                  .replace("[working folder]", "this folder"))
        box += ("\n\n" + opt + "\nYou are allowed to optimise the workflow. When you are done, save the final script as "
                "pipeline.py so that it runs unchanged as `python pipeline.py <input.tif> <output_labels.tif>`, keep a "
                "log of each change and its score in log.txt, and report the final score.")
    if "[" in box:
        raise ValueError(f"Unfilled placeholder left in Box 1 for {task}/{row}: {re.findall(r'\[[^]]*\]', box)}")
    return box


def generic(task: str, row: str) -> str:
    """Generic request: the first sentence of Box 1 (row c: the 'run, assess, improve' request)."""
    t = TASKS[task]
    first = f"I want to {t['question']} from {t['images']}."
    if row == "optimise":
        return (f"{first} Please run the analysis on image.tif in this folder, assess the result, improve the analysis "
                "and give me the result: save the label image as labels.tif, the areas as areas.csv and the final script "
                "as pipeline.py.")
    return f"{first} {HELP[row]}"


def direct(task: str, condition: str) -> str:
    """Row d: count only (generic) or draw outlines and count, with a fixed JSON format (box1)."""
    if condition == "generic":
        return f"How many {TASKS[task]['objects']} are in this image?"
    return (f"Please draw around every {TASKS[task]['one']} in this image and count them. "
            "Give each outline as a polygon in the pixel coordinates of the image (origin top-left, x to the right, "
            "y down), as JSON: {\"count\": <integer>, \"cells\": [{\"points\": [[x, y], ...]}, ...]}.")


def build_prompts() -> dict:
    """All 30 prompts, keyed by prompt id <row>_<condition>_<task>."""
    prompts = {}
    for task in TASKS:
        for row in ("advice", "code_python", "code_fiji", "optimise"):
            for condition in ("generic", "box1"):
                text = generic(task, row) if condition == "generic" else fill_box1(task, row)
                if row.startswith("code"):
                    text += "\n" + CODE_IO.format(file="image.tif")
                prompts[f"{row}_{condition}_{task}"] = text
        for condition in ("generic", "box1"):
            prompts[f"direct_{condition}_{task}"] = direct(task, condition)
    return prompts


ATTACH = {"advice": "", "code_python": "image.tif <- {t}_image.tif (fallback image.png <- {t}_image.png)",
          "code_fiji": "image.tif <- {t}_image.tif (fallback image.png <- {t}_image.png)",
          "optimise": "", "direct": "{t}_image.png"}
FOLDER = {"generic": "image.tif <- {t}_image.tif", "box1": "image_left.tif <- {t}_image_left.tif; annotation_left.tif <- {t}_annotation_left.tif"}


def main() -> None:
    """Write the prompt files and scenarios.csv (randomised order, fixed SEED)."""
    prompts = build_prompts()
    (OUT / "prompts").mkdir(parents=True, exist_ok=True)
    for prompt_id, text in prompts.items():
        (OUT / "prompts" / f"{prompt_id}.txt").write_text(text + "\n")
    rows = []
    for prompt_id in prompts:
        row = "direct" if prompt_id.startswith("direct") else re.match(r"(advice|code_python|code_fiji|optimise)", prompt_id)[1]
        condition, task = prompt_id.split("_")[-2:]
        assistants = ("claude",) if row == "optimise" else ASSISTANTS  # agent row: Claude Code operator (ChatGPT optional)
        for assistant in assistants:
            for k in range(1, REPLICATES + 1):
                rows.append({"scenario_id": f"{assistant}_{prompt_id}_r{k}", "assistant": assistant, "row": row,
                             "condition": condition, "task": task, "replicate": k, "prompt_file": f"prompts/{prompt_id}.txt",
                             "attach": ATTACH[row].format(t=task),
                             "agent_folder": FOLDER[condition].format(t=task) if row == "optimise" else "",
                             "subject_tools": {"advice": "web", "code_python": "web; view attachment",
                                               "code_fiji": "web; view attachment", "direct": "view attachment",
                                               "optimise": "web; run code in its folder only"}[row]})
    random.Random(SEED).shuffle(rows)
    for order, r in enumerate(rows, 1):
        r["run_order"] = order
    with (OUT / "scenarios.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["run_order"] + [k for k in rows[0] if k != "run_order"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(prompts)} prompts, {len(rows)} scenarios")


if __name__ == "__main__":
    main()
