"""Panel c, step 4 ("final check on an unseen image"): a crop of field 209, a second field of the same experiment that
was not used for steps 2-3 (field 104). Writes the brightfield crop, the manual outlines and the custom StarDist
outlines, plus the whole-field and crop F1 scores.

The crop is chosen by a fixed rule, not by eye: among 240 x 260 px windows (the step-3 size) with at least 12 manually
annotated cells, the one whose local StarDist F1 is closest to the whole-field F1, so the crop shows a typical result.
Local F1 counts objects by centroid inside the window. Run from fig1/source_data."""
import json
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image
from skimage.measure import approximate_polygon, find_contours, regionprops

from common.matching import match
from common.paths import raw_file
from common.labels import read_labels

FIELD = 209
W, H = 240, 260          # same window size as step 3
STEP = 10                # window search step (px)
MIN_CELLS = 12           # manual cells required inside a candidate window
OUT = Path("panel_c_step4")


def f1(tp: int, fn: int, fp: int) -> float:
    return 2 * tp / (2 * tp + fn + fp)


def outlines(labels: np.ndarray) -> list:
    """Vector outlines of every object in a crop (x, y in crop pixels), as for steps 2-3."""
    out = []
    for lab in np.unique(labels[labels > 0]):
        for c in find_contours(np.pad(labels == lab, 1).astype(float), 0.5):
            c = approximate_polygon(c - 1, 0.6)
            out.append([[round(float(v[1]), 2), round(float(v[0]), 2)] for v in c])
    return out


def choose_window(ref: np.ndarray, pred: np.ndarray, target: float) -> dict:
    pairs, fn, fp = match(ref, pred, 0.5)
    c_ref = {r.label: r.centroid for r in regionprops(ref)}
    c_pred = {r.label: r.centroid for r in regionprops(pred)}
    best = None
    for y in range(0, ref.shape[0] - H + 1, STEP):
        for x in range(0, ref.shape[1] - W + 1, STEP):
            inside = lambda c: y <= c[0] < y + H and x <= c[1] < x + W
            n_ref = sum(inside(c) for c in c_ref.values())
            if n_ref < MIN_CELLS:
                continue
            n_fn = sum(inside(c_ref[g]) for g in fn)
            n_fp = sum(inside(c_pred[p]) for p in fp)
            local = f1(n_ref - n_fn, n_fn, n_fp)
            key = (abs(local - target), y, x)
            if best is None or key < best["key"]:
                best = {"key": key, "x": x, "y": y, "n_ref": int(n_ref), "missed": int(n_fn), "extra": int(n_fp),
                        "f1": round(float(local), 3)}
    if best is None:
        raise RuntimeError(f"No {W} x {H} window with at least {MIN_CELLS} manual cells")
    best.pop("key")
    return best


def main() -> None:
    bf = tifffile.imread(raw_file(f"field{FIELD}_brightfield.tif")).astype(float)
    ref = read_labels(raw_file(f"field{FIELD}_cancer_cells_manual_labels.tif"))
    pred = read_labels(raw_file(f"field{FIELD}_cancer_cells_stardist_custom_labels.tif"))
    if not (bf.shape == ref.shape == pred.shape):
        raise ValueError(f"Shape mismatch: {bf.shape}, {ref.shape}, {pred.shape}")
    pairs, fn, fp = match(ref, pred, 0.5)
    whole = round(f1(len(pairs), len(fn), len(fp)), 3)
    win = choose_window(ref, pred, whole)
    x, y = win["x"], win["y"]

    OUT.mkdir(exist_ok=True)
    crop = bf[y:y + H, x:x + W]
    lo, hi = np.percentile(crop, [0.3, 99.7])
    img = np.round(np.clip((crop - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)
    Image.fromarray(np.repeat(np.repeat(img, 2, 0), 2, 1)).save(OUT / "test_bf.png")
    for name, labels in (("ref", ref), ("stardist", pred)):
        json.dump({"w": W, "h": H, "contours": outlines(labels[y:y + H, x:x + W])}, open(OUT / f"test_{name}.json", "w"))
    n_ref = len(np.unique(ref[ref > 0]))
    scores = {"field": FIELD,
              "whole_field": {"n_ref": n_ref, "tp": len(pairs), "missed": len(fn), "extra": len(fp), "f1": whole},
              "window": {"w": W, "h": H, **win}}
    json.dump(scores, open(OUT / "step4_scores.json", "w"), indent=1)
    print(json.dumps(scores))


if __name__ == "__main__":
    main()
