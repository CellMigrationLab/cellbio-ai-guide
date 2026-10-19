# code_box1_endo_r3

## user

You are an AI assistant chatting with a user. You can search the web (WebSearch and WebFetch; load them with ToolSearch if they are not listed). The user attached a file, which you can view: /home/user/sessions_v2/v050/image.png. You cannot run code; the user will run your script. Reply to the user as you normally would.

I want to segment and count the endothelial cells and measure their shape (area and aspect ratio) from brightfield images of a confluent endothelial monolayer (some cancer cells sit on top). Help me write the analysis as a Python script.
My images are 2D, with axes Y, X, channels 1 (brightfield), data type uint16 (12-bit values), pixel/voxel size 0.65 µm, and objects of interest approximately 25–50 µm in size. I use Python 3.13 on a laptop CPU (no GPU). The output I need is a label image with one integer per endothelial cell (0 = background) and a table with the area (µm²) and aspect ratio of each endothelial cell. I can provide a manual annotation of this image (a label image).
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

I'll look at the image first.

## assistant (tool call: Read)

```json
{
 "file_path": "/home/user/sessions_v2/v050/image.png"
}
```

## tool result

```
[{"type": "image", "note": "image shown to the subject"}]
```

## assistant (tool call: WebFetch)

```json
{
 "url": "https://cellpose.readthedocs.io/en/latest/api.html",
 "prompt": "Cellpose 4 / cpsam: how to instantiate CellposeModel (gpu arg, pretrained_model), eval() signature and parameters (diameter, flow_threshold, cellprob_threshold, niter, min_size, normalize, batch_size, bsize), return values, and any note about diameter/resizing and image channels. Also default normalization."
}
```

## assistant (tool call: WebFetch)

```json
{
 "url": "https://cellpose.readthedocs.io/en/latest/settings.html",
 "prompt": "What does the doc say about diameter in Cellpose-SAM (cpsam), recommended object size, CPU speed, normalization, and flow_threshold/cellprob_threshold?"
}
```

## tool result

```
**Diameter:** The doc says Cellpose-SAM was "trained on images with ROI diameters from size 7.5 to 120, with a mean diameter of 30 pixels." Because the model is fairly size-invariant, specifying the diameter is optional. If cells are very large, you can set a diameter to downsample the image, which speeds up runs. For example, a diameter of 90 downsamples by a factor of 3.

**Recommended object size:** The training range is 7.5 to 120 pixels in diameter, with a mean of 30 pixels.

**CPU speed:** The doc doesn't cover CPU performance. It only notes that downsampling via the diameter setting increases run speed.

**Normalization:** The doc doesn't mention image normalization.

**flow_threshold:** The default is 0.4, the maximum allowed error of the flows for each mask. Increase it if you get fewer ROIs than expected, and decrease it if you get too many ill-shaped ROIs.

**cellprob_threshold:** The default is 0.0. Pixels above this value are used to run dynamics and determine ROIs. Decrease it if you get too few ROIs, and increase it if you get too many, especially from dim areas.
```

## tool result

```
## Cellpose 4 / cpsam quick reference

**Instantiation**
- `cellpose.models.CellposeModel(gpu=False, pretrained_model='cpsam_v2', model_type=None, diam_mean=None, device=None, nchan=None, use_bfloat16=True)`
- The page also lists an older `__init__` with `pretrained_model=False` and `diam_mean=30.`, so the two signatures conflict.

**eval() parameters (main signature)**
- `x`, `batch_size=8`, `resample=True`, `channels=None`, `channel_axis=None`, `z_axis=None`
- `normalize=True`, `rescale=None`, `diameter=None`
- `flow_threshold=0.4`, `cellprob_threshold=0.0`, `do_3D=False`, `anisotropy=None`, `flow3D_smooth=0`
- `stitch_threshold=0.0`, `min_size=15`, `max_size_fraction=0.4`, `niter=None`
- `augment=False`, `tile_overlap=0.1`, `bsize=None`, `compute_masks=True`, `progress=None`
- The docstring says `batch_size` "Defaults to 64," but the signature shows 8. The earlier eval entry also lists `bsize=256` and `interp=True`.

**Return values**
- A tuple of `(masks, flows, styles)`.
- `masks`: labelled array where 0 means no mask and 1, 2, … are mask labels.
- `flows`: `flows[k][0]` is XY flow in HSV, `[1]` is XY flows, `[2]` is cell probability, and `[3]` is final pixel locations.
- `styles`: a vector of zeros, kept for compatibility with Cellpose 3.

**Diameter, resizing, and block size**
- The page says diameters "are used to rescale the image to 30 pix cell diameter."
- `rescale` is only used when `diameter` is None, and it defaults to 1.0 in that case.
- `bsize` is 384 for cpdino (adjustable) and must be 256 for cpsam.

**Channels**
- The eval docs say "Images must have 3 channels." The transforms docs say images are converted to 3 channels, and only the first 3 are used if there are more.
- If `channel_axis` is None, the channel axis is determined automatically.

**Default normalization**
- `normalize=True` scales each channel so that 0.0 maps to the 1st percentile and 1.0 to the 99th percentile of intensities.
- A dictionary can override this, with optional keys such as `lowhigh`, `sharpen`, `percentile`, `tile_norm_blocksize`, and `norm3D`.

[WebFetch note: this page's text is 100080 characters long and the answer above covers only characters 0 to 100000; the final 80 were not read — to read on, call WebFetch again with the same url and offset: 100000.]
```

## assistant

I looked at the image and wrote the scripts below, but I can't run code, so none of this is tested. The first run on your data is the real test.

## What I see in the image

