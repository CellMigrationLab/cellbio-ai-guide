# code_box1_nuclei_r3

## user

You are an AI assistant chatting with a user. You can search the web (WebSearch and WebFetch; load them with ToolSearch if they are not listed). The user attached a file, which you can view: /home/user/sessions_v2_preflight/v011/image.png. You cannot run code; the user will run your script. Reply to the user as you normally would.

I want to segment and count the endothelial nuclei and measure their shape (area and aspect ratio) from widefield fluorescence images of a DAPI-stained endothelial monolayer (cancer cells sit on top). Help me write the analysis as a Python script.
My images are 2D, with axes Y, X, channels 1 (DAPI), data type uint16 (12-bit values), pixel/voxel size 0.65 µm, and objects of interest approximately 13–17 µm in size. I use Python 3.13 on a laptop CPU (no GPU). The output I need is a label image with one integer per endothelial nucleus (0 = background) and a table with the area (µm²) and aspect ratio of each endothelial nucleus. I can provide a manual annotation of this image (a label image).
Please:

* Clarify the task. Ask for missing information only when it could materially affect the analysis. If useful, ask me for representative images or examples of the expected result.
* Use appropriate methods. Prefer established, maintained software and documented APIs. Check current documentation rather than relying only on memory. If consequential behaviour remains unclear, inspect the source code when available rather than guessing.
* Check deep learning model suitability. If using a pre-trained model, consider whether my images match its training data, including image type, channels, dimensionality, object scale, preprocessing and post-processing.
* Write code according to best practices. Keep functions small and focused, use clear names and annotations, and separate consequential processing steps. Validate inputs, provide informative errors and do not use silent fallbacks.
* Make processing explicit. State important parameters, defaults and transformations, including resizing, resampling, normalisation, channel selection and post-processing. Preserve the original coordinate system and physical units unless a transformation is explicitly required and documented.
* Make the analysis testable. Test it on representative reference data where possible, save useful intermediate outputs and overlays, and use validation measures appropriate to the intended biological measurement rather than relying on a single generic score. Include a test I can run on my annotated example and tell me what result would mean that the analysis failed. If I ask for counts or measurements, return the masks or outlines they come from.
* Audit and challenge the result. Before finishing, assume that the analysis could be scientifically wrong even if the code runs and the output looks plausible. Identify the failure modes most likely to change the biological conclusion and suggest concrete tests or reference data that would expose them.
The image is image.tif; the script should read it from the working directory and save the label image as labels.tif and a table with one row per object (label, area in µm², aspect ratio) as measurements.csv.

## assistant

I'll start by looking at your image.

## assistant (tool call: Read)

```json
{
 "file_path": "/home/user/sessions_v2_preflight/v011/image.png"
}
```

## tool result

```
[{"type": "image", "note": "image shown to the subject"}]
```

## assistant (tool call: WebSearch)

```json
{
 "query": "scikit-image 0.26 remove_small_objects min_size deprecated max_size release notes",
 "mode": "standard"
}
```

## tool result

```
Web search results for query: "scikit-image 0.26 remove_small_objects min_size deprecated max_size release notes"

Links: [{"title":"release 0.26.0.rst","url":"https://scikit-image.org/docs/stable/_sources/release_notes/release_0.26.0.rst.txt"},{"title":"\"\"\"Miscellaneous morphology functions.\"\"\"","url":"https://generationalwealth.duckdns.org/venv/lib/python3.13/site-packages/skimage/morphology/misc.py"},{"title":"misc.cpython 313","url":"https://generationalwealth.duckdns.org/venv/lib/python3.13/site-packages/skimage/morphology/__pycache__/misc.cpython-313.pyc"},{"title":"scikit-image 0.26.0 (2025-12-20)#","url":"https://scikit-image.org/docs/stable/release_notes/release_0.26.html"},{"title":"scikit-image 0.26.0 (2025-12-20)#","url":"https://scikit-image.org/docs/0.26.x/release_notes/release_0.26.html"},{"title":"Removing objects#","url":"https://scikit-image.org/docs/0.26.x/auto_examples/features_detection/plot_remove_objects.html"},{"title":"scikit-image 0.15.0 (2019-04-03)#","url":"https://scikit-image.org/docs/0.23.x/release_notes/release_0.15.html"},{"title":"scikit-image 0.15.0 (2019-04-03)#","url":"https://scikit-image.org/docs/0.24.x/release_notes/release_0.15.html"},{"title":"disroot.org","url":"https://git.disroot.org/kpriv/pkgsrc/src/commit/57913482b85a03eb7fc061ab77a7e9b1578b8ded/math/py-scikit-image/Makefile"}]

In scikit-image 0.26.0, `min_size` in `remove_small_objects` is deprecated in favor of a new `max_size` parameter. The release notes say the new threshold removes objects smaller than or equal to its value, while the previous parameter only removed smaller ones (#7739). That makes the boundary case the main behavior change: an object exactly `min_size` pixels in size is kept under the old parameter but removed under `max_size`.

The 0.26.0 notes are dated 2025-12-20. The same change is noted for `remove_small_holes`, where `area_threshold` is deprecated in favor of `max_size` (to make API and behavior clearer).

The installed function's docstring, from a third-party mirror, says the new parameter was added in 0.26 and that the deprecation has a stop version of 2.0.0, so `min_size` is expected to be removed in 2.0.0. I didn't find that stop version in the official release notes, so check it against the official docs before relying on it. The default for `max_size` is 64, and the official example uses `max_size=99` to separate objects of 100 pixels or more from smaller ones.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
```

