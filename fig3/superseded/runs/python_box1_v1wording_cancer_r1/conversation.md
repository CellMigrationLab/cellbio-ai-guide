# python_box1_v1wording_cancer_r1

## USER (2026-10-17T05:57:40.075Z)

Act as a helpful coding assistant for a cell biologist. You cannot run code. You may use the Read tool ONLY to view the image the user attached: <fig3-work>/bf3/box1_cancer_r1/bf_preview.png (a preview of their file bf.tif). You may use WebSearch and WebFetch to read documentation. Do not open any other file.

The user writes:
"I want to segment the cancer cells in my brightfield image bf.tif and measure their number and area. Write only the segmentation step using an established, maintained library and its documented API. Before writing the code, check the current documentation for the version I have installed (Cellpose 4.2.1.1, CPU only; numpy, scipy, scikit-image, tifffile and pandas are also available) and list the pages you used; if you cannot access it, say so. The input is a single-channel 16-bit 2D image (Y, X), and the pixel size is 0.65 µm per pixel; the cancer cells are round, refractile cells about 15–25 µm across sitting on top of a flat, confluent endothelial monolayer, and the endothelial cells must not be segmented. For every parameter that affects the result, including object size and any internal rescaling, state the value used, whether it is the library default, and why it suits these images. Do not silently resize, normalise, change channels or substitute defaults. Expose consequential parameters, fail clearly on invalid input, return the label image in the original coordinate system, and include a simple test: a script that compares the output with a small manually annotated image I provide (annot.tif, a label image of the same size; object count and F1 score) and saves an overlay of the outlines on the image. List the assumptions I should verify on real data."

Reply as you normally would. Put the segmentation script in ONE complete ```python block that reads bf.tif and saves labels.tif (and areas.csv, areas in µm²); put the test in a SECOND ```python block.

## HARNESS NOTE (2026-10-17T05:57:40.124Z)

<system-reminder>
Your final report is delivered through SubagentHandback: when your work is complete, call SubagentHandback({message: <your full report>}). The call ends your run, so make it your last step. Only a SubagentHandback call reaches your caller as your result; plain text you write at the end is not delivered. Do not also send the report with SendMessage: your caller would get it twice.
</system-reminder>

*[tool call: ToolSearch: select:WebFetch,WebSearch]*

*[tool call: Read: <fig3-work>/bf3/box1_cancer_r1/bf_preview.png]*