- **Endothelial cells:** the monolayer is confluent and the borders are very faint. At 0.65 µm/px, 25–50 µm is about 40–75 px, which matches what I see.
- **Cancer cells:** round, about 20 µm, with a strong bright and dark halo. They sit on top and hide the cells below them.
- **Debris:** small dark clumps.
- **Left half versus right half:** the left half is dark and phase-like, and the right half is bright and flat. The step is exactly at the midline, so it looks like two stitched tiles or two acquisitions.

## Questions that could change the analysis

1. Is that left/right step also present in `image.tif`? If the halves came from different acquisitions, I'd report results per half. The flat-field step below also creates an artefact near the seam.
2. How should cells partly hidden under a cancer cell be treated? I assumed they are excluded. The script drops any cell that overlaps a cancer-cell mask by more than 30%.
3. When you annotate, outline only endothelial cells, and outline every fully visible one. I'll compare only the cells the script also keeps, using the same border and cancer-overlap rules.

## Method

- **Cellpose-SAM (`cellpose>=4`) on a flat-fielded image.** It is the maintained generalist model and handles 2D greyscale input, with training diameters of 7.5–120 px (mean 30 px).
- **Suitability is uncertain.** Faint-border brightfield monolayers may be sparsely represented in its training data. Your annotation is the check.
- **Resizing:** I set `diameter` to 40 µm (about 61 px), so Cellpose downsamples by about 2× to its 30 px reference scale. That is also faster on CPU. Masks come back at the original resolution, so the coordinates are unchanged.
- **Docs caveats:** the `eval` signature (`diameter`, `flow_threshold`, `cellprob_threshold`, `normalize`, `min_size`) comes from the current docs. The docs list two conflicting `CellposeModel.__init__` signatures, so I use only `CellposeModel(gpu=False)`. The first run downloads the model weights.
- **Cancer cells** are found with a classical heuristic: strong local edges, ring closing, hole filling, then size and solidity filters. It is the least certain part and must be checked on the overlay.
- **Measurements:**
  - Area is the pixel count × 0.65² µm².
  - Aspect ratio is the major/minor axis of the ellipse with the same second moments, so it is ≥ 1.
- **Border-touching cells are removed**, because their area and shape are truncated.

Install with `pip install "cellpose>=4" tifffile scikit-image scipy pandas numpy`.

## `segment_endothelial.py`

