# code_box1_cancer_r3

## user

You are an AI assistant chatting with a user. You can search the web (WebSearch and WebFetch; load them with ToolSearch if they are not listed). The user attached a file, which you can view: /home/user/sessions_v2/v037/image.png. You cannot run code; the user will run your script. Reply to the user as you normally would.

I want to segment and count the cancer cells and measure their shape (area and aspect ratio) from brightfield images of cancer cells sitting on top of a confluent endothelial monolayer. Help me write the analysis as a Python script.
My images are 2D, with axes Y, X, channels 1 (brightfield), data type uint16 (12-bit values), pixel/voxel size 0.65 µm, and objects of interest approximately 15–25 µm in size. I use Python 3.13 on a laptop CPU (no GPU). The output I need is a label image with one integer per cancer cell (0 = background) and a table with the area (µm²) and aspect ratio of each cancer cell. I can provide a manual annotation of this image (a label image).
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
 "file_path": "/home/user/sessions_v2/v037/image.png"
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
 "prompt": "Cellpose latest version: how to instantiate CellposeModel (model_type, pretrained_model, gpu), the eval() signature and parameters (diameter, flow_threshold, cellprob_threshold, niter, normalize, channels deprecated?, min_size), return values, and which models exist (cpsam, cyto3). Note CPU guidance."
}
```

## assistant (tool call: WebFetch)

```json
{
 "url": "https://cellpose.readthedocs.io/en/latest/settings.html",
 "prompt": "Summarize settings: diameter behaviour in Cellpose 4 / cpsam, normalization defaults, flow_threshold, cellprob_threshold, channels handling."
}
```

## tool result

```
**Diameter (Cellpose 4 / Cellpose-SAM):** Specifying diameter is optional because the model is largely size-invariant. It was trained on ROI diameters from 7.5 to 120 pixels, with a mean of 30. If cells are very large, setting a diameter (e.g., 90) downsamples the image, which speeds up the run.

**Normalization defaults:** The page doesn't cover normalization, so I can't summarize defaults from it.

**flow_threshold:** Default is 0.4. It sets the maximum allowed error between recomputed flow gradients for each predicted mask and the flows the network predicted. Increase it if you get fewer ROIs than expected. Decrease it if you get too many ill-shaped ROIs.

**cellprob_threshold:** Default is 0.0. Pixels whose cell-probability output exceeds this value are used to run the dynamics and define ROIs. The outputs typically range from about -6 to +6. Decrease it if you get too few ROIs. Increase it if you get too many, especially from dim areas.

**Channels:** Channels are no longer an input. The model uses the first 3 channels and truncates the rest. For cellular images, it was trained on cytoplasm and nuclear channels in any order, with the unused channel set to zero. For a third fluorescent channel, you can omit it, merge it into the cytoplasm channel, or train a new model.
```

## tool result

```
## Instantiating CellposeModel

```python
from cellpose.models import CellposeModel
model = CellposeModel(gpu=False, pretrained_model='cpsam_v2')
```

- **`gpu`** defaults to `False`.
- **`pretrained_model`** defaults to `'cpsam_v2'`. The page also mentions `"cpdino"` and accepts a path to a custom model.
- **`model_type`** is in the signature (default `None`), but the page doesn't list its valid values.
- **`device`**, **`diam_mean`**, **`nchan`**, and **`use_bfloat16`** are also accepted.
- The page's separate `__init__` entry shows different defaults (`pretrained_model=False`, `diam_mean=30.`), so the class-level signature is the more reliable reference.

## eval() parameters

Key parameters and defaults:

- **`diameter`** (default `None`): cell diameters used to rescale images to 30 px. `rescale` only applies when `diameter` is `None`.
- **`flow_threshold`** (`0.4`): flow error threshold. Not used for 3D.
- **`cellprob_threshold`** (`0.0`): pixels above this are kept for masks.
- **`niter`** (`None`): dynamics iterations. If `None`, this scales with diameter.
- **`normalize`** (`True`): normalizes each channel to the 1st–99th percentile. Also accepts a dict of options.
- **`min_size`** (`15`): ROIs smaller than this (in pixels) are discarded.
- **`channels`** (`None`): listed in the signature alongside `channel_axis`. The page doesn't mark it as deprecated.
- **`bsize`**: 256 for cpsam (fixed) and 384 suggested for cpdino.

The page also contains an older `eval` signature with different defaults (for example, `bsize=256`, `invert`, `interp`). Check which one matches your installed version.

## Return values

