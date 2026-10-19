"""Scoring for Figure 3, protocol v2 (fig3/PROTOCOL_V2.md, sections 2 and 7).

Usage: PYTHONPATH=. python fig3/v2/score.py RUN_DIR      (writes RUN_DIR/score.json)

RUN_DIR/meta.json gives "row" and "task". Inputs per row:
  code, optimise : scored on the HELD-OUT RIGHT HALF (x >= 512) of each field F in (104, 209); the pipeline is run on the
                   whole field, and the left halves are what the model was given (mosaic). "mean" = mean F1 of the two.
                   For each field F: execution_fF.json (from runner.py) and, if the run succeeded,
                   labels_fF.tif.gz and measurements_fF.csv
  direct         : direct_answers.json, written by the operator from the conversation:
                   {"field": F, "turn1_text": "...", "turn2_text": "...", "turn2_median_area_um2": x | null,
                    "turn2_median_aspect_ratio": y | null, "turn3_json": {...} | null}
  advice         : not scored here (item check, PROTOCOL_V2 section 5)

Measures (frozen definitions): count = objects in the label image; area = pixels x 0.649614^2 µm²; aspect ratio =
major / minor axis of the moment ellipse (objects with minor axis < 2 px excluded); objects touching the border are
excluded from area and aspect-ratio statistics. The same functions measure the manual references.
"""
from __future__ import annotations

import csv
import gzip
import io
import json
import re
import sys
from pathlib import Path

import numpy as np
import tifffile
from skimage.measure import regionprops
from skimage.segmentation import clear_border

from common.labels import InvalidLabels, validate_labels
from common.matching import match
from common.metadata import FOLLAIN_FIELD_SHAPE, FOLLAIN_PX_UM
from fig3.scoring.tasks import HALF_X, TASKS, heldout_reference, reference, score_heldout

FIELDS = (104, 209)
MIN_MINOR_PX = 2.0
AREA_TOL = 0.02        # measurements.csv area must agree with the label image within 2 %
AR_TOL = 0.05          # and aspect ratio within 0.05


# ---------------------------------------------------------------- measures
def object_measures(labels: np.ndarray) -> dict[int, dict]:
    """Per object: area (µm²), aspect ratio (None if the minor axis < 2 px) and whether it touches the border."""
    out = {}
    h, w = labels.shape
    for r in regionprops(labels):
        y0, x0, y1, x1 = r.bbox
        minor = r.axis_minor_length
        out[int(r.label)] = {"area_um2": float(r.area * FOLLAIN_PX_UM ** 2),
                             "aspect_ratio": float(r.axis_major_length / minor) if minor >= MIN_MINOR_PX else None,
                             "border": bool(y0 == 0 or x0 == 0 or y1 == h or x1 == w)}
    return out


def summary_measures(labels: np.ndarray) -> dict:
    m = object_measures(labels)
    inner = [v for v in m.values() if not v["border"]]
    ars = [v["aspect_ratio"] for v in inner if v["aspect_ratio"] is not None]
    return {"count": len(m),
            "median_area_um2": round(float(np.median([v["area_um2"] for v in inner])), 1) if inner else None,
            "median_aspect_ratio": round(float(np.median(ars)), 3) if ars else None}


def reference_summary(task: str, field: int) -> dict:
    return summary_measures(reference(task, field))


def matched_shape_errors(task: str, pred: np.ndarray, field: int) -> dict:
    """Median absolute relative area error and absolute aspect-ratio error over matched, non-border objects of the
    held-out right half of the field (pred: whole-field label image)."""
    gt = heldout_reference(task, field)
    pred = pred[:, HALF_X:]
    p = clear_border(pred) if task == "endo" else pred
    pairs, _, _ = match(gt, p, 0.5)
    mg, mp = object_measures(gt), object_measures(p)
    area_err, ar_err = [], []
    for g, q, _ in pairs:
        if mg[g]["border"] or mp[q]["border"]:
            continue
        area_err.append(abs(mp[q]["area_um2"] / mg[g]["area_um2"] - 1))
        if mg[g]["aspect_ratio"] is not None and mp[q]["aspect_ratio"] is not None:
            ar_err.append(abs(mp[q]["aspect_ratio"] - mg[g]["aspect_ratio"]))
    return {"n_matched_inner": len(area_err),
            "median_abs_area_error_pct": round(100 * float(np.median(area_err)), 1) if area_err else None,
            "median_abs_aspect_ratio_error": round(float(np.median(ar_err)), 3) if ar_err else None}