```python
"""Segment endothelial cells in a brightfield monolayer and measure area and aspect ratio.

Input : image.tif (2D, uint16 holding 12-bit values), pixel size 0.65 um.
Output: labels.tif, measurements.csv, intermediates/ (flat-field, raw labels, cancer mask, overlay).
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import io, measure, morphology, segmentation

MAX_12BIT = 4095


@dataclass(frozen=True)
class Params:
    pixel_size_um: float = 0.65
    expected_cell_diameter_um: float = 40.0   # passed to Cellpose as diameter (converted to px)
    background_sigma_um: float = 65.0         # flat-field scale; must exceed cell size
    clip_percentiles: tuple[float, float] = (1.0, 99.0)  # contrast stretch to [0, 1]
    flow_threshold: float = 0.4               # Cellpose default
    cellprob_threshold: float = 0.0           # Cellpose default
    min_area_um2: float = 200.0               # drop fragments
    max_area_um2: float = 6000.0              # drop merged cells / background blobs
    # cancer-cell heuristic
    edge_sigma_um: float = 1.0
    edge_robust_z: float = 6.0                # edge strength in robust z-scores
    ring_close_radius_um: float = 1.5
    cancer_min_area_um2: float = 100.0
    cancer_max_area_um2: float = 1200.0
    cancer_min_solidity: float = 0.85
    max_cancer_overlap: float = 0.3           # drop endothelial labels overlapping cancer mask more than this


# ---------- input ----------
def read_image(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found in working directory")
    image = np.squeeze(tifffile.imread(path))
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    if image.max() > MAX_12BIT:
        raise ValueError(f"Max value {image.max()} exceeds 12-bit range ({MAX_12BIT})")
    if image.min() == image.max():
        raise ValueError("Image is constant")
    return image


# ---------- preprocessing ----------
def flat_field(image: np.ndarray, p: Params) -> np.ndarray:
    """Divide by a heavily blurred copy (removes slow illumination change), then
    stretch the p1-p99 range to [0, 1]. Output float32, same shape as input."""
    img = image.astype(np.float32)
    background = ndi.gaussian_filter(img, p.background_sigma_um / p.pixel_size_um, mode="reflect")
    if background.min() <= 0:
        raise ValueError("Non-positive background estimate; cannot flat-field")
    relative = img / background
    low, high = np.percentile(relative, p.clip_percentiles)
    if high <= low:
        raise ValueError("Degenerate contrast range after flat-fielding")
    return np.clip((relative - low) / (high - low), 0, 1).astype(np.float32)


# ---------- segmentation ----------
def run_cellpose(flat: np.ndarray, p: Params) -> np.ndarray:
    import cellpose
    from cellpose import models

    print(f"cellpose version {cellpose.version if hasattr(cellpose, 'version') else 'unknown'}")
    model = models.CellposeModel(gpu=False)
    diameter_px = p.expected_cell_diameter_um / p.pixel_size_um
    masks, _, _ = model.eval(
        flat,
        diameter=diameter_px,
        normalize=False,  # already scaled to [0, 1] above
        flow_threshold=p.flow_threshold,
        cellprob_threshold=p.cellprob_threshold,
    )
    if masks.shape != flat.shape:
        raise RuntimeError(f"Cellpose returned shape {masks.shape}, expected {flat.shape}")
    return masks.astype(np.int32)


def detect_cancer_cells(flat: np.ndarray, p: Params) -> np.ndarray:
    """Heuristic boolean mask of round cells with a strong halo (cancer cells on top)."""
    edge = ndi.gaussian_gradient_magnitude(flat, p.edge_sigma_um / p.pixel_size_um)
    median = np.median(edge)
    mad = np.median(np.abs(edge - median))
    if mad == 0:
        raise ValueError("Edge MAD is zero; cannot normalise edge strength")
    strong = (edge - median) / (1.4826 * mad) > p.edge_robust_z
    radius = max(1, round(p.ring_close_radius_um / p.pixel_size_um))
    disk = morphology.disk(radius)
    closed = ndi.binary_dilation(strong, disk)
    filled = ndi.binary_erosion(ndi.binary_fill_holes(closed), disk)

    px_area = p.pixel_size_um ** 2
    mask = np.zeros_like(filled)
    for region in measure.regionprops(measure.label(filled)):
        area_um2 = region.area * px_area
        if (p.cancer_min_area_um2 <= area_um2 <= p.cancer_max_area_um2
                and region.solidity >= p.cancer_min_solidity):
            mask[tuple(region.coords.T)] = True
    return mask


# ---------- label filtering (each step reports what it removed) ----------
def _remove(labels: np.ndarray, ids: np.ndarray) -> np.ndarray:
    out = labels.copy()
    out[np.isin(out, ids)] = 0
    return out


def drop_border_labels(labels: np.ndarray) -> tuple[np.ndarray, int]:
    edge_ids = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    edge_ids = edge_ids[edge_ids > 0]
    return _remove(labels, edge_ids), len(edge_ids)


def drop_labels_overlapping_mask(labels: np.ndarray, mask: np.ndarray, max_fraction: float):
    n = labels.max() + 1
    overlap = np.bincount(labels[mask], minlength=n)
    area = np.bincount(labels.ravel(), minlength=n)
    fraction = overlap / np.maximum(area, 1)
    ids = np.flatnonzero(fraction > max_fraction)
    ids = ids[ids > 0]
    return _remove(labels, ids), len(ids)


def drop_by_area(labels: np.ndarray, min_px: float, max_px: float) -> tuple[np.ndarray, int]:
    area = np.bincount(labels.ravel())
    ids = np.flatnonzero((area < min_px) | (area > max_px))
    ids = ids[(ids > 0) & (area[ids] > 0)]
    return _remove(labels, ids), len(ids)


# ---------- measurement and outputs ----------
def measure_cells(labels: np.ndarray, pixel_size_um: float) -> pd.DataFrame:
    rows = []
    for r in measure.regionprops(labels):
        if r.minor_axis_length == 0:
            raise ValueError(f"Label {r.label} has zero minor axis; cannot compute aspect ratio")
        rows.append({
            "label": r.label,
            "area_um2": r.area * pixel_size_um ** 2,
            "aspect_ratio": r.major_axis_length / r.minor_axis_length,
        })
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio"])


def save_overlay(flat: np.ndarray, labels: np.ndarray, cancer: np.ndarray, path: Path) -> None:
    rgb = np.repeat((flat[..., None] * 255).astype(np.uint8), 3, axis=2)
    rgb[segmentation.find_boundaries(labels, mode="inner")] = (0, 255, 0)   # endothelial = green
    rgb[segmentation.find_boundaries(cancer, mode="inner")] = (255, 0, 0)   # cancer mask = red
    io.imsave(path, rgb, check_contrast=False)


def analyse(image_path: Path, p: Params, out_dir: Path, inter_dir: Path) -> None:
    inter_dir.mkdir(exist_ok=True)
    image = read_image(image_path)
    flat = flat_field(image, p)
    tifffile.imwrite(inter_dir / "flat_field.tif", flat)

    raw = run_cellpose(flat, p)
    tifffile.imwrite(inter_dir / "labels_raw.tif", raw.astype(np.uint16))
    print(f"Cellpose objects: {len(np.unique(raw)) - 1}")

    cancer = detect_cancer_cells(flat, p)
    tifffile.imwrite(inter_dir / "cancer_mask.tif", cancer.astype(np.uint8))

    px_area = p.pixel_size_um ** 2
    labels, n_border = drop_border_labels(raw)
    labels, n_cancer = drop_labels_overlapping_mask(labels, cancer, p.max_cancer_overlap)
    labels, n_size = drop_by_area(labels, p.min_area_um2 / px_area, p.max_area_um2 / px_area)
    print(f"Dropped: {n_border} touching border, {n_cancer} overlapping cancer cells, {n_size} outside area range")

    labels = segmentation.relabel_sequential(labels)[0]
    if labels.max() > np.iinfo(np.uint16).max:
        raise ValueError("Too many labels for uint16")
    table = measure_cells(labels, p.pixel_size_um)

    tifffile.imwrite(out_dir / "labels.tif", labels.astype(np.uint16))
    table.to_csv(out_dir / "measurements.csv", index=False)
    save_overlay(flat, labels, cancer, inter_dir / "overlay.png")

    coverage = (labels > 0).sum() / labels.size
    print(f"Endothelial cells kept: {len(table)}; labelled fraction of field: {coverage:.2f}")
    print(table[["area_um2", "aspect_ratio"]].describe().round(2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", type=Path, default=Path("image.tif"))
    ap.add_argument("--pixel-size-um", type=float, default=0.65)
    ap.add_argument("--diameter-um", type=float, default=40.0)
    a = ap.parse_args()
    params = Params(pixel_size_um=a.pixel_size_um, expected_cell_diameter_um=a.diameter_um)
    analyse(a.image, params, Path("."), Path("intermediates"))
```