`eval()` returns `(masks, flows, styles)`:

- **`masks`**: labeled array where 0 is background and 1, 2, … are cell labels.
- **`flows`**: per-image lists where `[0]` is the XY flow as an HSV image, `[1]` is the XY flow, `[2]` is cell probability, and `[3]` is the final pixel locations after Euler integration.
- **`styles`**: arrays of zeros, kept for compatibility with Cellpose 3.

## Available models

The page names **`cpsam_v2`** (the default) and **`cpdino`**. It also references a `CPSAM` class. **`cyto3` is not mentioned anywhere in this content**, so I can't confirm it from this page.

## CPU guidance

The page gives only limited CPU guidance. `gpu=False` is the default, and `assign_device()` can select CPU, GPU, or mps. The page doesn't include specific CPU setup or performance advice.

[WebFetch note: this page's text is 100080 characters long and the answer above covers only characters 0 to 100000; the final 80 were not read — to read on, call WebFetch again with the same url and offset: 100000.]
```

## assistant

I can't run code here, so the scripts below are untested. I looked at your image and checked the current Cellpose docs, and my questions come before the code.

## What I saw in the image

- **Cells:** The cancer cells are round and refractile, with a bright or dark rim. At 0.65 µm/px a 20 µm cell is about 31 px across. That is close to Cellpose's 30 px training mean, so no resizing is needed.
- **Contrast change:** The left half of the image is dark with dark-rimmed cells. The right half is bright with white-haloed cells. It looks like two fields stitched together, or two different illumination or contrast settings. A single global intensity normalisation would treat the halves very differently. I therefore normalise locally and report the evaluation per half.
- **Image type:** The halo look suggests phase contrast or defocused brightfield. This matters for model choice, so I've asked about it below.
- **Distractors:** Black debris clumps, and the faint, flat endothelial cells that carpet the field. These are the main false-positive risks.

## Questions that could change the analysis

1. **Left and right halves:** Is the contrast jump real in `image.tif`, for example a stitched mosaic? Or is it an artefact of the PNG you sent? Please send the raw tif, or a crop of the seam.
2. **Cell clusters:** In touching clusters, should each cell be counted separately? That is my assumption. An undivided doublet gives an aspect ratio of about 2 and a false area.
3. **Cells cut by the image edge:** I exclude them by default, because a cut cell has a wrong area and aspect ratio. Say if you want them kept.
4. **Which cells are cancer cells:** I assume they are the round, refractile cells on top, and that the flat endothelial cells are not wanted. Is that right?
5. **Annotation:** Please send your manual label image. Does it follow the same rules (clusters split, edge cells included or not)?

## Method choice

I use **Cellpose** (the Cellpose-SAM generation, which is the default in v4). Reasons:

- It is maintained and runs on CPU. A 1024² image should take on the order of a minute.
- It is trained on diverse images, including non-fluorescent ones, and it is size-tolerant. The docs say it was trained on diameters of 7.5–120 px.
- Cellpose 4 has no `channels` argument. It takes the first 3 channels, so a 2D grayscale array is passed as is.

The risks:

- It was not specifically trained on your type of image, so it needs checking against your annotation.
- If it fails, fine-tuning on your annotation is the next step. A classical halo-ring approach is a fallback.

The docs list the default pretrained model as `cpsam_v2`. I don't hard-code a name, so the installed version's default is used, and the script logs the Cellpose version.

## Script 1: `analyse_cells.py`

```python
"""Segment cancer cells in a 2D brightfield image and measure area and aspect ratio.

Reads  image.tif (Y, X; uint16, 12-bit) from the working directory.
Writes labels.tif, measurements.csv, plus intermediates:
  normalised.tif, overlay.png, rejected.csv

Pipeline (each step is a separate function):
  1. load + validate
  2. local contrast normalisation (sigma in px, see Config)
  3. Cellpose segmentation (no resizing; diameter=None)
  4. filtering: border, area, solidity (each rejection is logged)
  5. measurement in physical units (um)
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import io as skio
from skimage.filters import gaussian
from skimage.measure import regionprops_table
from skimage.segmentation import clear_border, find_boundaries, relabel_sequential


@dataclass(frozen=True)
class Config:
    input_path: Path = Path("image.tif")
    pixel_size_um: float = 0.65
    max_value: int = 4095                 # 12-bit data stored in uint16
    norm_sigma_px: float = 64.0           # ~42 um; scale of local mean/std estimate
    cellpose_diameter_px: float | None = None  # None = no rescaling (model is size-tolerant)
    flow_threshold: float = 0.4           # Cellpose default
    cellprob_threshold: float = 0.0       # Cellpose default; lower -> more/larger cells
    min_area_um2: float = 80.0            # ~10 um diameter; removes debris. TUNE on annotation
    max_area_um2: float = 900.0           # ~34 um diameter; removes merged clusters/large flat cells
    min_solidity: float = 0.85            # irregular debris clumps have low solidity
    exclude_border: bool = True           # cut-off cells give wrong area/aspect ratio


# ---------- 1. load ----------
def load_image(path: Path, max_value: int) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path.resolve()} not found")
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise TypeError(f"Expected uint16, got {img.dtype}")
    if img.max() > max_value:
        raise ValueError(f"Max value {img.max()} exceeds {max_value}: not 12-bit data as stated")
    return img


# ---------- 2. normalise ----------
def normalise_local(img: np.ndarray, sigma_px: float) -> np.ndarray:
    """(img - local mean) / local std, float32. Equalises the dark and bright halves.

    Only used as model input; all measurements come from the label image, so
    pixel geometry is unchanged (no resampling).
    """
    f = img.astype(np.float32)
    mean = gaussian(f, sigma=sigma_px, preserve_range=True)
    var = gaussian((f - mean) ** 2, sigma=sigma_px, preserve_range=True)
    return ((f - mean) / np.sqrt(var + 1e-6)).astype(np.float32)


# ---------- 3. segment ----------
def segment_cellpose(norm: np.ndarray, cfg: Config) -> np.ndarray:
    import cellpose
    from cellpose.models import CellposeModel

    print(f"cellpose {getattr(cellpose, '__version__', 'unknown')}, CPU")
    model = CellposeModel(gpu=False)  # installed version's default pretrained model
    masks, _flows, _styles = model.eval(
        norm,
        diameter=cfg.cellpose_diameter_px,
        flow_threshold=cfg.flow_threshold,
        cellprob_threshold=cfg.cellprob_threshold,
        normalize=True,  # Cellpose default: 1-99 percentile, applied to the locally normalised image
    )
    return masks.astype(np.int32)


# ---------- 4. filter ----------
def _props(labels: np.ndarray, pixel_size_um: float) -> pd.DataFrame:
    t = pd.DataFrame(regionprops_table(
        labels, properties=("label", "area", "solidity", "major_axis_length", "minor_axis_length")))
    if (t["minor_axis_length"] <= 0).any():
        raise ValueError("Degenerate object (zero minor axis); check segmentation")
    t["area_um2"] = t["area"] * pixel_size_um**2
    t["aspect_ratio"] = t["major_axis_length"] / t["minor_axis_length"]
    return t


def filter_objects(labels: np.ndarray, cfg: Config) -> tuple[np.ndarray, pd.DataFrame]:
    """Return (filtered, sequentially relabelled labels) and a table of rejected objects with reasons."""
    rejected: list[dict] = []
    keep = labels.copy()

    if cfg.exclude_border:
        no_border = clear_border(keep)
        for lab in set(np.unique(keep)) - set(np.unique(no_border)) - {0}:
            rejected.append({"label": int(lab), "reason": "touches_border"})
        keep = no_border

    t = _props(keep, cfg.pixel_size_um) if keep.max() > 0 else pd.DataFrame()
    for _, r in t.iterrows():
        reason = None
        if r.area_um2 < cfg.min_area_um2:
            reason = "too_small"
        elif r.area_um2 > cfg.max_area_um2:
            reason = "too_large"
        elif r.solidity < cfg.min_solidity:
            reason = "low_solidity"
        if reason:
            rejected.append({"label": int(r.label), "reason": reason,
                             "area_um2": r.area_um2, "solidity": r.solidity})
            keep[keep == r.label] = 0

    keep, _, _ = relabel_sequential(keep)
    return keep.astype(np.uint16), pd.DataFrame(rejected, columns=["label", "reason", "area_um2", "solidity"])


# ---------- 5. measure ----------
def measure(labels: np.ndarray, pixel_size_um: float) -> pd.DataFrame:
    """Area (um^2) and aspect ratio = major/minor axis of the moment-equivalent ellipse."""
    if labels.max() == 0:
        return pd.DataFrame(columns=["label", "area_um2", "aspect_ratio"])
    return _props(labels, pixel_size_um)[["label", "area_um2", "aspect_ratio"]]


# ---------- outputs ----------
def save_overlay(img: np.ndarray, labels: np.ndarray, path: Path) -> None:
    lo, hi = np.percentile(img, (1, 99))
    gray = np.clip((img.astype(np.float32) - lo) / (hi - lo), 0, 1)
    rgb = np.stack([gray] * 3, axis=-1)
    rgb[find_boundaries(labels, mode="outer")] = (1, 0, 0)
    skio.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def main() -> None:
    cfg = Config()
    img = load_image(cfg.input_path, cfg.max_value)
    norm = normalise_local(img, cfg.norm_sigma_px)
    tifffile.imwrite("normalised.tif", norm)

    raw = segment_cellpose(norm, cfg)
    print(f"Cellpose objects before filtering: {raw.max()}")
    labels, rejected = filter_objects(raw, cfg)
    table = measure(labels, cfg.pixel_size_um)

    tifffile.imwrite("labels.tif", labels, resolution=(1 / cfg.pixel_size_um,) * 2,
                     metadata={"unit": "um"})
    table.to_csv("measurements.csv", index=False)
    rejected.to_csv("rejected.csv", index=False)
    save_overlay(img, labels, Path("overlay.png"))
    print(f"Kept {len(table)} cells; rejected {len(rejected)}:")
    print(rejected["reason"].value_counts().to_string() if len(rejected) else "  none")


if __name__ == "__main__":
    sys.exit(main())
```

Install with `pip install cellpose scikit-image tifffile pandas scipy`. Check the Cellpose install on Python 3.13, because PyTorch wheel availability can lag behind new Python versions.

## Script 2: `evaluate.py` (your annotated example)

```python
"""Compare labels.tif with a manual annotation.  Usage: python evaluate.py annotation.tif"""
import sys

import numpy as np
import pandas as pd
import tifffile

from analyse_cells import Config, measure


def iou_matches(gt: np.ndarray, pred: np.ndarray, thr: float) -> list[tuple[int, int]]:
    """Pairs (gt_label, pred_label) with IoU > thr (>=0.5 guarantees one-to-one)."""
    if thr < 0.5:
        raise ValueError("thr must be >= 0.5 for unique matching")
    both = (gt > 0) & (pred > 0)
    pairs, inter = np.unique(np.stack([gt[both], pred[both]]), axis=1, return_counts=True)
    gt_area = np.bincount(gt.ravel())
    pr_area = np.bincount(pred.ravel())
    out = []
    for (g, p), i in zip(pairs.T, inter):
        if i / (gt_area[g] + pr_area[p] - i) > thr:
            out.append((int(g), int(p)))
    return out


def evaluate(gt: np.ndarray, pred: np.ndarray, pixel_um: float, name: str) -> dict:
    n_gt, n_pred = len(np.unique(gt)) - 1, len(np.unique(pred)) - 1
    res = {"region": name, "n_gt": n_gt, "n_pred": n_pred,
           "count_error_%": 100 * (n_pred - n_gt) / max(n_gt, 1)}
    for thr in (0.5, 0.75):
        tp = len(iou_matches(gt, pred, thr))
        res[f"precision@{thr}"] = tp / max(n_pred, 1)
        res[f"recall@{thr}"] = tp / max(n_gt, 1)
        res[f"F1@{thr}"] = 2 * tp / max(n_gt + n_pred, 1)
    m = iou_matches(gt, pred, 0.5)
    if m:
        tg, tp_ = measure(gt, pixel_um).set_index("label"), measure(pred, pixel_um).set_index("label")
        g, p = zip(*m)
        a_g, a_p = tg.loc[list(g), "area_um2"].values, tp_.loc[list(p), "area_um2"].values
        r_g, r_p = tg.loc[list(g), "aspect_ratio"].values, tp_.loc[list(p), "aspect_ratio"].values
        res["median_abs_area_err_%"] = float(np.median(np.abs(a_p - a_g) / a_g) * 100)
        res["median_area_bias_%"] = float(np.median((a_p - a_g) / a_g) * 100)
        res["median_abs_AR_err"] = float(np.median(np.abs(r_p - r_g)))
    return res


def main(gt_path: str) -> None:
    cfg = Config()
    gt, pred = tifffile.imread(gt_path), tifffile.imread("labels.tif")
    if gt.shape != pred.shape:
        raise ValueError(f"Shape mismatch: annotation {gt.shape} vs labels {pred.shape}")
    w = gt.shape[1] // 2
    rows = [evaluate(gt, pred, cfg.pixel_size_um, "whole"),
            evaluate(gt[:, :w], pred[:, :w], cfg.pixel_size_um, "left half"),
            evaluate(gt[:, w:], pred[:, w:], cfg.pixel_size_um, "right half")]
    df = pd.DataFrame(rows).set_index("region").round(3)
    print(df.T.to_string())
    df.to_csv("evaluation.csv")


if __name__ == "__main__":
    main(sys.argv[1])
```

Half-image evaluation cuts objects at the seam, so the per-half numbers are approximate. Your annotation should follow the same border rule as the script. If it includes edge cells, set `exclude_border=False` or remove those cells from the annotation.

## What counts as failure

These thresholds are my suggestions, not standards. Adjust them to the size of effect you need to detect.

- **Detection:** F1@0.5 below 0.8 on the whole image, or on either half, means failure. A large gap between the halves means the normalisation or model does not handle both contrasts.
- **Count:** An absolute count error above 10%, or a consistent sign. Many extra objects suggest endothelial cells or debris were segmented. Many missing objects suggest the filters are too strict or clusters were merged.
- **Area:** Median absolute error above 15%, or median bias beyond ±10%. A consistent bias means the contour sits on the wrong side of the halo ring.
- **Aspect ratio:** Median absolute error above 0.1. Also check that your annotation's aspect-ratio distribution (about 1.0–1.2 for round cells) matches the prediction.
- **Visual check:** Open `overlay.png` and `rejected.csv`. Metrics can pass while one class of cell, such as dividing cells or the edges of clusters, is systematically wrong.

## Audit: how this could be wrong while looking fine

1. **Halo outline bias.** The outline may sit on the dark rim, the bright halo or the inside of the cell. That is a systematic area offset. At 20 µm, a 1 px (0.65 µm) shift changes area by about 13%. Compare against your annotation, and decide which boundary is "the cell".
2. **Cluster splitting.** Under-splitting inflates area and aspect ratio. Over-splitting deflates area and inflates the count. Evaluate clusters separately, for example by listing annotated cells touching another cell.
3. **Endothelial cells or debris counted as cancer cells.** The size and solidity filters are blunt. Check `rejected.csv` and the overlay, and tune `min_area_um2` and `min_solidity` on the annotation. Then validate on a different image, not the one you tuned on.
4. **Cancer cells on top of endothelial cells.** Cells in the endothelial layer's focal plane may be out of focus or partly hidden. Check for missed cells.
5. **Local normalisation side effects.** It amplifies noise in flat regions and shifts values near dense clusters. Compare against a run with plain global normalisation by setting a very large `norm_sigma_px`.
6. **Overfitting to one image.** One annotated image shows whether the pipeline can work, not that it generalises. Validate on other fields, days and densities. The biological conclusion should only rest on images that were not used for tuning.
7. **Excluded border cells.** This biases counts toward fewer cells, so compare density per image only when images have equal area. It can also bias shape statistics if elongated cells are more likely to touch the border.
8. **Aspect ratio of small objects.** At about 30 px diameter, one pixel of contour error moves the aspect ratio of a round cell by a few percent. Do not interpret small differences in aspect ratio between conditions without an estimate of that noise. An easy check is to annotate the same cells twice, or have two annotators do it.

## Next steps

1. Run `analyse_cells.py`, then `python evaluate.py your_annotation.tif`.
2. Send me `evaluation.csv`, `overlay.png` and `rejected.csv`, plus answers to the questions above.
3. If detection is poor, I can add Cellpose fine-tuning on your annotation, or a classical halo-based method for comparison.

Sources:
- https://cellpose.readthedocs.io/en/latest/api.html
- https://cellpose.readthedocs.io/en/latest/settings.html

## user

The image is two fields of the same kind placed side by side (left half one field, right half the other), so the background level differs between the halves. They are rounded and sit on top of the endothelial monolayer; touching cells should be counted individually. Cells cut by the image border can be left out of the area and shape statistics. I don't know.

## assistant

Thanks. Your answers change the script in four ways. I couldn't tell what your last "I don't know" refers to. It may mean the image type (phase contrast or true brightfield), your annotation conventions, or something else. Nothing below depends on it, but please say which it was. If it is the annotation, I'll assume it follows the rules in this message.

## What changes

- **Each field is processed separately.** The image is split at the middle column, and normalisation, segmentation and filtering run on each field. This avoids blending the two background levels across the seam and avoids objects spanning both fields. It requires an even width, which the script checks.
- **Border cells stay in the label image and the count, but are flagged.** `measurements.csv` gets a `touches_border` column, and the shape statistics should use only rows where it is `False`. A cell touching the seam counts as touching the border of its own field. Because the border is judged per field, `touches_border` is set for any object touching an edge of its field, including the seam.
- **The minimum-area filter is lower for border objects.** A cell cut by the edge looks small, so I use 20 µm² for them and 80 µm² for interior cells. The 20 µm² value is a guess, so tune it. Border objects are the least reliable part of the count, so check them in the overlay.
- **Touching cells are expected to be split.** I kept the 900 µm² maximum area (about 34 µm equivalent diameter), which rejects merged clumps. Rejected objects are listed in `rejected.csv`. If many real cells end up there, those clumps were under-split, and the count is wrong for them.
- **The output has extra columns.** `measurements.csv` now has `field` and `touches_border` in addition to the three columns you asked for.

## Revised `analyse_cells.py`

```python
"""Segment cancer cells in a 2D brightfield image made of two side-by-side fields,
and measure area and aspect ratio.

Reads  image.tif (Y, X; uint16, 12-bit) from the working directory.
Writes labels.tif, measurements.csv, plus intermediates:
  normalised.tif, overlay.png, rejected.csv

Pipeline:
  1. load + validate
  2. split into fields (equal-width, side by side); everything below runs per field
  3. local contrast normalisation (model input only)
  4. Cellpose segmentation (no resizing)
  5. filtering: area, solidity, max area (each rejection logged)
  6. measurement in um; objects touching a field edge are flagged, not removed
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from skimage import io as skio
from skimage.filters import gaussian
from skimage.measure import regionprops_table
from skimage.segmentation import find_boundaries, relabel_sequential


@dataclass(frozen=True)
class Config:
    input_path: Path = Path("image.tif")
    pixel_size_um: float = 0.65
    max_value: int = 4095                 # 12-bit data stored in uint16
    n_fields: int = 2                     # equal-width fields side by side
    norm_sigma_px: float = 64.0           # ~42 um; scale of local mean/std estimate
    cellpose_diameter_px: float | None = None  # None = no rescaling (model is size-tolerant)
    flow_threshold: float = 0.4           # Cellpose default
    cellprob_threshold: float = 0.0       # Cellpose default; lower -> more/larger cells
    min_area_um2: float = 80.0            # interior cells, ~10 um diameter. TUNE on annotation
    min_area_border_um2: float = 20.0     # cut cells are smaller; only removes slivers. TUNE
    max_area_um2: float = 900.0           # ~34 um diameter; removes merged clumps
    min_solidity: float = 0.85            # irregular debris clumps have low solidity


# ---------- 1. load ----------
def load_image(path: Path, max_value: int) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path.resolve()} not found")
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise TypeError(f"Expected uint16, got {img.dtype}")
    if img.max() > max_value:
        raise ValueError(f"Max value {img.max()} exceeds {max_value}: not 12-bit data as stated")
    return img