def check_measurements_csv(path: Path, labels: np.ndarray) -> dict:
    """Does the table have one row per label, with area and aspect ratio agreeing with the label image?"""
    if not path.is_file():
        return {"status": "missing"}
    try:
        with path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
    except (csv.Error, UnicodeDecodeError) as exc:
        return {"status": "unreadable", "error": str(exc)[:200]}
    if not rows:
        return {"status": "empty"}
    cols = {c.lower(): c for c in rows[0]}
    find = lambda *keys: next((cols[c] for c in cols if any(k in c for k in keys)), None)   # noqa: E731
    c_label, c_area, c_ar = find("label", "id"), find("area"), find("aspect", "ratio")
    if not (c_label and c_area and c_ar):
        return {"status": "columns_not_found", "columns": list(rows[0])}
    truth = object_measures(labels)
    try:
        table = {int(float(r[c_label])): (float(r[c_area]), float(r[c_ar])) for r in rows}
    except ValueError as exc:
        return {"status": "non_numeric", "error": str(exc)[:200]}
    missing, extra = sorted(set(truth) - set(table)), sorted(set(table) - set(truth))
    bad_area = [k for k in set(truth) & set(table) if abs(table[k][0] / truth[k]["area_um2"] - 1) > AREA_TOL]
    bad_ar = [k for k in set(truth) & set(table)
              if truth[k]["aspect_ratio"] is not None and abs(table[k][1] - truth[k]["aspect_ratio"]) > AR_TOL]
    ok = not (missing or extra or bad_area or bad_ar)
    return {"status": "consistent" if ok else "inconsistent", "n_rows": len(table), "labels_missing": len(missing),
            "rows_without_label": len(extra), "area_disagrees": len(bad_area), "aspect_ratio_disagrees": len(bad_ar),
            "area_column": c_area, "aspect_ratio_column": c_ar}


# ---------------------------------------------------------------- rows B and C
def score_field(run_dir: Path, task: str, field: int) -> dict:
    exec_path = run_dir / f"execution_f{field}.json"
    if not exec_path.is_file():
        raise FileNotFoundError(f"{exec_path} missing: run fig3/v2/runner.py first")
    execution = json.loads(exec_path.read_text())
    if execution["status"] != "ok":
        return {"status": execution["status"], "f1": 0.0}           # crashed / timeout / no_output: F1 0, drawn as x
    try:
        pred = run_labels(run_dir, field)
    except InvalidLabels as exc:
        return {"status": "invalid_labels", "error": str(exc), "f1": 0.0}
    out = {"status": "ok", **score_heldout(task, pred, field=field)}   # right half of the field only
    pred_sum, ref_sum = summary_measures(pred[:, HALF_X:]), summary_measures(heldout_reference(task, field))
    out["measures"] = pred_sum
    out["reference"] = ref_sum
    out["count_error"] = pred_sum["count"] - ref_sum["count"]
    for key in ("median_area_um2", "median_aspect_ratio"):
        out[f"{key}_error"] = (round(pred_sum[key] - ref_sum[key], 3)
                               if pred_sum[key] is not None and ref_sum[key] is not None else None)
    out.update(matched_shape_errors(task, pred, field))
    out["measurements_csv"] = check_measurements_csv(run_dir / f"measurements_f{field}.csv", pred)
    return out


def run_labels(run_dir: Path, field: int) -> np.ndarray:
    """The label image a script wrote (runner.py stores it gzip-compressed), validated strictly."""
    path = run_dir / f"labels_f{field}.tif.gz"
    if not path.is_file():
        raise FileNotFoundError(f"label image not found: {path}")
    with gzip.open(path, "rb") as handle:
        try:
            image = tifffile.imread(io.BytesIO(handle.read()))
        except Exception as exc:                 # not a readable TIFF: the script's output is invalid
            raise InvalidLabels(f"{path.name}: unreadable TIFF ({exc})") from exc
    return validate_labels(image, name=path.name, expected_shape=FOLLAIN_FIELD_SHAPE, squeeze=True)


# ---------------------------------------------------------------- row D
def parse_count(text: str) -> dict:
    """The first number in the reply (list markers such as '1.' at the start of a line are skipped). If that number
    starts a range ('a-b', 'a to b', 'between a and b'), the midpoint is the count and the range is kept."""
    t = re.sub(r"(?m)^\s*\d+[.)]\s", " ", text.replace(",", "").replace("*", ""))
    patterns = (r"between\s+(\d+)\s+and\s+(\d+)", r"(\d+)\s*(?:-|–|to)\s*(\d+)", r"(\d+)")
    hits = [m for m in (re.search(p, t) for p in patterns) if m]
    if not hits:
        return {"count": None, "range": None}
    first = min(hits, key=lambda m: (m.start(), -len(m.groups())))
    if len(first.groups()) == 2:
        lo, hi = int(first.group(1)), int(first.group(2))
        return {"count": (lo + hi) / 2, "range": [lo, hi]}
    return {"count": int(first.group(1)), "range": None}