## `evaluate.py`: test on your annotated image

Save your annotation as `annotation.tif`, a label image of the same shape with one integer per endothelial cell. Then run `python evaluate.py annotation.tif`.

It applies the same border and cancer-overlap exclusions to the annotation. It then matches cells by IoU ≥ 0.5 and compares count, area and aspect ratio.

```python
"""Compare labels.tif with a manual annotation using the biological readouts (count, area, aspect ratio)."""
import argparse
import sys
from pathlib import Path

import numpy as np
import tifffile
from skimage import measure

from segment_endothelial import Params, drop_border_labels, drop_labels_overlapping_mask


def match_by_iou(gt: np.ndarray, pred: np.ndarray, threshold: float = 0.5) -> list[tuple[int, int, float]]:
    n_pred = int(pred.max()) + 1
    pairs, inter = np.unique(gt.astype(np.int64) * n_pred + pred, return_counts=True)
    area_gt, area_pred = np.bincount(gt.ravel()), np.bincount(pred.ravel(), minlength=n_pred)
    candidates = []
    for pair, count in zip(pairs, inter):
        g, q = divmod(int(pair), n_pred)
        if g == 0 or q == 0:
            continue
        iou = count / (area_gt[g] + area_pred[q] - count)
        if iou > threshold:  # IoU > 0.5 guarantees a unique match
            candidates.append((g, q, iou))
    return sorted(candidates, key=lambda t: -t[2])


def shape_table(labels: np.ndarray, pixel_um: float) -> dict[int, tuple[float, float]]:
    return {r.label: (r.area * pixel_um ** 2, r.major_axis_length / r.minor_axis_length)
            for r in measure.regionprops(labels) if r.minor_axis_length > 0}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("annotation", type=Path)
    ap.add_argument("--labels", type=Path, default=Path("labels.tif"))
    ap.add_argument("--cancer-mask", type=Path, default=Path("intermediates/cancer_mask.tif"))
    ap.add_argument("--pixel-size-um", type=float, default=0.65)
    a = ap.parse_args()

    pred = tifffile.imread(a.labels).astype(np.int64)
    gt = np.squeeze(tifffile.imread(a.annotation)).astype(np.int64)
    cancer = tifffile.imread(a.cancer_mask).astype(bool)
    if not (pred.shape == gt.shape == cancer.shape):
        raise ValueError(f"Shape mismatch: {pred.shape}, {gt.shape}, {cancer.shape}")

    # Apply the same exclusion rules to the annotation as the pipeline applied to its output.
    gt, _ = drop_border_labels(gt)
    gt, _ = drop_labels_overlapping_mask(gt, cancer, Params().max_cancer_overlap)

    matches, used_g, used_q = [], set(), set()
    for g, q, iou in match_by_iou(gt, pred):
        if g not in used_g and q not in used_q:
            matches.append((g, q, iou)); used_g.add(g); used_q.add(q)

    n_gt, n_pred, tp = len(np.unique(gt)) - 1, len(np.unique(pred)) - 1, len(matches)
    precision, recall = tp / max(n_pred, 1), tp / max(n_gt, 1)
    count_err = (n_pred - n_gt) / n_gt

    gt_shape, pred_shape = shape_table(gt, a.pixel_size_um), shape_table(pred, a.pixel_size_um)
    area_err = np.array([(pred_shape[q][0] - gt_shape[g][0]) / gt_shape[g][0] for g, q, _ in matches])
    ar_diff = np.array([abs(pred_shape[q][1] - gt_shape[g][1]) for g, q, _ in matches])
    med_area_gt = np.median([v[0] for v in gt_shape.values()])
    med_area_pred = np.median([v[0] for v in pred_shape.values()])
    med_ar_gt = np.median([v[1] for v in gt_shape.values()])
    med_ar_pred = np.median([v[1] for v in pred_shape.values()])

    print(f"annotated={n_gt} predicted={n_pred} matched(IoU>0.5)={tp}")
    print(f"precision={precision:.2f} recall={recall:.2f} count error={count_err:+.1%}")
    print(f"median IoU of matches={np.median([m[2] for m in matches]):.2f}")
    print(f"matched area error: median {np.median(area_err):+.1%}, IQR {np.percentile(area_err, 25):+.1%}..{np.percentile(area_err, 75):+.1%}")
    print(f"matched |aspect-ratio difference|: median {np.median(ar_diff):.2f}")
    print(f"population median area: annotated {med_area_gt:.0f} vs predicted {med_area_pred:.0f} um2")
    print(f"population median aspect ratio: annotated {med_ar_gt:.2f} vs predicted {med_ar_pred:.2f}")

    checks = {  # starting thresholds; set them from the effect size you need to detect
        "recall >= 0.70": recall >= 0.70,
        "precision >= 0.70": precision >= 0.70,
        "|count error| <= 15%": abs(count_err) <= 0.15,
        "|median matched area error| <= 15%": abs(np.median(area_err)) <= 0.15,
        "median |aspect ratio diff| <= 0.15": np.median(ar_diff) <= 0.15,
    }
    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
```

## What counts as failure

- **Failed:** any FAIL line above, or an overlay (`intermediates/overlay.png`) where green outlines follow nuclei or texture instead of cell borders, or where several cells are merged into one.
- **Quick sanity check on the printed summary:** `labelled fraction of field` should be high. In a confluent monolayer, cells plus cancer cells should cover most of the field. If it is below about 0.5, cells are being missed, even if the ones found look good.
- **If it fails:**
  - First change `flow_threshold`, `cellprob_threshold` and the diameter.
  - Then try a different input (for example, a local-contrast version).
  - Then fine-tune Cellpose on a few annotated crops.
  - Tune on one image and test on a different annotated image. Scoring the same image you tuned on tells you little.