## assistant

I couldn't run code here, so this script is **untested**. It's a first draft to validate with the evaluation script below, not a finished result.

## What I see in your image

- **Endothelial nuclei:** dim, elliptical, about 20–28 px long (13–17 µm), mostly separate, with some touching pairs.
- **Cancer-cell nuclei:** much brighter, smaller, round and often blurred or out of focus. They sit in clusters and overlap the monolayer.

The main risk is that the cancer nuclei get counted as endothelial. A generic nucleus segmenter would segment both, so the exclusion step has to be explicit.

## Method choice

I used a classical pipeline: Gaussian smoothing, a local threshold plus a noise floor, h-maxima watershed to split touching nuclei, then a per-object filter. I chose it over a pre-trained model for these reasons:

- **Pre-trained models:** Cellpose and StarDist aren't trained to separate "endothelial vs cancer" nuclei. Either would need the same brightness and shape filter afterwards.
- **Your setup:** you have no GPU, and the nuclei are simple, well-separated ellipses, so a classical pipeline is a reasonable fit.
- **Upgrade path:** if the evaluation shows many merged or missed nuclei in crowded areas, Cellpose is the next step. Keep the same filter and evaluation.
- **scikit-image API:** `remove_small_objects` changed its size argument in 0.26 (`min_size` is deprecated in favour of `max_size`, and the boundary behaviour differs). I filter by area from `regionprops` instead, so the script doesn't depend on it ([release notes](https://scikit-image.org/docs/stable/release_notes/release_0.26.html)).

## Assumptions that affect the result

| Assumption | Default | Why it matters |
|---|---|---|
| Cancer nuclei are brighter | Reject objects with mean intensity above 2.5× the median object | Bright endothelial nuclei could be lost, and dim cancer nuclei could be kept. |
| Merged clumps have low solidity | Reject solidity below 0.88 | Rejected clumps are not counted, which undercounts crowded areas. |
| Nucleus area | Keep 40–250 µm² | Taken from your 13–17 µm size estimate. |
| Edge-touching nuclei | Excluded from labels and table | Their truncated shape would bias area and aspect ratio. The count is lower for the same reason. |
| No intensity normalisation | Thresholds are relative to the local background | Nothing is rescaled. Pixel values stay in raw 12-bit units. |

Coordinates stay in the original pixel grid with no resampling. Area is `pixels × 0.65²`. Aspect ratio is the major axis divided by the minor axis of the moment-based ellipse (`regionprops`).

## `analyze_nuclei.py`

