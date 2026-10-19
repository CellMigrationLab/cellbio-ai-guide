"""Row D summary (one line per conversation): what the model did at each turn, including the turn-3 declines.

Writes fig3/v2/direct_summary.csv from runs/direct_*/ (direct_answers.json, turns.json, score.json).
Usage: PYTHONPATH=. python fig3/v2/summarise_direct.py
A conversation whose turn-3 reply has no ellipse JSON is recorded as `declined` (the reply is kept verbatim in turns.json);
nothing in the scored files is changed by this script.
"""
import csv
import json

from common.paths import REPO_ROOT

RUNS = REPO_ROOT / "fig3" / "v2" / "runs"
OUT = REPO_ROOT / "fig3" / "v2" / "direct_summary.csv"
COLUMNS = ["scenario_id", "task", "field", "replicate", "turn1_count", "turn2_median_area_um2",
           "turn2_median_aspect_ratio", "turn3", "n_ellipses_drawn", "turn3_reply_start"]


def summarise(run) -> dict:
    answers = json.loads((run / "direct_answers.json").read_text())
    score = json.loads((run / "score.json").read_text())
    last_reply = json.loads((run / "turns.json").read_text())[-1]["reply"]
    drew = score["turn3"]["status"] == "ok"
    return {"scenario_id": run.name, "task": run.name.split("_")[3], "field": answers["field"],
            "replicate": run.name.rsplit("_r", 1)[1], "turn1_count": score["turn1"].get("count"),
            "turn2_median_area_um2": answers["turn2_median_area_um2"],
            "turn2_median_aspect_ratio": answers["turn2_median_aspect_ratio"],
            "turn3": "drew" if drew else "declined", "n_ellipses_drawn": score["turn3"].get("n_drawn", ""),
            "turn3_reply_start": " ".join(last_reply.split())[:240] if not drew else ""}


def main() -> None:
    rows = [summarise(r) for r in sorted(RUNS.glob("direct_*")) if (r / "score.json").exists()]
    with OUT.open("w", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    declined = [r for r in rows if r["turn3"] == "declined"]
    print(len(rows), "conversations;", len(declined), "declined to draw:",
          sorted({r["task"] for r in declined}))


if __name__ == "__main__":
    main()