*[tool call: WebFetch: https://cellpose.readthedocs.io/en/latest/api.html]*

*[tool call: WebFetch: https://cellpose.readthedocs.io/en/latest/settings.html]*

## ASSISTANT (2026-10-17T05:58:45.441Z)

I checked the documentation, but only the "latest" pages, not pages pinned to 4.2.1.1. I couldn't run any code, so none of this has been tested.

## Documentation pages used
- https://cellpose.readthedocs.io/en/latest/api.html, for the `CellposeModel` and `eval()` signatures, defaults and return values.
- https://cellpose.readthedocs.io/en/latest/settings.html, for diameter, flow_threshold, cellprob_threshold and channels with the cpsam model.

Caveats on those pages:
- They are the "latest" docs. I could not confirm they match 4.2.1.1.
- The API page has internal inconsistencies. It shows older and newer signatures side by side, and the `batch_size` docstring disagrees with the signature.
- `settings.html` does not cover `min_size` or normalisation. Those come from the API page only.
- The default `pretrained_model` is listed as `'cpsam_v2'`. The script prints the model it actually loaded, so check that against your install.
- Please run `help(CellposeModel.eval)` locally to confirm.

## Parameters

| Parameter | Value | Library default? | Why |
|---|---|---|---|
| `gpu` | False | yes | You have CPU only. |
| `pretrained_model` | None, so the library default | yes | I am not substituting a model. The loaded model is printed. |
| `diameter` | None | yes | Cells are about 20 µm, which is 31 px at 0.65 µm/px. The docs say cpsam is trained on a 30 px mean and is largely size-invariant. With `diameter=None` and `rescale=None` there is no internal resizing, so the output is in original pixel coordinates. |
| `rescale` | None (not passed) | yes | Only used when `diameter` is None. The docs say it then defaults to 1.0, so there is no resizing. |
| `normalize` | True | yes | Maps the 1st and 99th percentiles to 0 and 1, applied internally. I do not pre-normalise. Check it on your data, because bright artefacts shift the percentiles. |
| `channels` / `channel_axis` | None | yes | A 2D (Y, X) array is passed as is. cpsam does not take a `channels` argument. |
| `flow_threshold` | 0.4 | yes | Raise it for too few objects, lower it for ill-shaped ones. |
| `cellprob_threshold` | 0.0 | yes | Lower it to get more or larger masks. |
| `min_size` | 15 px | yes | This is about 6 µm², so it only drops specks. The real size filter is the area window below. |
| `batch_size`, `niter`, `tile_overlap`, `bsize`, `augment`, `resample`, `max_size_fraction` | not passed | yes | Library defaults. |
| `min_area_um2` | 78 | no, mine | Equals a 10 µm diameter, which is below your 15–25 µm range. It drops debris and fragments. |
| `max_area_um2` | 962 | no, mine | Equals a 35 µm diameter, which is above your range. It drops merged clumps and large flat endothelial cells. |
| `min_contrast` | 0.25 | no, mine, a guess | See the next paragraph. |

**Excluding endothelium.** Cellpose has no brightfield or endothelium class, so it may well outline the faint endothelial cells. The script therefore adds a post-filter on size and refractile contrast. Contrast is the 5th to 95th percentile intensity range inside each object, divided by the image's 1st to 99th percentile range. Cancer cells have a dark rim and bright halo and should score high. The flat monolayer should score low. The 0.25 threshold is not validated. Every object's features are written to `areas.csv` (kept objects only) so you can tune it. Printing the dropped objects' features would also be worth adding.

## Script: `segment_cancer.py`

```python
#!/usr/bin/env python
"""Segment round refractile cancer cells in a 16-bit brightfield image with Cellpose 4.

Usage: python segment_cancer.py bf.tif --out-labels labels.tif --out-csv areas.csv
Output labels have the same (Y, X) shape as the input; no resizing is done
(diameter=None, rescale=None). Areas are in um^2.
"""
import argparse
import importlib.metadata
import os
import sys
import warnings

import numpy as np
import pandas as pd
import tifffile
from skimage.measure import regionprops
from skimage.segmentation import relabel_sequential

EXPECTED_CELLPOSE = "4.2.1.1"


def load_image(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"Expected a single-channel 2D (Y, X) image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected 16-bit unsigned (uint16) image, got dtype {img.dtype}")
    if min(img.shape) < 64:
        raise ValueError(f"Image too small: {img.shape}")
    if img.max() == img.min():
        raise ValueError("Image is constant; nothing to segment.")
    return img


def segment_cancer_cells(
    image,
    pixel_size_um=0.65,
    # --- Cellpose parameters (library defaults unless noted) ---
    pretrained_model=None,       # None -> library default model
    diameter=None,               # None -> no internal rescaling (cpsam is size-invariant)
    flow_threshold=0.4,          # library default
    cellprob_threshold=0.0,      # library default
    min_size=15,                 # library default (pixels)
    normalize=True,              # library default (1-99 percentile)
    # --- post-filters (NOT library defaults; tune on real data) ---
    min_area_um2=78.0,           # ~10 um diameter
    max_area_um2=962.0,          # ~35 um diameter
    min_contrast=0.25,           # refractile-contrast threshold to reject endothelium
):
    if not (np.isfinite(pixel_size_um) and pixel_size_um > 0):
        raise ValueError("pixel_size_um must be a positive number")
    if min_area_um2 >= max_area_um2:
        raise ValueError("min_area_um2 must be < max_area_um2")
    if image.ndim != 2 or image.dtype != np.uint16:
        raise ValueError("image must be a 2D uint16 array")

    try:
        ver = importlib.metadata.version("cellpose")
    except importlib.metadata.PackageNotFoundError:
        raise ImportError("cellpose is not installed")
    if ver != EXPECTED_CELLPOSE:
        warnings.warn(f"Cellpose {ver} installed, script written for {EXPECTED_CELLPOSE}")

    from cellpose import models

    kw = {} if pretrained_model is None else {"pretrained_model": pretrained_model}
    model = models.CellposeModel(gpu=False, **kw)
    print(f"Cellpose {ver}; model: {getattr(model, 'pretrained_model', 'unknown')}", file=sys.stderr)

    masks, _flows, _styles = model.eval(
        image,
        diameter=diameter,
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold,
        min_size=min_size,
        normalize=normalize,
    )
    masks = np.asarray(masks)
    if masks.shape != image.shape:
        raise RuntimeError(f"Output shape {masks.shape} != input shape {image.shape}; "
                           "refusing to return labels in a different coordinate system.")

    # Per-object features
    lo, hi = np.percentile(image, [1, 99]).astype(float)
    scale = hi - lo
    if scale <= 0:
        raise ValueError("Image has no dynamic range between 1st and 99th percentile.")
    im = image.astype(float)
    h, w = image.shape
    px_area = pixel_size_um ** 2
    rows = []
    keep = np.zeros(masks.max() + 1, dtype=bool)
    for rp in regionprops(masks):
        vals = im[rp.coords[:, 0], rp.coords[:, 1]]
        p5, p95 = np.percentile(vals, [5, 95])
        contrast = (p95 - p5) / scale
        area_um2 = rp.area * px_area
        minr, minc, maxr, maxc = rp.bbox
        border = minr == 0 or minc == 0 or maxr == h or maxc == w
        ok = (min_area_um2 <= area_um2 <= max_area_um2) and (contrast >= min_contrast)
        keep[rp.label] = ok
        rows.append(dict(cellpose_label=rp.label, area_px=int(rp.area), area_um2=area_um2,
                         contrast=contrast, touches_border=border, kept=ok))
    table = pd.DataFrame(rows)

    filtered = np.where(keep[masks], masks, 0)
    labels, _, _ = relabel_sequential(filtered)
    labels = labels.astype(np.uint16)
    old_to_new = {}
    for new in np.unique(labels)[1:]:
        old = masks[labels == new][0]
        old_to_new[old] = new
    if len(table):
        kept = table[table.kept].copy()
        kept["label"] = kept.cellpose_label.map(old_to_new)
        kept = kept.drop(columns=["kept"]).sort_values("label")
    else:
        kept = pd.DataFrame(columns=["cellpose_label", "area_px", "area_um2", "contrast",
                                     "touches_border", "label"])
    print(f"Cellpose objects: {len(table)}; kept after size/contrast filter: {len(kept)}",
          file=sys.stderr)
    return labels, kept[["label", "area_um2", "area_px", "contrast", "touches_border"]]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("image", nargs="?", default="bf.tif")
    p.add_argument("--out-labels", default="labels.tif")
    p.add_argument("--out-csv", default="areas.csv")
    p.add_argument("--pixel-size-um", type=float, default=0.65)
    p.add_argument("--diameter", type=float, default=None)
    p.add_argument("--flow-threshold", type=float, default=0.4)
    p.add_argument("--cellprob-threshold", type=float, default=0.0)
    p.add_argument("--min-size", type=int, default=15)
    p.add_argument("--min-area-um2", type=float, default=78.0)
    p.add_argument("--max-area-um2", type=float, default=962.0)
    p.add_argument("--min-contrast", type=float, default=0.25)
    a = p.parse_args()

    img = load_image(a.image)
    labels, table = segment_cancer_cells(
        img, pixel_size_um=a.pixel_size_um, diameter=a.diameter,
        flow_threshold=a.flow_threshold, cellprob_threshold=a.cellprob_threshold,
        min_size=a.min_size, min_area_um2=a.min_area_um2,
        max_area_um2=a.max_area_um2, min_contrast=a.min_contrast)
    tifffile.imwrite(a.out_labels, labels)
    table.to_csv(a.out_csv, index=False)
    print(f"Wrote {a.out_labels} and {a.out_csv}: {len(table)} cells, "
          f"median area {table.area_um2.median() if len(table) else float('nan'):.1f} um^2")


if __name__ == "__main__":
    main()
```

## Test: `test_segmentation.py`

```python
#!/usr/bin/env python
"""Compare labels with a manual annotation (annot.tif): object counts, F1 at IoU>=0.5,
and save an outline overlay.  Usage: python test_segmentation.py bf.tif labels.tif annot.tif
"""
import sys

import numpy as np
import tifffile
from scipy.optimize import linear_sum_assignment
from skimage.segmentation import find_boundaries

IOU_THRESHOLD = 0.5  # a prediction matches if IoU >= this


def f1_score(pred, ref, thr=IOU_THRESHOLD):
    p_ids = np.unique(pred)[1:]
    r_ids = np.unique(ref)[1:]
    if len(p_ids) == 0 or len(r_ids) == 0:
        tp = 0
    else:
        p_idx = {v: i for i, v in enumerate(p_ids)}
        r_idx = {v: i for i, v in enumerate(r_ids)}
        inter = np.zeros((len(p_ids), len(r_ids)))
        both = (pred > 0) & (ref > 0)
        for a, b in zip(pred[both], ref[both]):
            inter[p_idx[a], r_idx[b]] += 1
        p_area = np.array([(pred == v).sum() for v in p_ids])
        r_area = np.array([(ref == v).sum() for v in r_ids])
        iou = inter / (p_area[:, None] + r_area[None, :] - inter)
        rows, cols = linear_sum_assignment(-iou)
        tp = int((iou[rows, cols] >= thr).sum())
    fp, fn = len(p_ids) - tp, len(r_ids) - tp
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 1.0
    return len(p_ids), len(r_ids), tp, fp, fn, f1


def main(bf_path, labels_path, annot_path):
    img = tifffile.imread(bf_path)
    pred = tifffile.imread(labels_path)
    ref = tifffile.imread(annot_path)
    if not (img.shape == pred.shape == ref.shape) or img.ndim != 2:
        raise ValueError(f"Shapes must match and be 2D: image {img.shape}, "
                         f"labels {pred.shape}, annot {ref.shape}")

    n_pred, n_ref, tp, fp, fn, f1 = f1_score(pred, ref)
    print(f"Predicted objects: {n_pred}\nAnnotated objects: {n_ref}")
    print(f"IoU threshold {IOU_THRESHOLD}: TP={tp} FP={fp} FN={fn}  F1={f1:.3f}")

    # Overlay (display-only contrast stretch; does not touch the data)
    lo, hi = np.percentile(img, [1, 99])
    disp = np.clip((img.astype(float) - lo) / (hi - lo), 0, 1)
    rgb = np.dstack([disp] * 3)
    rgb[find_boundaries(pred, mode="outer")] = [1, 0, 0]   # prediction: red
    rgb[find_boundaries(ref, mode="outer") & ~find_boundaries(pred, mode="outer")] = [0, 1, 0]  # annotation: green
    tifffile.imwrite("overlay.tif", (rgb * 255).astype(np.uint8), photometric="rgb")
    print("Saved overlay.tif (red = prediction, green = annotation)")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
```

## Assumptions to verify on real data
1. **Cellpose may segment the endothelium.** Check the overlay and the `contrast` column for known endothelial objects. Retune `min_contrast`; 0.25 is a guess.
2. **Pixel size** really is 0.65 µm/px and is the same in x and y. All areas depend on it.
3. **Cell size.** Cancer cells should fall in the 78–962 µm² window. In your preview, some cells look smaller than 15 µm, so check that the lower limit is not cutting real cells.
4. **Touching clusters.** These may merge into one object or split wrongly. Merged ones get dropped by the area ceiling, which would undercount. Look at the clumps, for example at top left and bottom centre.
5. **Debris and bright artefacts.** Dark debris and bright halos can pass the filters. Percentile normalisation can also shift when bright artefacts are present.
6. **Border cells** are kept but flagged in `touches_border`. Decide whether to exclude them from area statistics.
7. **Same imaging conditions.** The contrast threshold is relative to each image's own range. It may not transfer across different focus or illumination.
8. **Annotation.** `annot.tif` should contain only cancer cells, and an F1 from a small image is noisy. The IoU 0.5 matching threshold is my choice.
9. **Docs and install.** Confirm the signature and default model with `help(CellposeModel.eval)`. Also confirm the default model name that the script prints.

Files: the script and test are inline above. I did not write them to disk, as I had no instruction to create files.

## ASSISTANT (final report)

## Documentation pages used
- https://cellpose.readthedocs.io/en/latest/api.html (CellposeModel and eval() signature, defaults, return values)
- https://cellpose.readthedocs.io/en/latest/settings.html (diameter, flow_threshold, cellprob_threshold, channels for cpsam)

Caveats: these are the "latest" docs, not pinned to 4.2.1.1, so I could not confirm they match the installed version. The API page contains internal inconsistencies (older and newer signatures side by side; batch_size docstring vs signature). settings.html does not cover min_size or normalisation; those come from the API page only. Default pretrained_model is listed as 'cpsam_v2'; the script prints the model actually loaded. User should run help(CellposeModel.eval) locally. I could not run any code, so nothing is tested.

## Parameters
| Parameter | Value | Library default? | Why |
|---|---|---|---|
| gpu | False | yes | CPU only |
| pretrained_model | None (library default) | yes | not substituting a model; loaded model is printed |
| diameter | None | yes | cells ~20 um = ~31 px at 0.65 um/px, matching cpsam's 30 px training mean; cpsam is largely size-invariant; no internal rescaling, so output is in original pixel coordinates |
| rescale | None (not passed) | yes | only used when diameter is None; docs say defaults to 1.0, i.e. no resizing |
| normalize | True | yes | 1st/99th percentile to 0/1, done internally; no pre-normalisation; check against bright artefacts |
| channels / channel_axis | None | yes | 2D (Y,X) array passed as is; cpsam takes no channels argument |
| flow_threshold | 0.4 | yes | raise for too few objects, lower for ill-shaped ones |
| cellprob_threshold | 0.0 | yes | lower for more or larger masks |
| min_size | 15 px | yes | ~6 um^2, drops only specks; real size filter is the area window |
| batch_size, niter, tile_overlap, bsize, augment, resample, max_size_fraction | not passed | yes | library defaults |
| min_area_um2 | 78 | no, mine | = 10 um diameter, below the 15-25 um range; drops debris and fragments |
| max_area_um2 | 962 | no, mine | = 35 um diameter, above the range; drops merged clumps and large flat endothelial cells |
| min_contrast | 0.25 | no, mine, a guess | see below |

Excluding endothelium: Cellpose has no brightfield or endothelium class, so it may outline the faint endothelial cells. The script adds a post-filter on size and refractile contrast, defined as the 5th-95th percentile intensity range inside each object divided by the image's 1st-99th percentile range. Cancer cells (dark rim, bright halo) should score high; the flat monolayer low. 0.25 is not validated. All features for kept objects go to areas.csv for tuning.

## Script: segment_cancer.py
```python
#!/usr/bin/env python
"""Segment round refractile cancer cells in a 16-bit brightfield image with Cellpose 4.

Usage: python segment_cancer.py bf.tif --out-labels labels.tif --out-csv areas.csv
Output labels have the same (Y, X) shape as the input; no resizing is done
(diameter=None, rescale=None). Areas are in um^2.
"""
import argparse
import importlib.metadata
import os
import sys
import warnings

import numpy as np
import pandas as pd
import tifffile
from skimage.measure import regionprops
from skimage.segmentation import relabel_sequential

EXPECTED_CELLPOSE = "4.2.1.1"


def load_image(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"Expected a single-channel 2D (Y, X) image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected 16-bit unsigned (uint16) image, got dtype {img.dtype}")
    if min(img.shape) < 64:
        raise ValueError(f"Image too small: {img.shape}")
    if img.max() == img.min():
        raise ValueError("Image is constant; nothing to segment.")
    return img


def segment_cancer_cells(
    image,
    pixel_size_um=0.65,
    # --- Cellpose parameters (library defaults unless noted) ---
    pretrained_model=None,       # None -> library default model
    diameter=None,               # None -> no internal rescaling (cpsam is size-invariant)
    flow_threshold=0.4,          # library default
    cellprob_threshold=0.0,      # library default
    min_size=15,                 # library default (pixels)
    normalize=True,              # library default (1-99 percentile)
    # --- post-filters (NOT library defaults; tune on real data) ---
    min_area_um2=78.0,           # ~10 um diameter
    max_area_um2=962.0,          # ~35 um diameter
    min_contrast=0.25,           # refractile-contrast threshold to reject endothelium
):
    if not (np.isfinite(pixel_size_um) and pixel_size_um > 0):
        raise ValueError("pixel_size_um must be a positive number")
    if min_area_um2 >= max_area_um2:
        raise ValueError("min_area_um2 must be < max_area_um2")
    if image.ndim != 2 or image.dtype != np.uint16:
        raise ValueError("image must be a 2D uint16 array")

    try:
        ver = importlib.metadata.version("cellpose")
    except importlib.metadata.PackageNotFoundError:
        raise ImportError("cellpose is not installed")
    if ver != EXPECTED_CELLPOSE:
        warnings.warn(f"Cellpose {ver} installed, script written for {EXPECTED_CELLPOSE}")

    from cellpose import models

    kw = {} if pretrained_model is None else {"pretrained_model": pretrained_model}
    model = models.CellposeModel(gpu=False, **kw)
    print(f"Cellpose {ver}; model: {getattr(model, 'pretrained_model', 'unknown')}", file=sys.stderr)

    masks, _flows, _styles = model.eval(
        image,
        diameter=diameter,
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold,
        min_size=min_size,
        normalize=normalize,
    )
    masks = np.asarray(masks)
    if masks.shape != image.shape:
        raise RuntimeError(f"Output shape {masks.shape} != input shape {image.shape}; "
                           "refusing to return labels in a different coordinate system.")

    # Per-object features
    lo, hi = np.percentile(image, [1, 99]).astype(float)
    scale = hi - lo
    if scale <= 0:
        raise ValueError("Image has no dynamic range between 1st and 99th percentile.")
    im = image.astype(float)
    h, w = image.shape
    px_area = pixel_size_um ** 2
    rows = []
    keep = np.zeros(masks.max() + 1, dtype=bool)
    for rp in regionprops(masks):
        vals = im[rp.coords[:, 0], rp.coords[:, 1]]
        p5, p95 = np.percentile(vals, [5, 95])
        contrast = (p95 - p5) / scale
        area_um2 = rp.area * px_area
        minr, minc, maxr, maxc = rp.bbox
        border = minr == 0 or minc == 0 or maxr == h or maxc == w
        ok = (min_area_um2 <= area_um2 <= max_area_um2) and (contrast >= min_contrast)
        keep[rp.label] = ok
        rows.append(dict(cellpose_label=rp.label, area_px=int(rp.area), area_um2=area_um2,
                         contrast=contrast, touches_border=border, kept=ok))
    table = pd.DataFrame(rows)

    filtered = np.where(keep[masks], masks, 0)
    labels, _, _ = relabel_sequential(filtered)
    labels = labels.astype(np.uint16)
    old_to_new = {}
    for new in np.unique(labels)[1:]:
        old = masks[labels == new][0]
        old_to_new[old] = new
    if len(table):
        kept = table[table.kept].copy()
        kept["label"] = kept.cellpose_label.map(old_to_new)
        kept = kept.drop(columns=["kept"]).sort_values("label")
    else:
        kept = pd.DataFrame(columns=["cellpose_label", "area_px", "area_um2", "contrast",
                                     "touches_border", "label"])
    print(f"Cellpose objects: {len(table)}; kept after size/contrast filter: {len(kept)}",
          file=sys.stderr)
    return labels, kept[["label", "area_um2", "area_px", "contrast", "touches_border"]]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("image", nargs="?", default="bf.tif")
    p.add_argument("--out-labels", default="labels.tif")
    p.add_argument("--out-csv", default="areas.csv")
    p.add_argument("--pixel-size-um", type=float, default=0.65)
    p.add_argument("--diameter", type=float, default=None)
    p.add_argument("--flow-threshold", type=float, default=0.4)
    p.add_argument("--cellprob-threshold", type=float, default=0.0)
    p.add_argument("--min-size", type=int, default=15)
    p.add_argument("--min-area-um2", type=float, default=78.0)
    p.add_argument("--max-area-um2", type=float, default=962.0)
    p.add_argument("--min-contrast", type=float, default=0.25)
    a = p.parse_args()

    img = load_image(a.image)
    labels, table = segment_cancer_cells(
        img, pixel_size_um=a.pixel_size_um, diameter=a.diameter,
        flow_threshold=a.flow_threshold, cellprob_threshold=a.cellprob_threshold,
        min_size=a.min_size, min_area_um2=a.min_area_um2,
        max_area_um2=a.max_area_um2, min_contrast=a.min_contrast)
    tifffile.imwrite(a.out_labels, labels)
    table.to_csv(a.out_csv, index=False)
    print(f"Wrote {a.out_labels} and {a.out_csv}: {len(table)} cells, "
          f"median area {table.area_um2.median() if len(table) else float('nan'):.1f} um^2")


if __name__ == "__main__":
    main()
```

## Test: test_segmentation.py
```python
#!/usr/bin/env python
"""Compare labels with a manual annotation (annot.tif): object counts, F1 at IoU>=0.5,
and save an outline overlay.  Usage: python test_segmentation.py bf.tif labels.tif annot.tif
"""
import sys

import numpy as np
import tifffile
from scipy.optimize import linear_sum_assignment
from skimage.segmentation import find_boundaries

IOU_THRESHOLD = 0.5  # a prediction matches if IoU >= this


def f1_score(pred, ref, thr=IOU_THRESHOLD):
    p_ids = np.unique(pred)[1:]
    r_ids = np.unique(ref)[1:]
    if len(p_ids) == 0 or len(r_ids) == 0:
        tp = 0
    else:
        p_idx = {v: i for i, v in enumerate(p_ids)}
        r_idx = {v: i for i, v in enumerate(r_ids)}
        inter = np.zeros((len(p_ids), len(r_ids)))
        both = (pred > 0) & (ref > 0)
        for a, b in zip(pred[both], ref[both]):
            inter[p_idx[a], r_idx[b]] += 1
        p_area = np.array([(pred == v).sum() for v in p_ids])
        r_area = np.array([(ref == v).sum() for v in r_ids])
        iou = inter / (p_area[:, None] + r_area[None, :] - inter)
        rows, cols = linear_sum_assignment(-iou)
        tp = int((iou[rows, cols] >= thr).sum())
    fp, fn = len(p_ids) - tp, len(r_ids) - tp
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 1.0
    return len(p_ids), len(r_ids), tp, fp, fn, f1


def main(bf_path, labels_path, annot_path):
    img = tifffile.imread(bf_path)
    pred = tifffile.imread(labels_path)
    ref = tifffile.imread(annot_path)
    if not (img.shape == pred.shape == ref.shape) or img.ndim != 2:
        raise ValueError(f"Shapes must match and be 2D: image {img.shape}, "
                         f"labels {pred.shape}, annot {ref.shape}")

    n_pred, n_ref, tp, fp, fn, f1 = f1_score(pred, ref)
    print(f"Predicted objects: {n_pred}\nAnnotated objects: {n_ref}")
    print(f"IoU threshold {IOU_THRESHOLD}: TP={tp} FP={fp} FN={fn}  F1={f1:.3f}")

    # Overlay (display-only contrast stretch; does not touch the data)
    lo, hi = np.percentile(img, [1, 99])
    disp = np.clip((img.astype(float) - lo) / (hi - lo), 0, 1)
    rgb = np.dstack([disp] * 3)
    rgb[find_boundaries(pred, mode="outer")] = [1, 0, 0]   # prediction: red
    rgb[find_boundaries(ref, mode="outer") & ~find_boundaries(pred, mode="outer")] = [0, 1, 0]  # annotation: green
    tifffile.imwrite("overlay.tif", (rgb * 255).astype(np.uint8), photometric="rgb")
    print("Saved overlay.tif (red = prediction, green = annotation)")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
```

## Assumptions to verify on real data
1. Cellpose may segment the endothelium. Check the overlay and the contrast column for known endothelial objects and retune min_contrast; 0.25 is a guess.
2. Pixel size really is 0.65 um/px and the same in x and y; all areas depend on it.
3. Cancer cells fall in the 78-962 um^2 window. Some cells in the preview look smaller than 15 um, so check the lower limit is not cutting real cells.
4. Touching clusters may merge or split wrongly; merged ones get dropped by the area ceiling and would undercount (e.g. clumps at top left and bottom centre of the preview).
5. Dark debris and bright halo artefacts can pass the filters; percentile normalisation can shift when bright artefacts are present.
6. Border cells are kept but flagged in touches_border; decide whether to exclude them from area statistics.
7. Contrast is relative to each image's own range, so it may not transfer across different focus or illumination.
8. annot.tif should contain only cancer cells; F1 from a small image is noisy; the IoU 0.5 match threshold is my choice.
9. Confirm the signature and default model with help(CellposeModel.eval) and the model name the script prints.

Files: the script and test are inline above; I did not write them to disk, as no instruction was given to create files. I read only the preview image <fig3-work>/bf3/box1_cancer_r1/bf_preview.png.