# ---------- 2. split ----------
def split_fields(img: np.ndarray, n_fields: int) -> list[np.ndarray]:
    if img.shape[1] % n_fields != 0:
        raise ValueError(f"Width {img.shape[1]} not divisible into {n_fields} equal fields")
    return np.split(img, n_fields, axis=1)


# ---------- 3. normalise ----------
def normalise_local(img: np.ndarray, sigma_px: float) -> np.ndarray:
    """(img - local mean) / local std, float32. Model input only; no resampling."""
    f = img.astype(np.float32)
    mean = gaussian(f, sigma=sigma_px, preserve_range=True)
    var = gaussian((f - mean) ** 2, sigma=sigma_px, preserve_range=True)
    return ((f - mean) / np.sqrt(var + 1e-6)).astype(np.float32)


# ---------- 4. segment ----------
def load_model():
    import cellpose
    from cellpose.models import CellposeModel

    print(f"cellpose {getattr(cellpose, '__version__', 'unknown')}, CPU")
    return CellposeModel(gpu=False)  # installed version's default pretrained model


def segment_cellpose(model, norm: np.ndarray, cfg: Config) -> np.ndarray:
    masks, _flows, _styles = model.eval(
        norm,
        diameter=cfg.cellpose_diameter_px,
        flow_threshold=cfg.flow_threshold,
        cellprob_threshold=cfg.cellprob_threshold,
        normalize=True,  # Cellpose default 1-99 percentile, on the locally normalised field
    )
    return masks.astype(np.int32)