```python
"""Segment endothelial nuclei in a 2D DAPI image; measure area (µm²) and aspect ratio.

Reads image.tif (Y, X; uint16, 12-bit) from the working directory and writes
labels.tif, measurements.csv and debug outputs (debug/).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import filters, io, measure, morphology, segmentation

MAX_12BIT = 4095


@dataclass(frozen=True)
class Params:
    pixel_size_um: float = 0.65
    smooth_sigma_um: float = 0.65        # ~1 px Gaussian to suppress shot noise
    local_block_um: float = 35.0         # local-threshold window, > nucleus length (~16 µm)
    floor_mad_factor: float = 5.0        # global floor = median + 5 * robust sigma
    open_radius_px: int = 2              # removes thin bridges / specks
    split_h_px: float = 1.0              # h-maxima height on the distance map
    min_area_um2: float = 40.0
    max_area_um2: float = 250.0
    min_solidity: float = 0.88
    bright_factor: float = 2.5           # cancer-nucleus cut-off, x median object intensity
    keep_border: bool = False


def load_image(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found in {Path.cwd()}")
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {img.dtype}")
    if img.max() > MAX_12BIT:
        raise ValueError(f"Max value {img.max()} exceeds 12-bit range ({MAX_12BIT})")
    n_saturated = int((img == MAX_12BIT).sum())
    if n_saturated:
        print(f"WARNING: {n_saturated} saturated pixels (value {MAX_12BIT}); "
              "intensity-based cancer-cell rejection is less reliable there.")
    return img


def smooth(img: np.ndarray, sigma_px: float) -> np.ndarray:
    return filters.gaussian(img.astype(np.float32), sigma=sigma_px, preserve_range=True)


def background_floor(smoothed: np.ndarray, mad_factor: float) -> float:
    median = np.median(smoothed)
    robust_sigma = 1.4826 * np.median(np.abs(smoothed - median))
    return float(median + mad_factor * robust_sigma)


def foreground_mask(smoothed: np.ndarray, p: Params) -> np.ndarray:
    block = int(round(p.local_block_um / p.pixel_size_um)) | 1  # must be odd
    local = filters.threshold_local(smoothed, block_size=block, method="gaussian")
    mask = (smoothed > local) & (smoothed > background_floor(smoothed, p.floor_mad_factor))
    mask = ndi.binary_fill_holes(mask)
    footprint = morphology.disk(p.open_radius_px)
    return ndi.binary_opening(mask, structure=footprint)


def split_touching(mask: np.ndarray, h_px: float) -> np.ndarray:
    """Watershed on the distance map; h-maxima markers avoid over-splitting ellipses."""
    distance = filters.gaussian(ndi.distance_transform_edt(mask), sigma=1.0)
    markers = measure.label(morphology.h_maxima(distance, h_px))
    return segmentation.watershed(-distance, markers, mask=mask)


def describe_objects(labels: np.ndarray, raw: np.ndarray, p: Params) -> pd.DataFrame:
    table = pd.DataFrame(measure.regionprops_table(
        labels, intensity_image=raw,
        properties=("label", "area", "solidity", "intensity_mean", "bbox")))
    px_area = p.pixel_size_um ** 2
    table["area_um2"] = table["area"] * px_area
    h, w = labels.shape
    table["touches_border"] = ((table["bbox-0"] == 0) | (table["bbox-1"] == 0)
                               | (table["bbox-2"] == h) | (table["bbox-3"] == w))
    return table


def reject_reasons(table: pd.DataFrame, p: Params) -> pd.Series:
    size_ok = table["area_um2"].between(p.min_area_um2, p.max_area_um2)
    reference = table.loc[size_ok, "intensity_mean"].median()
    reason = pd.Series("", index=table.index)
    # Later rules overwrite earlier ones, so the first rule listed has the highest priority.
    reason[table["solidity"] < p.min_solidity] = "low_solidity"
    reason[table["intensity_mean"] > p.bright_factor * reference] = "bright_cancer_like"
    if not p.keep_border:
        reason[table["touches_border"]] = "touches_border"
    reason[~size_ok] = "size"
    print(f"Reference (median) object intensity: {reference:.1f}; "
          f"cancer cut-off: {p.bright_factor * reference:.1f}")
    return reason


def measure_final(labels: np.ndarray, p: Params) -> pd.DataFrame:
    props = measure.regionprops_table(
        labels, properties=("label", "area", "major_axis_length", "minor_axis_length"))
    table = pd.DataFrame(props)
    return pd.DataFrame({
        "label": table["label"],
        "area_um2": table["area"] * p.pixel_size_um ** 2,
        "aspect_ratio": table["major_axis_length"] / table["minor_axis_length"],
    })


def save_overlay(raw: np.ndarray, accepted: np.ndarray, rejected: np.ndarray, path: Path) -> None:
    base = np.clip(raw / np.percentile(raw, 99.5), 0, 1) ** 0.5
    rgb = np.dstack([base] * 3)
    rgb[segmentation.find_boundaries(rejected > 0)] = (1, 0, 0)   # red: rejected
    rgb[segmentation.find_boundaries(accepted > 0)] = (0, 1, 0)   # green: endothelial
    io.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def main() -> None:
    p = Params()
    raw = load_image(Path("image.tif"))
    debug = Path("debug")
    debug.mkdir(exist_ok=True)

    smoothed = smooth(raw, p.smooth_sigma_um / p.pixel_size_um)
    mask = foreground_mask(smoothed, p)
    candidates = split_touching(mask, p.split_h_px)
    table = describe_objects(candidates, raw, p)
    table["reject_reason"] = reject_reasons(table, p)

    accepted_ids = table.loc[table["reject_reason"] == "", "label"].to_numpy()
    accepted = np.where(np.isin(candidates, accepted_ids), candidates, 0)
    rejected = np.where((candidates > 0) & (accepted == 0), candidates, 0)
    final, _, _ = segmentation.relabel_sequential(accepted)
    if final.max() > np.iinfo(np.uint16).max:
        raise ValueError("More than 65535 objects; cannot store as uint16")

    tifffile.imwrite("labels.tif", final.astype(np.uint16))
    measure_final(final, p).to_csv("measurements.csv", index=False)
    table.to_csv(debug / "all_candidates.csv", index=False)
    tifffile.imwrite(debug / "foreground_mask.tif", (mask * 255).astype(np.uint8))
    save_overlay(raw, accepted, rejected, debug / "overlay.png")

    print(f"Candidates: {len(table)}; accepted endothelial nuclei: {final.max()}")
    print(table["reject_reason"].replace("", "accepted").value_counts().to_string())


if __name__ == "__main__":
    main()
```