def match_centres(task: str, field: int, centres: list[tuple[float, float]]) -> dict:
    """One-to-one matching of ellipse centres to reference objects: a centre matches the object it falls in; if several
    centres fall in one object, the one closest to its centroid is the match and the others are false positives."""
    gt = reference(task, field)
    h, w = gt.shape
    cents = {r.label: r.centroid for r in regionprops(gt)}
    best: dict[int, float] = {}
    fp = 0
    for x, y in centres:
        xi, yi = int(round(x)), int(round(y))
        lab = int(gt[yi, xi]) if 0 <= yi < h and 0 <= xi < w else 0
        if lab == 0:
            fp += 1
            continue
        d = float(np.hypot(y - cents[lab][0], x - cents[lab][1]))
        if lab in best:
            fp += 1
            best[lab] = min(best[lab], d)
        else:
            best[lab] = d
    tp, fn = len(best), len(cents) - len(best)
    f1 = 2 * tp / (2 * tp + fp + fn) if (tp + fp + fn) else 0.0
    return {"n_ref": len(cents), "n_drawn": len(centres), "tp": tp, "fp": fp, "fn": fn, "f1": round(f1, 3)}


COUNT_CORRECTIONS = json.loads((Path(__file__).parent / "count_corrections.json").read_text())


def corrected_count(run_name: str, parsed: dict) -> dict:
    """Operator's reading of the reply for the few runs where the first-number rule read the wrong number
    (count_corrections.json). The rule's own result must still be the one recorded there, so a change of the rule is noticed."""
    fix = COUNT_CORRECTIONS.get(run_name)
    if fix is None:
        return parsed
    if parsed["count"] != fix["rule_gave"]:
        raise ValueError(f"{run_name}: parse_count gave {parsed['count']}, count_corrections.json expects {fix['rule_gave']}")
    return {"count": fix["count"], "range": fix["range"], "corrected_from": fix["rule_gave"]}


def score_direct(run_dir: Path, task: str) -> dict:
    ans = json.loads((run_dir / "direct_answers.json").read_text())
    field = int(ans["field"])
    ref = reference_summary(task, field)
    out = {"field": field, "reference": ref, "turn1": corrected_count(run_dir.name, parse_count(ans["turn1_text"]))}
    if out["turn1"]["count"] is not None:
        out["turn1"]["count_error"] = out["turn1"]["count"] - ref["count"]
        if out["turn1"]["range"]:
            out["turn1"]["reference_in_range"] = out["turn1"]["range"][0] <= ref["count"] <= out["turn1"]["range"][1]
    out["turn2"] = {k: ans.get(k) for k in ("turn2_median_area_um2", "turn2_median_aspect_ratio")}
    j = ans.get("turn3_json")
    if not isinstance(j, dict) or not isinstance(j.get("ellipses"), list):
        out["turn3"] = {"status": "no_valid_json", "f1": 0.0}
        return out
    centres, areas, ars, invalid = [], [], [], 0
    for e in j["ellipses"]:
        try:
            x, y, a, b = (float(e[k]) for k in ("x", "y", "major", "minor"))
        except (KeyError, TypeError, ValueError):
            invalid += 1
            continue
        if not (a > 0 and b > 0):
            invalid += 1
            continue
        centres.append((x, y))
        areas.append(np.pi * a * b / 4 * FOLLAIN_PX_UM ** 2)
        ars.append(max(a, b) / min(a, b))
    out["turn3"] = {"status": "ok", "stated_count": j.get("count"), "n_ellipses": len(centres), "n_invalid": invalid,
                    "stated_median_area_um2": j.get("median_area_um2"), "stated_median_aspect_ratio": j.get("median_aspect_ratio"),
                    "drawn_median_area_um2": round(float(np.median(areas)), 1) if areas else None,
                    "drawn_median_aspect_ratio": round(float(np.median(ars)), 3) if ars else None,
                    **match_centres(task, field, centres)}
    return out


def score_run(run_dir: Path) -> dict:
    meta = json.loads((run_dir / "meta.json").read_text())
    row, task = meta["row"], meta["task"]
    if task not in TASKS:
        raise ValueError(f"unknown task {task!r}")
    if row in ("code", "optimise"):
        out = {f"f{f}": score_field(run_dir, task, f) for f in FIELDS}
        out["mean"] = {"f1": round(sum(out[f"f{f}"]["f1"] for f in FIELDS) / len(FIELDS), 3),
                       "note": "mean of the object F1 on the held-out halves of fields 104 and 209 (failed = 0)"}
        return out
    if row == "direct":
        return score_direct(run_dir, task)
    if row == "advice":
        return {"status": "not_scored_here", "note": "item check, PROTOCOL_V2 section 5"}
    raise ValueError(f"unknown row {row!r}")


def main(argv: list[str]) -> None:
    if len(argv) != 2:
        raise SystemExit(__doc__)
    run_dir = Path(argv[1])
    result = score_run(run_dir)
    (run_dir / "score.json").write_text(json.dumps(result, indent=1, allow_nan=False))
    print(run_dir.name, json.dumps(result)[:600])


if __name__ == "__main__":
    main(sys.argv)
