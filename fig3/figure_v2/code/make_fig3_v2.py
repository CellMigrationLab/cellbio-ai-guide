"""Draft of Figure 3 (protocol v2) from the stored main runs (fig3/v2/runs/*/score.json).

Layout follows PROTOCOL_V2 section 8 (rows B, C, D; row A waits for the authors' item review). Writes the numbers
behind the plot to source_data/v2_scores.csv first, then draws from that file. Re-run after every scenario.
Run from fig3/figure_v2/source_data with PYTHONPATH set to the repository root (make fig3v2).
"""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RUNS = Path("../../v2/runs")
TASKS = [("nuclei", "Endothelial nuclei (DAPI)"), ("cancer", "Cancer cells (brightfield)"),
         ("endo", "Endothelial cells (brightfield)")]
FIELDS = ("f104", "f209")
FIELD_LABEL = {"f104": "dev. field 104", "f209": "test field 209"}
COND = {"code": [("simple", "simple"), ("box1", "Box 1")], "optimise": [("by_eye", "by eye"), ("labels", "with labels")]}
COL = {"simple": "#8a8f98", "box1": "#6f42c1", "by_eye": "#8a8f98", "labels": "#6f42c1", "three_turns": "#6f42c1"}


def read_scenarios():
    with open("../../v2/scenarios.csv", newline="") as f:
        return {r["scenario_id"]: r for r in csv.DictReader(f)}


def collect():
    """One row per (run, field) for B, C and D with the measures used in the panels."""
    sc = read_scenarios()
    rows = []
    for d in sorted(RUNS.iterdir()):
        sp = d / "score.json"
        if d.name not in sc or not sp.exists():
            continue
        s, score = sc[d.name], json.loads(sp.read_text())
        base = dict(scenario_id=d.name, row=s["row"], condition=s["condition"], task=s["task"], replicate=s["replicate"])
        if s["row"] in ("code", "optimise"):
            for fld in FIELDS:
                r = score[fld]
                ok = r["status"] == "ok"
                rows.append({**base, "field": fld[1:], "status": r["status"], "f1": r["f1"] if ok else "",
                             "count_error": r["count_error"] if ok else "",
                             "median_abs_area_error_pct": r["median_abs_area_error_pct"] if ok else "",
                             "median_abs_aspect_ratio_error": r["median_abs_aspect_ratio_error"] if ok else ""})
        elif s["row"] == "direct":
            t1, t3 = score["turn1"], score["turn3"]
            ok = t3["status"] == "ok"
            ref = score["reference"]["count"]
            rows.append({**base, "field": str(score["field"]), "status": t3["status"], "f1": t3["f1"] if ok else "",
                         "count_error": t1["count_error"], "stated_count_ratio": round(t1["count"] / ref, 3),
                         "drawn_count_ratio": round(t3["n_drawn"] / ref, 3) if ok else "",
                         "median_abs_area_error_pct": "", "median_abs_aspect_ratio_error": ""})
    return rows


def write_source(rows):
    cols = ["scenario_id", "row", "condition", "task", "replicate", "field", "status", "f1", "count_error",
            "stated_count_ratio", "drawn_count_ratio", "median_abs_area_error_pct", "median_abs_aspect_ratio_error"]
    with open("v2_scores.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, restval="")
        w.writeheader()
        w.writerows(rows)


def dots(ax, xs, ys, color, crashed=False):
    ax.scatter(xs, ys, s=26, color=color, zorder=3, marker="x" if crashed else "o", linewidths=1.4 if crashed else 0)


def f1_panel(ax, rows, row, task, title):
    conds = COND[row]
    ticks, labels, x = [], [], 0
    for cname, clabel in conds:
        for fld in FIELDS:
            sel = [r for r in rows if r["row"] == row and r["task"] == task and r["condition"] == cname and r["field"] == fld[1:]]
            ok = [float(r["f1"]) for r in sel if r["status"] == "ok"]
            bad = [r for r in sel if r["status"] != "ok"]
            jit = [x + 0.12 * (i - (len(ok) - 1) / 2) for i in range(len(ok))]
            dots(ax, jit, ok, COL[cname])
            if ok:
                ax.hlines(sorted(ok)[len(ok) // 2], x - 0.3, x + 0.3, color=COL[cname], lw=1.5, zorder=2)
            dots(ax, [x] * len(bad), [0.02] * len(bad), "#c0392b", crashed=True)
            ticks.append(x)
            labels.append(f"{clabel}\n{FIELD_LABEL[fld].split()[-1]}")
            x += 1
        x += 0.6
    ax.set_xticks(ticks, labels, fontsize=6.5)
    ax.set_ylim(-0.03, 1.02)
    ax.set_title(title, fontsize=8, loc="left")
    ax.spines[["top", "right"]].set_visible(False)


def direct_panel(ax, rows, task):
    for i, fld in enumerate(("104", "209")):
        sel = [r for r in rows if r["row"] == "direct" and r["task"] == task and r["field"] == fld]
        for j, (key, off, col) in enumerate((("stated_count_ratio", -0.15, "#8a8f98"), ("drawn_count_ratio", 0.15, "#6f42c1"))):
            ys = [float(r[key]) for r in sel if r[key] != ""]
            dots(ax, [i * 1.2 + off + 0.05 * k for k in range(len(ys))], ys, col)
        miss = [r for r in sel if r["drawn_count_ratio"] == ""]
        dots(ax, [i * 1.2 + 0.15] * len(miss), [0.02] * len(miss), "#c0392b", crashed=True)
    ax.axhline(1, color="#14223a", lw=0.8, ls="--", zorder=1)
    ax.set_xticks([0, 1.2], ["field 104", "field 209"], fontsize=6.5)
    ax.set_ylim(0, None)
    ax.set_title("D  direct answers: count / manual count", fontsize=8, loc="left")
    ax.spines[["top", "right"]].set_visible(False)


def main():
    rows = collect()
    write_source(rows)
    n_runs = len({r["scenario_id"] for r in rows})
    fig, axes = plt.subplots(4, 3, figsize=(10, 10), gridspec_kw={"height_ratios": [0.3, 1, 1, 1]})
    for c, (task, name) in enumerate(TASKS):
        axes[0, c].set_title(name, fontsize=10, fontweight="bold", loc="left", pad=10)
        axes[0, c].axis("off")
        axes[0, c].text(0, 0.5, "A  advice: item classes\n(pending the authors' review\nof the item tables)", fontsize=7, color="#555", va="center")
        f1_panel(axes[1, c], rows, "code", task, "B  code written by the model: F1 (× = crashed)")
        f1_panel(axes[2, c], rows, "optimise", task, "C  agent: F1 (× = crashed)")
        direct_panel(axes[3, c], rows, task)
        axes[1, c].set_ylabel("object F1" if c == 0 else "")
        axes[2, c].set_ylabel("object F1" if c == 0 else "")
        axes[3, c].set_ylabel("stated (grey), drawn (purple)" if c == 0 else "", fontsize=6.5)
    fig.suptitle(f"Figure 3, protocol v2: DRAFT with {n_runs} of 72 main runs (dots = runs, bars = median)", fontsize=9, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig("../output/fig3_v2_draft.png", dpi=150)
    fig.savefig("../output/fig3_v2_draft.svg")


if __name__ == "__main__":
    main()