# ---------- 5. filter ----------
def edge_labels(labels: np.ndarray) -> set[int]:
    """Labels with at least one pixel on the image edge."""
    edge = np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    return {int(v) for v in np.unique(edge)} - {0}


def _props(labels: np.ndarray, pixel_size_um: float) -> pd.DataFrame:
    t = pd.DataFrame(regionprops_table(
        labels, properties=("label", "area", "solidity", "major_axis_length", "minor_axis_length")))
    if (t["minor_axis_length"] <= 0).any():
        raise ValueError("Degenerate object (zero minor axis); check segmentation")
    t["area_um2"] = t["area"] * pixel_size_um**2
    t["aspect_ratio"] = t["major_axis_length"] / t["minor_axis_length"]
    return t


def filter_objects(labels: np.ndarray, cfg: Config) -> tuple[np.ndarray, pd.DataFrame]:
    """Remove debris/merged objects; returns relabelled uint16 labels and rejection log."""
    if labels.max() == 0:
        return labels.astype(np.uint16), pd.DataFrame(columns=["label", "reason", "area_um2", "solidity"])
    border = edge_labels(labels)
    keep = labels.copy()
    rejected: list[dict] = []
    for _, r in _props(labels, cfg.pixel_size_um).iterrows():
        lab = int(r.label)
        min_area = cfg.min_area_border_um2 if lab in border else cfg.min_area_um2
        if r.area_um2 < min_area:
            reason = "too_small"
        elif r.area_um2 > cfg.max_area_um2:
            reason = "too_large"
        elif r.solidity < cfg.min_solidity:
            reason = "low_solidity"
        else:
            continue
        rejected.append({"label": lab, "reason": reason, "area_um2": r.area_um2, "solidity": r.solidity})
        keep[keep == lab] = 0
    keep, _, _ = relabel_sequential(keep)
    return keep.astype(np.uint16), pd.DataFrame(rejected, columns=["label", "reason", "area_um2", "solidity"])


