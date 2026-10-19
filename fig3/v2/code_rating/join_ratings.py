"""Join an LLM rater's table (chatgpt_ratings_N.csv) to key.csv and summarise by prompt condition (exploratory).
Usage: PYTHONPATH=. python fig3/v2/code_rating/join_ratings.py chatgpt_ratings_1.csv   (writes <name>_joined.csv)"""
import csv
import statistics as st
import sys

from common.paths import REPO_ROOT

DIR = REPO_ROOT / "fig3" / "v2" / "code_rating"
ITEMS = ["readability", "visible_parameters", "debuggability", "error_handling", "testability", "overall_complexity"]


def main(name: str) -> None:
    key = {r["script"]: r for r in csv.DictReader((DIR / "key.csv").open())}
    rows = [{**key[r["script"]], **{i: int(r[i]) for i in ITEMS}} for r in csv.DictReader((DIR / name).open())]
    with (DIR / name.replace(".csv", "_joined.csv")).open("w", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for cond in ("simple", "box1"):
        sel = [r for r in rows if r["condition"] == cond]
        print(cond, len(sel), {i: round(st.mean(r[i] for r in sel), 2) for i in ITEMS})


if __name__ == "__main__":
    main(sys.argv[1])