## Audit: how this could be wrong while looking fine

1. **The model may segment texture, not cells.** The borders are faint, so merged or split cells would bias area and aspect ratio. Compare the median area against a coarse count of nuclei or cells in a few hand-counted regions.
2. **The cancer-cell heuristic is untested.** Missed cancer cells leak in as fake endothelial cells. Debris or strong edges may be flagged as cancer cells. Check the red outlines on both halves, since contrast differs.
3. **Selection bias.** Excluding border-touching cells favours smaller cells. Excluding cells under cancer cells removes exactly the regions where the interaction occurs. Report how many cells were dropped, and compare areas near versus far from cancer cells if that matters biologically.
4. **The seam.** If the step at mid-image is real, flat-fielding can leave a band of artefact there. Compare the measurements for cells in the left half, the right half and within about 100 px of the seam. They should agree.
5. **Annotation limits.** One image and one annotator give a noisy reference. A second annotator or a re-annotation after a week would show how much of the disagreement is the ground truth itself. Aspect ratio is sensitive to small boundary differences for cells close to round.
6. **Pixel size and scale.** I assumed 0.65 µm isotropic and a 40 µm typical cell diameter. If the diameter is off by more than about 1.5×, Cellpose results degrade.
7. **Reporting.** Say that the aspect ratio is a moment-based ellipse measure, and that the counts are complete cells in this field of view, not cells per area. Report density as cells per mm² of the non-border area.

Please send the real `image.tif` details if the seam is genuine, plus your annotation and the first `overlay.png`. Then I can help tune the parameters.

## user

The image is two fields of the same kind placed side by side (left half one field, right half the other), so the background level differs between the halves. Count them as whole cells; their outline follows the cell junctions, including the part under the cancer cells.

## assistant

Those two facts change the design in two ways:

- **Each field is now processed on its own.** The image is split at the midline, and flat-fielding, Cellpose, cancer-cell detection and border exclusion run per field. This removes the seam artefact I warned about. It also means cells touching the midline count as border cells, because they are truncated.
- **Cancer cells are no longer a reason to drop an endothelial cell.** A label that is mostly cancer cell (more than 50% inside the cancer mask) is removed as a cancer cell. The cancer-covered pixels are then handed to the nearest endothelial label, so cells keep their area under cancer cells.
  - This is a guess at where junctions run under a cancer cell. It splits the covered area between neighbouring cells by nearest distance.
  - It is the weakest step, so the evaluation now reports cells touching cancer cells separately.
  - A cell fully hidden under a cancer cell cannot be recovered and will be missed.

I have not run any of this. Below are the full updated files.

## `segment_endothelial.py`