## `evaluate.py`: the test on your annotation

Run it as `python evaluate.py annotation.tif`.

```python
"""Compare labels.tif with a manual annotation, using measures tied to count, area and shape."""
import sys

import numpy as np
import pandas as pd
import tifffile
from skimage import measure

PIXEL_SIZE_UM = 0.65
IOU_MATCH = 0.5


def shape_table(labels: np.ndarray) -> pd.DataFrame:
    t = pd.DataFrame(measure.regionprops_table(
        labels, properties=("label", "area", "major_axis_length", "minor_axis_length")))
    t["area_um2"] = t["area"] * PIXEL_SIZE_UM ** 2
    t["aspect_ratio"] = t["major_axis_length"] / t["minor_axis_length"].clip(lower=1e-6)
    return t.set_index("label")


def matched_pairs(gt: np.ndarray, pred: np.ndarray) -> list[tuple[int, int]]:
    pairs, inter = np.unique(np.stack([gt.ravel(), pred.ravel()]), axis=1, return_counts=True)
    area_gt, area_pred = np.bincount(gt.ravel()), np.bincount(pred.ravel())
    out = []
    for (g, q), n in zip(pairs.T, inter):
        if g and q and n / (area_gt[g] + area_pred[q] - n) > IOU_MATCH:  # IoU > 0.5 is unique
            out.append((int(g), int(q)))
    return out


def main(annotation_path: str) -> None:
    gt, pred = tifffile.imread(annotation_path), tifffile.imread("labels.tif")
    if gt.shape != pred.shape:
        raise ValueError(f"Shape mismatch: annotation {gt.shape} vs labels {pred.shape}")
    gt, pred = gt.astype(np.int64), pred.astype(np.int64)
    gt_t, pred_t = shape_table(gt), shape_table(pred)
    pairs = matched_pairs(gt, pred)
    tp = len(pairs)
    precision, recall = tp / len(pred_t), tp / len(gt_t)
    f1 = 2 * precision * recall / (precision + recall) if tp else 0.0
    count_err = (len(pred_t) - len(gt_t)) / len(gt_t)

    g_ids, p_ids = zip(*pairs)
    a_rel = (pred_t.loc[list(p_ids), "area_um2"].to_numpy()
             / gt_t.loc[list(g_ids), "area_um2"].to_numpy() - 1)
    ar_diff = (pred_t.loc[list(p_ids), "aspect_ratio"].to_numpy()
               - gt_t.loc[list(g_ids), "aspect_ratio"].to_numpy())

    print(f"GT {len(gt_t)}  predicted {len(pred_t)}  matched(IoU>{IOU_MATCH}) {tp}")
    print(f"precision {precision:.3f}  recall {recall:.3f}  F1 {f1:.3f}  count error {count_err:+.1%}")
    print(f"area: median per-nucleus error {np.median(a_rel):+.1%}; "
          f"population median GT {gt_t.area_um2.median():.1f} vs pred {pred_t.area_um2.median():.1f} µm²")
    print(f"aspect ratio: median per-nucleus error {np.median(ar_diff):+.3f} "
          f"(MAE {np.mean(np.abs(ar_diff)):.3f}); "
          f"population mean GT {gt_t.aspect_ratio.mean():.2f} vs pred {pred_t.aspect_ratio.mean():.2f}")

    checks = {
        "F1 >= 0.80": f1 >= 0.80,
        "|count error| <= 10%": abs(count_err) <= 0.10,
        "precision >= 0.90 (cancer nuclei not leaking in)": precision >= 0.90,
        "|median area error| <= 15%": abs(np.median(a_rel)) <= 0.15,
        "aspect-ratio MAE <= 0.15": np.mean(np.abs(ar_diff)) <= 0.15,
    }
    for name, ok in checks.items():
        print(("PASS  " if ok else "FAIL  ") + name)


if __name__ == "__main__":
    main(sys.argv[1])
```