# ---------- 6. measure ----------
def measure(labels: np.ndarray, pixel_size_um: float) -> pd.DataFrame:
    """Area (um^2), aspect ratio = major/minor axis of the moment-equivalent ellipse,
    and touches_border (touches an edge of the array passed in)."""
    cols = ["label", "area_um2", "aspect_ratio", "touches_border"]
    if labels.max() == 0:
        return pd.DataFrame(columns=cols)
    t = _props(labels, pixel_size_um)
    border = edge_labels(labels)
    t["touches_border"] = t["label"].isin(border)
    return t[cols]


# ---------- outputs ----------
def save_overlay(img: np.ndarray, labels: np.ndarray, border_labels: set[int], path: Path) -> None:
    """Red outlines = interior cells (used for statistics); yellow = cells touching a field edge."""
    lo, hi = np.percentile(img, (1, 99))  # display only
    gray = np.clip((img.astype(np.float32) - lo) / (hi - lo), 0, 1)
    rgb = np.stack([gray] * 3, axis=-1)
    is_border = np.isin(labels, list(border_labels))
    outline = find_boundaries(labels, mode="inner")
    rgb[outline & ~is_border] = (1, 0, 0)
    rgb[outline & is_border] = (1, 1, 0)
    skio.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def process_field(model, field: np.ndarray, cfg: Config) -> tuple[np.ndarray, pd.DataFrame, np.ndarray]:
    norm = normalise_local(field, cfg.norm_sigma_px)
    raw = segment_cellpose(model, norm, cfg)
    labels, rejected = filter_objects(raw, cfg)
    return labels, rejected, norm