```python
"""Segment endothelial cells in a brightfield monolayer and measure area and aspect ratio.

Input : image.tif (2D, uint16 holding 12-bit values), pixel size 0.65 um, made of
        N_FIELDS fields placed side by side (left to right), each processed independently.
Output: labels.tif, measurements.csv, intermediates/ (flat-field, raw labels, cancer mask, overlay).
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import io, measure, morphology, segmentation

MAX_12BIT = 4095


@dataclass(frozen=True)
class Params:
    pixel_size_um: float = 0.65
    n_fields: int = 2                         # fields side by side, equal width
    expected_cell_diameter_um: float = 40.0   # passed to Cellpose as diameter (converted to px)
    background_sigma_um: float = 65.0         # flat-field scale; must exceed cell size
    clip_percentiles: tuple[float, float] = (1.0, 99.0)  # contrast stretch to [0, 1]
    flow_threshold: float = 0.4               # Cellpose default
    cellprob_threshold: float = 0.0           # Cellpose default
    min_area_um2: float = 200.0               # drop fragments (checked after cancer-region fill)
    max_area_um2: float = 6000.0              # drop merged cells / background blobs
    # cancer-cell heuristic
    edge_sigma_um: float = 1.0
    edge_robust_z: float = 6.0                # edge strength in robust z-scores
    ring_close_radius_um: float = 1.5
    cancer_min_area_um2: float = 100.0
    cancer_max_area_um2: float = 1200.0
    cancer_min_solidity: float = 0.85
    cancer_label_fraction: float = 0.5        # Cellpose label with more than this inside the cancer mask = cancer cell
    fill_max_distance_um: float = 25.0        # max reach when assigning cancer-covered pixels to a neighbour


# ---------- input ----------
def read_image(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found in working directory")
    image = np.squeeze(tifffile.imread(path))
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    if image.max() > MAX_12BIT:
        raise ValueError(f"Max value {image.max()} exceeds 12-bit range ({MAX_12BIT})")
    if image.min() == image.max():
        raise ValueError("Image is constant")
    return image


def split_fields(array: np.ndarray, n_fields: int) -> list[np.ndarray]:
    """Split into n_fields equal-width fields along X (left to right)."""
    if array.shape[1] % n_fields != 0:
        raise ValueError(f"Width {array.shape[1]} is not divisible by n_fields={n_fields}")
    return np.split(array, n_fields, axis=1)


def stitch_labels(fields: list[np.ndarray]) -> np.ndarray:
    """Concatenate per-field label images along X, offsetting ids so they stay unique."""
    out, offset = [], 0
    for field in fields:
        shifted = np.where(field > 0, field + offset, 0)
        offset += int(field.max())
        out.append(shifted)
    return np.hstack(out).astype(np.int32)


# ---------- preprocessing ----------
def flat_field(image: np.ndarray, p: Params) -> np.ndarray:
    """Divide by a heavily blurred copy (removes slow illumination change), then
    stretch the p1-p99 range to [0, 1]. Output float32, same shape as input."""
    img = image.astype(np.float32)
    background = ndi.gaussian_filter(img, p.background_sigma_um / p.pixel_size_um, mode="reflect")
    if background.min() <= 0:
        raise ValueError("Non-positive background estimate; cannot flat-field")
    relative = img / background
    low, high = np.percentile(relative, p.clip_percentiles)
    if high <= low:
        raise ValueError("Degenerate contrast range after flat-fielding")
    return np.clip((relative - low) / (high - low), 0, 1).astype(np.float32)


# ---------- segmentation ----------
def load_cellpose():
    import cellpose
    from cellpose import models

    print(f"cellpose version: {getattr(cellpose, 'version', 'unknown')}")
    return models.CellposeModel(gpu=False)


def run_cellpose(model, flat: np.ndarray, p: Params) -> np.ndarray:
    masks, _, _ = model.eval(
        flat,
        diameter=p.expected_cell_diameter_um / p.pixel_size_um,
        normalize=False,  # already scaled to [0, 1] above
        flow_threshold=p.flow_threshold,
        cellprob_threshold=p.cellprob_threshold,
    )
    if masks.shape != flat.shape:
        raise RuntimeError(f"Cellpose returned shape {masks.shape}, expected {flat.shape}")
    return masks.astype(np.int32)


def detect_cancer_cells(flat: np.ndarray, p: Params) -> np.ndarray:
    """Heuristic boolean mask of round cells with a strong halo (cancer cells on top)."""
    edge = ndi.gaussian_gradient_magnitude(flat, p.edge_sigma_um / p.pixel_size_um)
    median = np.median(edge)
    mad = np.median(np.abs(edge - median))
    if mad == 0:
        raise ValueError("Edge MAD is zero; cannot normalise edge strength")
    strong = (edge - median) / (1.4826 * mad) > p.edge_robust_z
    radius = max(1, round(p.ring_close_radius_um / p.pixel_size_um))
    disk = morphology.disk(radius)
    closed = ndi.binary_dilation(strong, disk)
    filled = ndi.binary_erosion(ndi.binary_fill_holes(closed), disk)

    px_area = p.pixel_size_um ** 2
    mask = np.zeros_like(filled)
    for region in measure.regionprops(measure.label(filled)):
        area_um2 = region.area * px_area
        if (p.cancer_min_area_um2 <= area_um2 <= p.cancer_max_area_um2
                and region.solidity >= p.cancer_min_solidity):
            mask[tuple(region.coords.T)] = True
    return mask


# ---------- label editing (each step reports what it changed) ----------
def _remove(labels: np.ndarray, ids: np.ndarray) -> np.ndarray:
    out = labels.copy()
    out[np.isin(out, ids)] = 0
    return out


def drop_border_labels(labels: np.ndarray) -> tuple[np.ndarray, int]:
    edge_ids = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    edge_ids = edge_ids[edge_ids > 0]
    return _remove(labels, edge_ids), len(edge_ids)


def drop_cancer_labels(labels: np.ndarray, cancer: np.ndarray, min_fraction: float) -> tuple[np.ndarray, int]:
    """Remove labels that are mostly inside the cancer mask (i.e. the cancer cells themselves)."""
    n = labels.max() + 1
    inside = np.bincount(labels[cancer], minlength=n)
    area = np.bincount(labels.ravel(), minlength=n)
    ids = np.flatnonzero(inside / np.maximum(area, 1) > min_fraction)
    ids = ids[ids > 0]
    return _remove(labels, ids), len(ids)


def fill_under_cancer(labels: np.ndarray, cancer: np.ndarray, max_distance_px: float) -> tuple[np.ndarray, int]:
    """Give unlabelled cancer-covered pixels to the nearest endothelial label (within max_distance_px).
    Heuristic: assumes cells continue under the cancer cell and split it by nearest distance.
    Returns the new labels and the number of cancer-covered pixels left unassigned."""
    expanded = segmentation.expand_labels(labels, distance=max_distance_px)
    to_fill = cancer & (labels == 0)
    out = labels.copy()
    out[to_fill] = expanded[to_fill]
    return out, int((out[cancer] == 0).sum())


def drop_by_area(labels: np.ndarray, min_px: float, max_px: float) -> tuple[np.ndarray, int]:
    area = np.bincount(labels.ravel())
    ids = np.flatnonzero((area < min_px) | (area > max_px))
    ids = ids[(ids > 0) & (area[ids] > 0)]
    return _remove(labels, ids), len(ids)


# ---------- per-field pipeline ----------
def segment_field(image: np.ndarray, model, p: Params, name: str):
    flat = flat_field(image, p)
    raw = run_cellpose(model, flat, p)
    cancer = detect_cancer_cells(flat, p)
    px_area = p.pixel_size_um ** 2

    labels, n_cancer = drop_cancer_labels(raw, cancer, p.cancer_label_fraction)
    labels, n_unassigned = fill_under_cancer(labels, cancer, p.fill_max_distance_um / p.pixel_size_um)
    labels, n_border = drop_border_labels(labels)
    labels, n_size = drop_by_area(labels, p.min_area_um2 / px_area, p.max_area_um2 / px_area)
    labels = segmentation.relabel_sequential(labels)[0]
    print(f"[{name}] cellpose objects={len(np.unique(raw)) - 1}; removed as cancer={n_cancer}, "
          f"border={n_border}, area range={n_size}; cancer pixels left unassigned={n_unassigned}; "
          f"cells kept={labels.max()}")
    return flat, raw, cancer, labels


# ---------- measurement and outputs ----------
def measure_cells(labels: np.ndarray, pixel_size_um: float) -> pd.DataFrame:
    rows = []
    for r in measure.regionprops(labels):
        if r.minor_axis_length == 0:
            raise ValueError(f"Label {r.label} has zero minor axis; cannot compute aspect ratio")
        rows.append({
            "label": r.label,
            "area_um2": r.area * pixel_size_um ** 2,
            "aspect_ratio": r.major_axis_length / r.minor_axis_length,
        })
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio"])


def save_overlay(flat: np.ndarray, labels: np.ndarray, cancer: np.ndarray, path: Path) -> None:
    rgb = np.repeat((flat[..., None] * 255).astype(np.uint8), 3, axis=2)
    rgb[segmentation.find_boundaries(labels, mode="inner")] = (0, 255, 0)   # endothelial = green
    rgb[segmentation.find_boundaries(cancer, mode="inner")] = (255, 0, 0)   # cancer mask = red
    io.imsave(path, rgb, check_contrast=False)


def analyse(image_path: Path, p: Params, out_dir: Path, inter_dir: Path) -> None:
    inter_dir.mkdir(exist_ok=True)
    image = read_image(image_path)
    model = load_cellpose()

    results = [segment_field(f, model, p, f"field {i + 1}")
               for i, f in enumerate(split_fields(image, p.n_fields))]
    flat = np.hstack([r[0] for r in results])
    raw = stitch_labels([r[1] for r in results])
    cancer = np.hstack([r[2] for r in results])
    labels = stitch_labels([r[3] for r in results])
    if labels.max() > np.iinfo(np.uint16).max:
        raise ValueError("Too many labels for uint16")

    table = measure_cells(labels, p.pixel_size_um)
    tifffile.imwrite(out_dir / "labels.tif", labels.astype(np.uint16))
    table.to_csv(out_dir / "measurements.csv", index=False)
    tifffile.imwrite(inter_dir / "flat_field.tif", flat)
    tifffile.imwrite(inter_dir / "labels_raw.tif", raw.astype(np.uint16))
    tifffile.imwrite(inter_dir / "cancer_mask.tif", cancer.astype(np.uint8))
    save_overlay(flat, labels, cancer, inter_dir / "overlay.png")

    print(f"Total endothelial cells: {len(table)}; labelled fraction of image: {(labels > 0).mean():.2f}")
    print(table[["area_um2", "aspect_ratio"]].describe().round(2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", type=Path, default=Path("image.tif"))
    ap.add_argument("--pixel-size-um", type=float, default=0.65)
    ap.add_argument("--diameter-um", type=float, default=40.0)
    ap.add_argument("--n-fields", type=int, default=2)
    a = ap.parse_args()
    params = Params(pixel_size_um=a.pixel_size_um, expected_cell_diameter_um=a.diameter_um, n_fields=a.n_fields)
    analyse(a.image, params, Path("."), Path("intermediates"))
```

