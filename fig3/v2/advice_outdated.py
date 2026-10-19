"""Row A, first-pass item check by the operator (draft for the authors' review, PROTOCOL_V2 section 5): did the reply suggest
an outdated Cellpose model or code (removed in Cellpose 4: `cyto3`, `nuclei`, `models.Cellpose`, the "cellpose<4" pin)?

The classification below was made by reading each reply; the evidence is a verbatim excerpt (the script checks it is in the
reply). Writes fig3/v2/advice_outdated.csv. Usage: PYTHONPATH=. python fig3/v2/advice_outdated.py
"""
import csv
import json

from common.paths import REPO_ROOT

RUNS = REPO_ROOT / "fig3" / "v2" / "runs"
OUT = REPO_ROOT / "fig3" / "v2" / "advice_outdated.csv"
# scenario -> (outdated suggested 1/0, verbatim evidence from the reply)
ITEMS = {
    "advice_simple_cancer_r1": (0, "I'd use the Cellpose-SAM model as the starting point"),
    "advice_simple_cancer_r2": (1, "Try Cellpose first (cyto3 or Cellpose-SAM)"),
    "advice_simple_cancer_r3": (0, "Fine-tune Cellpose (Cellpose-SAM) on a small set"),
    "advice_simple_endo_r1": (0, "Use **Cellpose (the Cellpose-SAM / v4 generalist)"),
    "advice_simple_endo_r2": (1, "Fine-tune Cellpose (the CPSAM or cyto3 model)"),
    "advice_simple_endo_r3": (1, "start with Cellpose 3 (`cyto3`) and fine-tune it"),
    "advice_simple_nuclei_r1": (1, "**Cellpose** (`nuclei` or `cyto3` model)"),
    "advice_simple_nuclei_r2": (1, "use Cellpose 3.x (`pip install \"cellpose<4\"`), whose `nuclei` model is much lighter"),
    "advice_simple_nuclei_r3": (1, "(nuclei model, or the newer generalist model)"),
    "advice_box1_cancer_r1": (0, "I checked the current Cellpose docs"),
    "advice_box1_cancer_r2": (0, "I haven't confirmed whether cpsam needs a diameter at all"),
    "advice_box1_cancer_r3": (0, "**Cellpose-SAM (Cellpose 4, `cpsam`) first"),
    "advice_box1_endo_r1": (0, "the default pretrained weights, which are `cpsam_v2` in the current docs"),
    "advice_box1_endo_r2": (0, "Cellpose 4 (Cellpose-SAM, `cpsam`)"),
    "advice_box1_endo_r3": (0, None),
    "advice_box1_nuclei_r1": (0, "Cellpose 4 uses a single model, CPSAM"),
    "advice_box1_nuclei_r2": (0, "Cellpose 4 dropped the old `nuclei` model"),
    "advice_box1_nuclei_r3": (0, "The page I fetched doesn't mention the older `nuclei` model, so I can't confirm it still exists"),
}


def main() -> None:
    rows = []
    for sid, (outdated, evidence) in sorted(ITEMS.items()):
        reply = " ".join(t.get("reply") or "" for t in json.loads((RUNS / sid / "turns.json").read_text()))
        meta = json.loads((RUNS / sid / "meta.json").read_text())
        if evidence is not None and evidence not in reply:
            raise ValueError(f"{sid}: evidence not found verbatim: {evidence!r}")
        rows.append({"scenario_id": sid, "task": meta["task"], "condition": meta["condition"],
                     "outdated_suggested": outdated, "evidence": evidence or "", "web_used": int(bool(meta["web_used"]))})
    with OUT.open("w", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "replies ->", OUT.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