def main() -> None:
    cfg = Config()
    img = load_image(cfg.input_path, cfg.max_value)
    model = load_model()

    label_fields, norm_fields, tables, rejects, border_all = [], [], [], [], set()
    offset = 0
    for i, field in enumerate(split_fields(img, cfg.n_fields)):
        labels, rejected, norm = process_field(model, field, cfg)
        table = measure(labels, cfg.pixel_size_um)
        table.insert(1, "field", i)
        rejected.insert(1, "field", i)
        # offset labels so they are unique across fields
        labels_off = np.where(labels > 0, labels.astype(np.int64) + offset, 0)
        table["label"] += offset
        border_all |= {int(l) + offset for l in table.loc[table.touches_border, "label"] - offset}
        offset += int(labels.max())
        label_fields.append(labels_off); norm_fields.append(norm)
        tables.append(table); rejects.append(rejected)
        print(f"field {i}: kept {len(table)} (interior {(~table.touches_border).sum()}), rejected {len(rejected)}")

    if offset > np.iinfo(np.uint16).max:
        raise ValueError("Too many objects for uint16 label image")
    labels_all = np.concatenate(label_fields, axis=1).astype(np.uint16)
    table_all = pd.concat(tables, ignore_index=True)
    rejected_all = pd.concat(rejects, ignore_index=True)

    tifffile.imwrite("normalised.tif", np.concatenate(norm_fields, axis=1))
    tifffile.imwrite("labels.tif", labels_all, resolution=(1 / cfg.pixel_size_um,) * 2,
                     metadata={"unit": "um"})
    table_all.to_csv("measurements.csv", index=False)
    rejected_all.to_csv("rejected.csv", index=False)
    save_overlay(img, labels_all, border_all, Path("overlay.png"))

    interior = table_all[~table_all.touches_border]
    print(f"Total cells counted (incl. border-touching): {len(table_all)}")
    print(f"Interior cells used for shape statistics: {len(interior)}; "
          f"median area {interior.area_um2.median():.0f} um2, median aspect ratio {interior.aspect_ratio.median():.2f}")
    if len(rejected_all):
        print(rejected_all["reason"].value_counts().to_string())