## `evaluate.py`

Run `python evaluate.py annotation.tif`. The annotation has the same shape as `image.tif`, with one integer per whole endothelial cell, including the part under cancer cells. Label ids must be unique across the two fields. The script applies the same per-field border exclusion to your annotation.

```python
"""Compare labels.tif with a manual annotation using the biological readouts (count, area, aspect ratio)."""
import argparse
import sys
from pathlib import Path

import numpy as np
import tifffile
from skimage import measure

from segment_endothelial import drop_border_labels, split_fields


def match_by_iou(gt: np.ndarray, pred: np.ndarray, threshold: float = 0.5) -> list[tuple[int, int, float]]:
    n_pred = int(pred.max()) + 1
    pairs, inter = np.unique(gt * n_pred + pred, return_counts=True)
    area_gt, area_pred = np.bincount(gt.ravel()), np.bincount(pred.ravel(), minlength=n_pred)
    found = []
    for pair, count in zip(pairs, inter):
        g, q = divmod(int(pair), n_pred)
        if g == 0 or q == 0:
            continue
        iou = count / (area_gt[g] + area_pred[q] - count)
        if iou > threshold:  # IoU > 0.5 guarantees a unique partner
            found.append((g, q, float(iou)))
    return found


def shape_table(labels: np.ndarray, pixel_um: float) -> dict[int, tuple[float, float]]:
    return {r.label: (r.area * pixel_um ** 2, r.major_axis_length / r.minor_axis_length)
            for r in measure.regionprops(labels) if r.minor_axis_length > 0}


def check_unique_ids_across_fields(gt: np.ndarray, n_fields: int) -> None:
    seen: set[int] = set()
    for i, field in enumerate(split_fields(gt, n_fields)):
        ids = set(np.unique(field[field > 0]).tolist())
        if seen & ids:
            raise ValueError(f"Annotation label ids in field {i + 1} repeat ids from earlier fields")
        seen |= ids


def summarise(name, gt_ids, matches, gt_shape, pred_shape):
    matched = [m for m in matches if m[0] in gt_ids]
    recall = len(matched) / max(len(gt_ids), 1)
    if not matched:
        print(f"{name}: annotated={len(gt_ids)} matched=0")
        return recall, float("nan"), float("nan")
    area_err = np.array([(pred_shape[q][0] - gt_shape[g][0]) / gt_shape[g][0] for g, q, _ in matched])
    ar_diff = np.array([abs(pred_shape[q][1] - gt_shape[g][1]) for g, q, _ in matched])
    print(f"{name}: annotated={len(gt_ids)} matched={len(matched)} recall={recall:.2f} | "
          f"area error median {np.median(area_err):+.1%} (IQR {np.percentile(area_err, 25):+.1%}"
          f"..{np.percentile(area_err, 75):+.1%}) | median |AR diff| {np.median(ar_diff):.2f}")
    return recall, float(np.median(area_err)), float(np.median(ar_diff))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("annotation", type=Path)
    ap.add_argument("--labels", type=Path, default=Path("labels.tif"))
    ap.add_argument("--cancer-mask", type=Path, default=Path("intermediates/cancer_mask.tif"))
    ap.add_argument("--pixel-size-um", type=float, default=0.65)
    ap.add_argument("--n-fields", type=int, default=2)
    a = ap.parse_args()

    pred = tifffile.imread(a.labels).astype(np.int64)
    gt = np.squeeze(tifffile.imread(a.annotation)).astype(np.int64)
    cancer = tifffile.imread(a.cancer_mask).astype(bool)
    if not (pred.shape == gt.shape == cancer.shape):
        raise ValueError(f"Shape mismatch: {pred.shape}, {gt.shape}, {cancer.shape}")
    check_unique_ids_across_fields(gt, a.n_fields)

    # Same exclusion as the pipeline: cells touching the border of their own field are removed.
    gt = np.hstack([drop_border_labels(f)[0] for f in split_fields(gt, a.n_fields)])

    matches, used_g, used_q = [], set(), set()
    for g, q, iou in sorted(match_by_iou(gt, pred), key=lambda t: -t[2]):
        if g not in used_g and q not in used_q:
            matches.append((g, q, iou)); used_g.add(g); used_q.add(q)

    gt_ids = set(np.unique(gt[gt > 0]).tolist())
    n_gt, n_pred, tp = len(gt_ids), len(np.unique(pred[pred > 0])), len(matches)
    if tp == 0:
        print("FAIL  no prediction matches any annotated cell (IoU > 0.5)")
        return 1
    count_err = (n_pred - n_gt) / n_gt
    print(f"annotated={n_gt} predicted={n_pred} matched={tp} precision={tp / n_pred:.2f} "
          f"count error={count_err:+.1%} median IoU={np.median([m[2] for m in matches]):.2f}")

    gt_shape, pred_shape = shape_table(gt, a.pixel_size_um), shape_table(pred, a.pixel_size_um)
    under = np.bincount(gt[cancer], minlength=gt.max() + 1) > 0   # annotated cells touching a cancer cell
    touching = {i for i in gt_ids if under[i]}
    summaries = {
        "all cells": summarise("all cells", gt_ids, matches, gt_shape, pred_shape),
        "no cancer contact": summarise("no cancer contact", gt_ids - touching, matches, gt_shape, pred_shape),
        "touching cancer": summarise("touching cancer", touching, matches, gt_shape, pred_shape),
    }
    print(f"population median area: annotated {np.median([v[0] for v in gt_shape.values()]):.0f} vs "
          f"predicted {np.median([v[0] for v in pred_shape.values()]):.0f} um2; median aspect ratio: "
          f"annotated {np.median([v[1] for v in gt_shape.values()]):.2f} vs "
          f"predicted {np.median([v[1] for v in pred_shape.values()]):.2f}")

    recall_all, area_all, ar_all = summaries["all cells"]
    recall_c, area_c, _ = summaries["touching cancer"]
    checks = {  # starting thresholds; set them from the effect size you need to detect
        "recall (all) >= 0.70": recall_all >= 0.70,
        "precision >= 0.70": tp / n_pred >= 0.70,
        "|count error| <= 15%": abs(count_err) <= 0.15,
        "|median area error, all| <= 15%": abs(area_all) <= 0.15,
        "median |aspect ratio diff| <= 0.15": ar_all <= 0.15,
        "recall (touching cancer) >= 0.60": recall_c >= 0.60 or not touching,
        "|median area error, touching cancer| <= 20%": (abs(area_c) <= 0.20) or not touching,
    }
    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
```