**What counts as failure:** any FAIL line is a failure. The cut-offs are my proposals, not standards, so tighten them if your biological effect is small. Two cases are especially informative:

- **Low precision with a normal F1:** cancer nuclei are being counted as endothelial. Look for red-vs-green errors in `debug/overlay.png`.
- **Good F1 but a biased area:** the threshold is too tight or too loose. The matching criterion (IoU above 0.5) hides this, so check the area line separately.

## Audit: how this could be wrong while looking fine

1. **Brightness as the cancer/endothelial rule.** Endothelial nuclei vary in brightness, for example in mitosis or with uneven staining. Dim cancer cells that are out of focus will pass the filter. *Test:* annotate or mark cancer nuclei as well. Report the confusion between the two classes, and sweep `bright_factor` from 1.5 to 4 to see how much the count changes.
2. **Endothelial nuclei hidden under cancer cells.** Dim nuclei next to or under bright blobs get merged with the blob's halo, shrunk or lost. This biases the count down and the area up near tumour clusters. *Test:* compare annotated vs predicted counts and area in cluster regions versus clean regions, not only overall.
3. **Merged or oversplit nuclei.** Splitting depends on `split_h_px`. Oversplitting inflates the count and lowers the area. Merging does the reverse, and the solidity filter removes merged clumps rather than fixing them. *Test:* check how many `low_solidity` rejects are real merged nuclei, and sweep `split_h_px` from 0.5 to 2.
4. **Boundary placement.** A local threshold on blurred widefield data places the edge arbitrarily. That shifts area by more than the biological differences you might be looking for, and aspect ratio shifts with it. *Test:* vary the threshold and check that conclusions don't change. If you compare conditions, use the same pipeline on all of them.
5. **Edge exclusion.** Dropping edge-touching nuclei lowers the count. Compare counts only between images of equal size and field.
6. **Aspect ratio of small objects.** Moment-based aspect ratio is noisy for tiny or pixelated objects, and a 1 px boundary error changes it noticeably. Note that annotation noise limits what you can test.
7. **Single-image tuning.** All defaults are guesses from one picture. Tune on one image and test on a different annotated image, ideally from another experiment or day, with a different cancer-cell density.

## Questions that could change the analysis

- Does your annotation contain **only endothelial nuclei**, with cancer nuclei left as background? If it includes both, I'd add a class column to the evaluation.
- Are cancer nuclei **always brighter** than endothelial ones? If you have a cancer-specific label (a cell tracker or second channel), use it instead of intensity.
- Can you send one image from a **different condition or day**? That would test whether the thresholds generalise.