if __name__ == "__main__":
    sys.exit(main())
```

## Changes to `evaluate.py`

The evaluation now runs per field, so the border logic matches the analysis. Detection and counts use all cells. Area and aspect-ratio errors use only matched cells that don't touch the field edge in either label image.

Replace the measurement block in `evaluate()` (everything after `m = iou_matches(gt, pred, 0.5)`) with:

```python
    m = iou_matches(gt, pred, 0.5)
    tg = measure(gt, pixel_um).set_index("label")
    tp_ = measure(pred, pixel_um).set_index("label")
    m = [(g, p) for g, p in m if not tg.loc[g, "touches_border"] and not tp_.loc[p, "touches_border"]]
    res["n_matched_interior"] = len(m)
    if m:
        g, p = map(list, zip(*m))
        a_g, a_p = tg.loc[g, "area_um2"].values, tp_.loc[p, "area_um2"].values
        r_g, r_p = tg.loc[g, "aspect_ratio"].values, tp_.loc[p, "aspect_ratio"].values
        res["median_abs_area_err_%"] = float(np.median(np.abs(a_p - a_g) / a_g) * 100)
        res["median_area_bias_%"] = float(np.median((a_p - a_g) / a_g) * 100)
        res["median_abs_AR_err"] = float(np.median(np.abs(r_p - r_g)))
    return res
