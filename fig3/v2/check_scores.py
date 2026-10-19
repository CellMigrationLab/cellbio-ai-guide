"""Recompute every score of the accepted main runs (fig3/v2/runs/*) and compare it with the stored score.json.

Rows B and C are scored from the label images stored by the runner, row D from direct_answers.json (nothing is run again);
row A has no score file. Prints OK or the first differences; exit code 1 on any difference.
Usage: PYTHONPATH=. python fig3/v2/check_scores.py
"""
import json
import sys

from common.paths import REPO_ROOT
from fig3.v2.score import score_run

RUNS = REPO_ROOT / "fig3" / "v2" / "runs"


def main() -> int:
    n, bad = 0, []
    for run in sorted(RUNS.glob("*")):
        stored = run / "score.json"
        if not stored.exists():
            continue
        n += 1
        if score_run(run) != json.loads(stored.read_text()):
            bad.append(run.name)
    if bad:
        print("DIFFERENT:", ", ".join(bad[:8]))
        return 1
    print(f"OK: {n} stored scores of the main runs reproduced")
    return 0


if __name__ == "__main__":
    sys.exit(main())