## How to read the result

- **The analysis failed if** any line says FAIL, or the overlay shows green outlines following nuclei or texture, or merged or split cells. The same applies if the labelled fraction is below roughly 0.5 (cells are being missed), or if the red cancer outlines miss cancer cells or flag debris.
- **Compare the "no cancer contact" and "touching cancer" lines.**
  - If only the touching group fails, the cell finding is fine and the under-cancer fill rule is the problem. The fix is a better rule for assigning covered area, not retuning Cellpose.
  - If both fail, the model does not suit these images. Tune on one annotated image and test on a different one, or fine-tune Cellpose on a few annotated crops.

## Remaining audit points

1. **Fill under cancer cells is an assumption.** Cancer cells often sit on junctions, and nearest-distance assignment will bias the area of cells next to them. Quantify this on the touching group. If cancer coverage differs between conditions, the bias differs too, so a comparison between conditions could be wrong.
2. **Cells fully hidden under a cancer cell are undetectable.** That undercounts cells in the most covered regions. Count them by hand in a few areas to estimate the miss rate.
3. **An imperfect cancer mask moves area.** If it is too small, cancer cells stay as endothelial labels or leave gaps. If it is too large, it takes area from real cells. Check it on both fields, since the left field looks phase-like and the right looks flat.
4. **Border exclusion favours small cells**, and per-field processing makes this cut apply at the midline too. Report density per area of the non-border region, or just say counts refer to complete cells.
5. **Do the two fields agree?** They are the same kind of sample, so their medians for area and aspect ratio should be similar. If they differ a lot, suspect segmentation differences between the two contrast styles before suspecting biology.
6. **One annotated image from one annotator** limits what you can conclude. Annotating a second image, or re-annotating after a few days, shows how much of the disagreement is just annotation variability.

Send me the first `overlay.png` and the evaluation output, and I can help tune the parameters from there.