```

Replace the `rows = [...]` list in `main()` with one row per field. The whole-image row is dropped, because the seam is not a real edge and would distort the border flags.

```python
    rows = [evaluate(g, p, cfg.pixel_size_um, f"field {i}")
            for i, (g, p) in enumerate(zip(np.split(gt, cfg.n_fields, axis=1),
                                           np.split(pred, cfg.n_fields, axis=1)))]
```

Your annotation needs one label per cell, with touching cells separated and border cells included. Cells at the border can then be excluded from the shape statistics automatically.

## Pass and fail criteria

These are my suggested thresholds, not standards. Adjust them to the effect size you need.

| Measure | Failure |
|---|---|
| F1@0.5, either field | below 0.8 |
| Count error | beyond ±10%, or the same sign in both fields |
| Median area error (interior cells) | above 15%, or a bias beyond ±10% |
| Median aspect-ratio error | above 0.1 |
| Fields differ strongly | one field much worse than the other |

The last row means the per-field normalisation did not fix the contrast difference.

Look at `overlay.png` for the other failures. Red outlines are interior cells and yellow outlines are border cells. Check these in particular:

- Clusters merged into one object.
- Flat endothelial cells outlined as cancer cells.
- Real cells listed in `rejected.csv`.

## Remaining risks

- **Clusters.** Splitting touching cells is the hardest part. Evaluate it specifically by listing the annotated cells that touch another cell and checking their recall separately. If it is poor, fine-tuning Cellpose on your annotation is the next step.
- **Border-cell counts.** These are the least reliable part of the count. Compare total counts with and without the border-touching cells.
- **Two fields, one annotation.** Both fields come from one image, so they are not independent test data. Tune on one field and test on the other. That is a better check than tuning and testing on both. Validate on at least one other image before drawing biological conclusions.

Please run both scripts and send me `evaluation.csv`, `overlay.png` and `rejected.csv`. Tell me what "I don't know" referred to. Then I can say whether the parameters need tuning or whether Cellpose needs fine-tuning.