Requirements: Python 3.13 with `numpy scipy pandas scikit-image tifffile` (scikit-image 0.22 or newer; I've checked the 0.26 changes noted above).

Sources:
- [scikit-image 0.26.0 release notes](https://scikit-image.org/docs/stable/release_notes/release_0.26.html)

## user

Only the endothelial nuclei. The nuclei of the cancer cells are brighter and rounder in DAPI. Only this channel will be available for the analysis. The cancer cells are not fluorescently labelled. I don't know.

## assistant

Your answers settle two things. The annotation can be used directly as ground truth, and the cancer-cell rule can use both brightness and roundness, with DAPI as the only channel. Because "I don't know" came up, I'd rather not guess the cut-offs. I've added a short script that reads them off your annotated image.

## Changes to `analyze_nuclei.py`

**1. `Params`: add two fields.**

```python
    roundish_factor: float = 1.5         # a round object brighter than this x median is cancer-like
    round_max_aspect: float = 1.25       # "round" = aspect ratio below this
```

**2. `describe_objects`: also compute aspect ratio** (replace the `regionprops_table` call and the line after `area_um2`).

```python
    table = pd.DataFrame(measure.regionprops_table(
        labels, intensity_image=raw,
        properties=("label", "area", "solidity", "intensity_mean", "bbox",
                    "major_axis_length", "minor_axis_length")))
    px_area = p.pixel_size_um ** 2
    table["area_um2"] = table["area"] * px_area
    table["aspect_ratio"] = (table["major_axis_length"]
                             / table["minor_axis_length"].clip(lower=1e-6))
```

**3. `reject_reasons`: replace the brightness rule.**

```python
    too_bright = table["intensity_mean"] > p.bright_factor * reference
    round_and_brighter = ((table["aspect_ratio"] < p.round_max_aspect)
                          & (table["intensity_mean"] > p.roundish_factor * reference))
    reason[too_bright | round_and_brighter] = "cancer_like"
```

**4. `main`: save the candidate labels, which the calibration needs.** Add this next to the other debug writes.

```python
    tifffile.imwrite(debug / "candidates.tif", candidates.astype(np.int32))
```

I made roundness count only together with extra brightness. Roundness alone would also remove round endothelial nuclei, and that would bias the aspect ratios you want to measure. Even so, the filter truncates the low end of the aspect-ratio distribution to some degree. To see how much, compare the results with `round_max_aspect = 0` (brightness only) and with the default.

## `calibrate.py`: read the cut-offs off your annotation

Run `python analyze_nuclei.py`, then `python calibrate.py annotation.tif`.

```python
"""Compare candidate objects that match the annotation with those that don't."""
import sys

import numpy as np
import pandas as pd
import tifffile

IOU_MATCH = 0.5


def matched_candidates(gt: np.ndarray, cand: np.ndarray) -> set[int]:
    pairs, inter = np.unique(np.stack([gt.ravel(), cand.ravel()]), axis=1, return_counts=True)
    area_gt, area_c = np.bincount(gt.ravel()), np.bincount(cand.ravel())
    return {int(c) for (g, c), n in zip(pairs.T, inter)
            if g and c and n / (area_gt[g] + area_c[c] - n) > IOU_MATCH}


def main(annotation_path: str) -> None:
    gt = tifffile.imread(annotation_path).astype(np.int64)
    cand = tifffile.imread("debug/candidates.tif").astype(np.int64)
    if gt.shape != cand.shape:
        raise ValueError(f"Shape mismatch: {gt.shape} vs {cand.shape}")
    table = pd.read_csv("debug/all_candidates.csv")
    size_ok = table["area_um2"].between(40, 250)   # same size gate as the pipeline defaults
    table["rel_intensity"] = table["intensity_mean"] / table.loc[size_ok, "intensity_mean"].median()
    table["group"] = np.where(table["label"].isin(matched_candidates(gt, cand)),
                              "matches annotation", "no match")
    cols = ["rel_intensity", "aspect_ratio", "area_um2", "solidity"]
    print(table.groupby("group")[cols].describe(percentiles=[0.05, 0.5, 0.95])
          .T.to_string(float_format=lambda v: f"{v:.2f}"))
    print("\nNo-match objects by pipeline reason:")
    print(table.loc[table.group == "no match", "reject_reason"]
          .replace("", "accepted (false positive)").value_counts().to_string())


if __name__ == "__main__":
    main(sys.argv[1])
```

## How to read the output

- **`bright_factor`:** set it above the 95th percentile of `rel_intensity` for "matches annotation" and below the typical value for the bright no-match objects. If those two ranges overlap, brightness alone can't separate the classes.
- **Roundness rule:** if the matched nuclei rarely have aspect ratio below 1.25, the rule is safe. If many do, drop it (`round_max_aspect = 0`).
- **"accepted (false positive)" row:** these are no-match objects that the pipeline kept. Look at them in `debug/overlay.png` to see whether they are cancer nuclei, merged nuclei, or annotation gaps.
- **Overfitting:** the cut-offs come from a single image. Treat them as provisional until `evaluate.py` passes on an annotated image you didn't calibrate on, ideally from another day or a different cancer-cell density. If you can annotate a second image, I'd tune on one and keep the other as the untouched test.

As before, none of this code has been run. If `evaluate.py` fails, paste its output and the `calibrate.py` table and I'll adjust from there.
