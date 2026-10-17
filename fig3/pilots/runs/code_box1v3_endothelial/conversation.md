# code_box1v3_endothelial

## USER (2026-10-17T09:09:55.434Z)

Act as a helpful coding assistant for a cell biologist. You cannot run code. You may use the Read tool ONLY to view the image the user attached: <fig3-work>/bf3/pb3_endo_r1/bf_preview.png (a preview of their file bf.tif). You may use WebSearch and WebFetch. Do not open any other file.

The user writes:
"I want to count the endothelial cells and measure their area from brightfield images of a confluent endothelial monolayer (some cancer cells sit on top). Help me write the analysis.
My images are 2D, with axes Y, X, channels 1 (brightfield), data type uint16 (12-bit values), pixel/voxel size 0.65 µm, and objects of interest approximately 25–50 µm in size. The output I need is a label image with one integer per endothelial cell (0 = background) and a table of endothelial-cell areas in µm². I can provide a manually annotated example (a label image of one field).
Please:

* Clarify the task. Ask for missing information only when it could materially affect the analysis. If useful, ask me for representative images or examples of the expected result.
* Use appropriate methods. Prefer established, maintained software and documented APIs. Check current documentation rather than relying only on memory. If consequential behaviour remains unclear, inspect the source code when available rather than guessing.
* Check deep learning model suitability. If using a pre-trained model, consider whether my images match its training data, including image type, channels, dimensionality, object scale, preprocessing and post-processing.
* Write code according to best practices. Keep functions small and focused, use clear names and annotations, and separate consequential processing steps. Validate inputs, provide informative errors and do not use silent fallbacks.
* Make processing explicit. State important parameters, defaults and transformations, including resizing, resampling, normalisation, channel selection and post-processing. Preserve the original coordinate system and physical units unless a transformation is explicitly required and documented.
* Make the analysis testable. Test it on representative reference data where possible, save useful intermediate outputs and overlays, and use validation measures appropriate to the intended biological measurement rather than relying on a single generic score.
* Audit and challenge the result. Before finishing, assume that the analysis could be scientifically wrong even if the code runs and the output looks plausible. Identify the failure modes most likely to change the biological conclusion and suggest concrete tests or reference data that would expose them.
My setup: Python with numpy, scipy, scikit-image, tifffile, pandas and Cellpose 4.2.1.1 (CPU only). My image file is bf.tif."

Reply as you normally would. Put the analysis script in ONE complete ```python block that reads bf.tif and saves the label image as labels.tif; it must be the first ```python block in your reply. Any test or other code goes in later blocks.

## HARNESS NOTE (2026-10-17T09:09:55.463Z)

<system-reminder>
Your final report is delivered through SubagentHandback: when your work is complete, call SubagentHandback({message: <your full report>}). The call ends your run, so make it your last step. Only a SubagentHandback call reaches your caller as your result; plain text you write at the end is not delivered. Do not also send the report with SendMessage: your caller would get it twice.
</system-reminder>

*[tool call: Read: <fig3-work>/bf3/pb3_endo_r1/bf_preview.png]*

*[tool call: ToolSearch: select:WebFetch,WebSearch]*

*[tool call: WebFetch: https://cellpose.readthedocs.io/en/latest/api.html]*

*[tool call: WebFetch: https://cellpose.readthedocs.io/en/latest/settings.html]*

## ASSISTANT (final report)

## What I looked at

I viewed the preview of bf.tif and checked the Cellpose 4 docs. The preview shows a faint, low-contrast monolayer. Endothelial cell borders are only just visible, and the cells look like large polygons of about 40–70 px. Bright, round, high-contrast cancer cells (about 25–35 px) sit on top, along with debris and a few saturated blobs.

This matters because Cellpose-SAM (cpsam) is a generalist model. It will probably pick out the bright round cancer cells much more readily than the faint endothelial cells underneath. I cannot run code, so I don't know how well it works on your images. Treat the script below as a first attempt to be checked against your annotation. Fine-tuning on your own labels is the likely next step.

## Questions that would change the analysis

1. Is the whole field in bf.tif the 1024x1024 shown in the preview, or was it downscaled for the preview? I assume 0.65 µm/px for the real file.
2. What should happen to endothelial area under a cancer cell? The cell is partly hidden, so its visible area is underestimated. I assume you want to flag those cells rather than silently include or drop them.
3. Is the manual annotation endothelial-only, with cancer cells left as 0? I assume so.
4. Are fields all from the same microscope and contrast mode (plain brightfield rather than phase)? The preview has phase-like halos around the cancer cells. I assume they are all the same.

## Methods and choices

- **Model:** Cellpose 4 (cpsam). It takes no `channels` argument. It uses the first 3 channels, so I pass the brightfield image in channel 0 and zeros in the other two, which the docs say is supported. By default it normalises each channel by 1st–99th percentile. I leave that on and flat-field correct first.
- **Diameter:** I give it a diameter in pixels, derived from µm. The default is 40 µm, which is about 62 px. Cellpose rescales internally and returns masks at the original size, so the coordinate system and pixel size are unchanged. The docs say cpsam is fairly size-invariant, so `--diameter-um` is a parameter to tune.
- **Thresholds:** `flow_threshold=0.4` and `cellprob_threshold=0.0` are the Cellpose defaults, set explicitly. For faint cells, lowering `cellprob_threshold` gives more and larger masks.
- **Flat-field correction:** I subtract a large Gaussian background (sigma about 100 µm) and add back the mean. This removes uneven illumination, which is visible in your preview.
- **Border cells:** Cells touching the image edge are cut off, so I flag them. The area summary excludes them.
- **Cancer cells:** The script does not separate cancer cells. Separating them needs a decision from you (see the audit).

```python
#!/usr/bin/env python
"""Segment endothelial cells in a 2D brightfield image (Cellpose-SAM) and
measure their areas.

Input : bf.tif   (Y, X), uint16 (12-bit), 0.65 um/pixel
Output: labels.tif            uint16/uint32 label image, 0 = background
        endothelial_areas.csv one row per label, area in um^2
        flatfield.tif, overlay.tif  intermediate outputs for inspection

Processing steps (nothing else is applied):
 1. validate input
 2. flat-field correction (Gaussian background subtraction), float32
 3. Cellpose-SAM; Cellpose's own normalisation (1st-99th percentile per
    channel); diameter given in pixels derived from um; masks come back at
    the original image size, so the coordinate system is unchanged
 4. remove objects smaller than --min-area-um2 and relabel sequentially
 5. measure areas; flag cells touching the image border
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, segmentation

EXPECTED_MAX_12BIT = 4095


def load_brightfield(path: Path) -> np.ndarray:
    """Read a single-channel 2D uint16 image; raise on anything else."""
    if not path.is_file():
        raise FileNotFoundError(f"Input image not found: {path}")
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(
            f"Expected a 2D (Y, X) image, got shape {image.shape}. "
            "Squeeze singleton axes or select one channel explicitly."
        )
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 data, got {image.dtype}.")
    if image.max() == image.min():
        raise ValueError("Image is constant; nothing to segment.")
    if image.max() > EXPECTED_MAX_12BIT:
        raise ValueError(
            f"Max value {image.max()} exceeds the 12-bit range "
            f"({EXPECTED_MAX_12BIT}); check the bit depth before continuing."
        )
    return image


def flatfield_correct(image: np.ndarray, sigma_px: float) -> np.ndarray:
    """Subtract a heavily blurred copy (uneven illumination), keep the mean."""
    img = image.astype(np.float32)
    background = ndi.gaussian_filter(img, sigma=sigma_px)
    return img - background + float(img.mean())


def segment_cellpose(
    image: np.ndarray,
    diameter_px: float,
    flow_threshold: float,
    cellprob_threshold: float,
) -> np.ndarray:
    """Run Cellpose-SAM (CPU) on a single-channel image; return int labels."""
    from cellpose import models  # imported here: slow import, fail late

    # cpsam uses the first 3 channels; unused channels are set to zero.
    rgb = np.zeros((*image.shape, 3), dtype=np.float32)
    rgb[..., 0] = image
    model = models.CellposeModel(gpu=False)
    masks, _flows, _styles = model.eval(
        rgb,
        channel_axis=2,
        diameter=diameter_px,
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold,
        normalize=True,  # per-channel 1st-99th percentile (Cellpose default)
    )
    masks = np.asarray(masks)
    if masks.shape != image.shape:
        raise RuntimeError(
            f"Cellpose returned shape {masks.shape}, expected {image.shape}."
        )
    return masks


def remove_small_objects(labels: np.ndarray, min_area_px: int) -> np.ndarray:
    """Drop labels smaller than min_area_px and relabel 1..N."""
    areas = np.bincount(labels.ravel())
    too_small = areas < min_area_px
    too_small[0] = False
    cleaned = labels.copy()
    cleaned[too_small[labels]] = 0
    relabeled, _, _ = segmentation.relabel_sequential(cleaned)
    return relabeled


def measure_areas(labels: np.ndarray, pixel_size_um: float) -> pd.DataFrame:
    """Per-cell area in um^2 and a border-touching flag."""
    rows = []
    height, width = labels.shape
    for region in measure.regionprops(labels):
        min_r, min_c, max_r, max_c = region.bbox
        touches_border = (
            min_r == 0 or min_c == 0 or max_r == height or max_c == width
        )
        rows.append(
            {
                "label": region.label,
                "area_px": int(region.area),
                "area_um2": float(region.area) * pixel_size_um**2,
                "centroid_y_um": region.centroid[0] * pixel_size_um,
                "centroid_x_um": region.centroid[1] * pixel_size_um,
                "touches_border": touches_border,
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "label", "area_px", "area_um2",
            "centroid_y_um", "centroid_x_um", "touches_border",
        ],
    )


def make_overlay(image: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """RGB uint8 overlay: grayscale image with red label boundaries."""
    lo, hi = np.percentile(image, (1, 99))
    gray = np.clip((image.astype(np.float32) - lo) / (hi - lo), 0, 1)
    rgb = np.stack([gray] * 3, axis=-1)
    rgb[segmentation.find_boundaries(labels, mode="inner")] = (1, 0, 0)
    return (rgb * 255).astype(np.uint8)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("bf.tif"))
    parser.add_argument("--output", type=Path, default=Path("labels.tif"))
    parser.add_argument("--pixel-size-um", type=float, default=0.65)
    parser.add_argument("--diameter-um", type=float, default=40.0,
                        help="Typical endothelial cell diameter (um).")
    parser.add_argument("--flow-threshold", type=float, default=0.4)
    parser.add_argument("--cellprob-threshold", type=float, default=0.0)
    parser.add_argument("--background-sigma-um", type=float, default=100.0)
    parser.add_argument("--min-area-um2", type=float, default=150.0,
                        help="Objects smaller than this are removed.")
    args = parser.parse_args()

    if args.pixel_size_um <= 0 or args.diameter_um <= 0:
        raise ValueError("Pixel size and diameter must be positive.")

    outdir = args.output.parent
    image = load_brightfield(args.input)

    corrected = flatfield_correct(
        image, sigma_px=args.background_sigma_um / args.pixel_size_um
    )
    tifffile.imwrite(outdir / "flatfield.tif", corrected)

    labels = segment_cellpose(
        corrected,
        diameter_px=args.diameter_um / args.pixel_size_um,
        flow_threshold=args.flow_threshold,
        cellprob_threshold=args.cellprob_threshold,
    )
    min_area_px = int(round(args.min_area_um2 / args.pixel_size_um**2))
    labels = remove_small_objects(labels, min_area_px)

    dtype = np.uint16 if labels.max() <= np.iinfo(np.uint16).max else np.uint32
    tifffile.imwrite(args.output, labels.astype(dtype))
    tifffile.imwrite(outdir / "overlay.tif", make_overlay(image, labels),
                     photometric="rgb")

    table = measure_areas(labels, args.pixel_size_um)
    table.to_csv(outdir / "endothelial_areas.csv", index=False)

    interior = table[~table["touches_border"]]
    print(f"Cells: {len(table)} ({len(interior)} not touching the border)")
    if len(interior):
        print(f"Median area (non-border): {interior['area_um2'].median():.0f} um^2")
    else:
        print("WARNING: no non-border cells found; inspect overlay.tif.")


if __name__ == "__main__":
    main()
```

Usage: `python analyse.py --input bf.tif --output labels.tif`. Check `overlay.tif` before trusting any number.

## Testing against your manual annotation

Send me the annotated label image (and its bf.tif) and I will help interpret the results. This checks the biological measurements, not one generic score. It reports the count error, the F1 score at IoU 0.5 (a standard instance-matching measure), and the area bias on matched cells.

```python
import numpy as np, tifffile
from skimage import measure

def match(gt, pred, iou_thr=0.5):
    """Greedy one-to-one matching by IoU; returns list of (gt_id, pred_id, iou)."""
    pairs = []
    for g in np.unique(gt)[1:]:
        gm = gt == g
        ids, counts = np.unique(pred[gm], return_counts=True)
        for p, c in zip(ids, counts):
            if p == 0:
                continue
            iou = c / (gm.sum() + (pred == p).sum() - c)
            if iou >= iou_thr:
                pairs.append((g, p, iou))
    return pairs

gt = tifffile.imread("manual_labels.tif"); pred = tifffile.imread("labels.tif")
pairs = match(gt, pred)
tp = len(pairs); n_gt = len(np.unique(gt)) - 1; n_pr = len(np.unique(pred)) - 1
f1 = 2 * tp / (n_gt + n_pr)
print(f"GT {n_gt}, pred {n_pr}, count error {(n_pr - n_gt) / n_gt:+.1%}, F1@0.5 {f1:.2f}")
px = 0.65 ** 2
a_gt = np.array([(gt == g).sum() * px for g, _, _ in pairs])
a_pr = np.array([(pred == p).sum() * px for _, p, _ in pairs])
print(f"Matched-cell area bias: median {np.median(a_pr / a_gt - 1):+.1%}")
print(f"Total area, GT vs pred (um^2): {(gt > 0).sum() * px:.0f} vs {(pred > 0).sum() * px:.0f}")
```

## Audit: how this could be scientifically wrong

1. **Model segments cancer cells, not endothelium (most likely).** If so, the count is biased toward the number of cancer cells and the areas are about 30 µm round objects. Check in `overlay.tif` whether red outlines sit on bright round cells. If they do, the fix is fine-tuning cpsam on your annotation (a few fields can be enough), or masking the cancer cells first.
2. **Under-segmentation or over-segmentation of the faint monolayer.** Weak borders can merge several cells into one big object or split one cell into pieces. Both change count and area in opposite directions. Compare the median area from the script with your manual median. Sweep `--cellprob-threshold` (for example -3 to +1) and `--diameter-um` (30 to 60) and see whether count and area are stable.
3. **Occlusion by cancer cells.** Endothelial cells under a cancer cell lose area, so cells in cancer-rich regions look smaller. Compare areas near and far from cancer cells. If the biological question is about contact with cancer cells, this bias is directly confounded with your result.
4. **Debris and saturated blobs** can appear as small false cells. The `--min-area-um2` filter (150 µm²) is a guess. Check the smallest objects by eye.
5. **Border cells** are truncated. They are flagged and excluded from the area summary, but they still appear in `labels.tif`. Keep them out of density counts, or count them consistently.
6. **Illumination and focus differences between fields.** Percentile normalisation and flat-field correction behave differently across images. Test on fields from other days or conditions, not just the annotated one.
7. **A single annotated field can't show generalisation.** Hold out whole fields from tuning, and use a second annotator on a subset to see how much human variability the model has to beat.
8. **Brightfield area is the visible footprint**, not necessarily the true cell boundary. Boundaries drawn by an annotator are the reference, so say so when you report areas.

## Cellpose caveats from the docs

- The docs for `eval()` and the constructor disagree on some defaults (for example `batch_size` and the `pretrained_model` name), so I only rely on arguments I could confirm: `channel_axis`, `diameter`, `flow_threshold`, `cellprob_threshold`, `normalize`.
- I have not confirmed how the normaliser treats the two all-zero channels. If the overlay looks wrong, try putting the same image in all 3 channels and compare.
- I cannot run code here, so none of this has been executed. If it errors on your machine, send me the traceback.

## USER (2026-10-17T09:23:55.891Z)

The coordinator sent a message while you were working:
The user replies:
"Thanks. Answers to your questions:
1. The preview is the full field (1024 x 1022 px), only contrast-scaled to 8-bit for display. Pixel size 0.65 µm is correct (from the metadata).
2. Endothelial cells partly covered by a cancer cell: label the visible part, do not exclude them.
3. Yes, the annotation contains endothelial cells only (cancer cells are 0). Cells touching the image border are not annotated.
4. Yes, all fields come from the same microscope and settings, plain brightfield.
Here is my annotation of this field (a colour-coded label image, 382 complete endothelial cells): you may view <fig3-work>/bf3/box3/assets/endo_annotation.png with the Read tool."

Same rules as before (you cannot run code; Read only the image preview and this annotation; WebSearch/WebFetch allowed). Reply to the user as you normally would. If you change the analysis script, put the complete updated script as the FIRST ```python block of this reply (reads bf.tif, saves labels.tif).

Address this before completing your current task.

*[tool call: Read: <fig3-work>/bf3/box3/assets/endo_annotation.png]*

## ASSISTANT (final report)

## What your annotation changes

I viewed `endo_annotation.png`. It is a space-filling mosaic of 382 cells with no gaps between them. Border cells are left out, which leaves a dark rim of roughly 10–20 px around the field. There are no holes where cancer cells sit, so the endothelial labels continue under and around them, as you asked in answer 2.

Rough numbers from it:
- The field is 1024 x 1022 px, about 665 x 664 µm, or 0.44 mm².
- Mean annotated area is about 2,400 px, or about 1,000 µm² (my estimate from the image, not measured).
- That gives an equivalent diameter of about 36 µm, so the 40 µm diameter default is in the right range.
- The smallest cells are about 15 x 20 px, or roughly 130 µm².

Changes I made to the script:
1. **Border cells are removed from `labels.tif` by default**, to match how you annotate. The flag `--keep-border-cells` turns this off. The earlier version kept them in the label image and only flagged them. Removal happens before the size filter, and the number removed is printed.
2. **`--min-area-um2` default lowered from 150 to 100**, because your smallest annotated cells are about 130 µm². I do not know how many true small cells are lost at 100, so check this.
3. **`--diameter-um` default lowered from 40 to 36** to match your annotation.
4. **Removed the `touches_border` column**, since all remaining cells are complete.

I cannot run code, so none of this has been executed. The first thing to check is whether Cellpose labels the faint monolayer or only the bright round cancer cells.

```python
#!/usr/bin/env python
"""Segment endothelial cells in a 2D brightfield image (Cellpose-SAM) and
measure their areas.

Input : bf.tif   (Y, X), uint16 (12-bit), 0.65 um/pixel
Output: labels.tif            uint16/uint32 label image, 0 = background
        endothelial_areas.csv one row per label, area in um^2
        flatfield.tif, overlay.tif  intermediate outputs for inspection

Processing steps (nothing else is applied):
 1. validate input
 2. flat-field correction (Gaussian background subtraction), float32
 3. Cellpose-SAM; Cellpose's own normalisation (1st-99th percentile per
    channel); diameter given in pixels derived from um; masks come back at
    the original image size, so the coordinate system is unchanged
 4. remove cells touching the image border (they are truncated; the manual
    annotation excludes them too) unless --keep-border-cells is given
 5. remove objects smaller than --min-area-um2 and relabel 1..N
 6. measure areas in um^2
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, segmentation

EXPECTED_MAX_12BIT = 4095


def load_brightfield(path: Path) -> np.ndarray:
    """Read a single-channel 2D uint16 image; raise on anything else."""
    if not path.is_file():
        raise FileNotFoundError(f"Input image not found: {path}")
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(
            f"Expected a 2D (Y, X) image, got shape {image.shape}. "
            "Squeeze singleton axes or select one channel explicitly."
        )
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 data, got {image.dtype}.")
    if image.max() == image.min():
        raise ValueError("Image is constant; nothing to segment.")
    if image.max() > EXPECTED_MAX_12BIT:
        raise ValueError(
            f"Max value {image.max()} exceeds the 12-bit range "
            f"({EXPECTED_MAX_12BIT}); check the bit depth before continuing."
        )
    return image


def flatfield_correct(image: np.ndarray, sigma_px: float) -> np.ndarray:
    """Subtract a heavily blurred copy (uneven illumination), keep the mean."""
    img = image.astype(np.float32)
    background = ndi.gaussian_filter(img, sigma=sigma_px)
    return img - background + float(img.mean())


def segment_cellpose(
    image: np.ndarray,
    diameter_px: float,
    flow_threshold: float,
    cellprob_threshold: float,
) -> np.ndarray:
    """Run Cellpose-SAM (CPU) on a single-channel image; return int labels."""
    from cellpose import models  # imported here: slow import, fail late

    # cpsam uses the first 3 channels; unused channels are set to zero.
    rgb = np.zeros((*image.shape, 3), dtype=np.float32)
    rgb[..., 0] = image
    model = models.CellposeModel(gpu=False)
    masks, _flows, _styles = model.eval(
        rgb,
        channel_axis=2,
        diameter=diameter_px,
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold,
        normalize=True,  # per-channel 1st-99th percentile (Cellpose default)
    )
    masks = np.asarray(masks)
    if masks.shape != image.shape:
        raise RuntimeError(
            f"Cellpose returned shape {masks.shape}, expected {image.shape}."
        )
    return masks


def remove_border_cells(labels: np.ndarray) -> np.ndarray:
    """Set every label that touches the image edge to 0 (no relabelling)."""
    edge_ids = np.unique(
        np.concatenate(
            [labels[0, :], labels[-1, :], labels[:, 0], labels[:, -1]]
        )
    )
    edge_ids = edge_ids[edge_ids != 0]
    cleaned = labels.copy()
    cleaned[np.isin(labels, edge_ids)] = 0
    return cleaned


def remove_small_objects(labels: np.ndarray, min_area_px: int) -> np.ndarray:
    """Drop labels smaller than min_area_px (0 stays background)."""
    areas = np.bincount(labels.ravel())
    too_small = areas < min_area_px
    too_small[0] = False
    cleaned = labels.copy()
    cleaned[too_small[labels]] = 0
    return cleaned


def measure_areas(labels: np.ndarray, pixel_size_um: float) -> pd.DataFrame:
    """Per-cell area in um^2 and centroid in um."""
    rows = [
        {
            "label": region.label,
            "area_px": int(region.area),
            "area_um2": float(region.area) * pixel_size_um**2,
            "centroid_y_um": region.centroid[0] * pixel_size_um,
            "centroid_x_um": region.centroid[1] * pixel_size_um,
        }
        for region in measure.regionprops(labels)
    ]
    return pd.DataFrame(
        rows,
        columns=["label", "area_px", "area_um2",
                 "centroid_y_um", "centroid_x_um"],
    )


def make_overlay(image: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """RGB uint8 overlay: grayscale image with red label boundaries."""
    lo, hi = np.percentile(image, (1, 99))
    gray = np.clip((image.astype(np.float32) - lo) / (hi - lo), 0, 1)
    rgb = np.stack([gray] * 3, axis=-1)
    rgb[segmentation.find_boundaries(labels, mode="inner")] = (1, 0, 0)
    return (rgb * 255).astype(np.uint8)


def count_labels(labels: np.ndarray) -> int:
    return int(np.count_nonzero(np.unique(labels)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("bf.tif"))
    parser.add_argument("--output", type=Path, default=Path("labels.tif"))
    parser.add_argument("--pixel-size-um", type=float, default=0.65)
    parser.add_argument("--diameter-um", type=float, default=36.0,
                        help="Typical endothelial cell diameter (um).")
    parser.add_argument("--flow-threshold", type=float, default=0.4)
    parser.add_argument("--cellprob-threshold", type=float, default=0.0)
    parser.add_argument("--background-sigma-um", type=float, default=100.0)
    parser.add_argument("--min-area-um2", type=float, default=100.0,
                        help="Objects smaller than this are removed.")
    parser.add_argument("--keep-border-cells", action="store_true",
                        help="Keep cells touching the image edge.")
    args = parser.parse_args()

    if args.pixel_size_um <= 0 or args.diameter_um <= 0:
        raise ValueError("Pixel size and diameter must be positive.")

    outdir = args.output.parent
    image = load_brightfield(args.input)

    corrected = flatfield_correct(
        image, sigma_px=args.background_sigma_um / args.pixel_size_um
    )
    tifffile.imwrite(outdir / "flatfield.tif", corrected)

    labels = segment_cellpose(
        corrected,
        diameter_px=args.diameter_um / args.pixel_size_um,
        flow_threshold=args.flow_threshold,
        cellprob_threshold=args.cellprob_threshold,
    )
    n_raw = count_labels(labels)

    if not args.keep_border_cells:
        labels = remove_border_cells(labels)
    n_after_border = count_labels(labels)

    min_area_px = int(round(args.min_area_um2 / args.pixel_size_um**2))
    labels = remove_small_objects(labels, min_area_px)
    labels, _, _ = segmentation.relabel_sequential(labels)
    n_final = count_labels(labels)
    print(f"Cellpose objects: {n_raw}; after border removal: "
          f"{n_after_border}; after size filter: {n_final}")

    dtype = np.uint16 if labels.max() <= np.iinfo(np.uint16).max else np.uint32
    tifffile.imwrite(args.output, labels.astype(dtype))
    tifffile.imwrite(outdir / "overlay.tif", make_overlay(image, labels),
                     photometric="rgb")

    table = measure_areas(labels, args.pixel_size_um)
    table.to_csv(outdir / "endothelial_areas.csv", index=False)
    if len(table):
        print(f"Median area: {table['area_um2'].median():.0f} um^2")
    else:
        print("WARNING: no cells found; inspect overlay.tif.")


if __name__ == "__main__":
    main()
```

Usage: `python analyse.py --input bf.tif --output labels.tif`. Look at `overlay.tif` before you trust any number.

## Testing against your annotation

Your annotation holds 382 complete cells, so it can check count, matching and area. Save it as a label TIFF (the PNG is colour-coded, so I can't use it directly). It must be the same shape as `labels.tif`, with 0 for background and cancer-cell regions covered by the visible endothelial part.

```python
import numpy as np, tifffile

PIXEL_UM2 = 0.65 ** 2

def match(gt, pred, iou_thr=0.5):
    """One-to-one matches (gt_id, pred_id, iou) with IoU >= iou_thr."""
    pairs = []
    for g in np.unique(gt)[1:]:
        gm = gt == g
        ids, counts = np.unique(pred[gm], return_counts=True)
        for p, c in zip(ids, counts):
            if p == 0:
                continue
            iou = c / (gm.sum() + (pred == p).sum() - c)
            if iou >= iou_thr:
                pairs.append((g, p, iou))
    return pairs

gt = tifffile.imread("manual_labels.tif")
pred = tifffile.imread("labels.tif")
assert gt.shape == pred.shape, (gt.shape, pred.shape)
n_gt = len(np.unique(gt)) - 1          # expected 382
n_pr = len(np.unique(pred)) - 1
pairs = match(gt, pred)
tp = len(pairs)
print(f"GT {n_gt}, pred {n_pr}, count error {(n_pr - n_gt) / n_gt:+.1%}")
print(f"F1@IoU0.5 {2 * tp / (n_gt + n_pr):.2f}, "
      f"missed {n_gt - tp}, extra {n_pr - tp}")
a_gt = np.array([(gt == g).sum() * PIXEL_UM2 for g, _, _ in pairs])
a_pr = np.array([(pred == p).sum() * PIXEL_UM2 for _, p, _ in pairs])
print(f"Matched-cell area bias: median {np.median(a_pr / a_gt - 1):+.1%}")
print(f"Median area GT {np.median(a_gt):.0f} vs pred {np.median(a_pr):.0f} um^2")
print(f"Covered area GT {np.count_nonzero(gt) * PIXEL_UM2:.0f} vs "
      f"pred {np.count_nonzero(pred) * PIXEL_UM2:.0f} um^2")
```

## Audit: what is most likely to be wrong

1. **The model may not segment the faint monolayer at all.** Your annotation is a tight mosaic, and Cellpose-SAM may instead outline the bright round cancer cells and leave gaps. Check three numbers: count versus 382, the covered-area ratio (your mosaic covers most of the field), and the overlay. If coverage is low, lower `--cellprob-threshold` (try -2, then -4). If the monolayer still isn't found, fine-tune on your annotation. You have 382 cells, which is a sensible starting set, but hold out whole fields for testing.
2. **Merged and split cells.** With weak borders, neighbouring cells merge into big objects or one cell splits into two. Look at the matched-area bias and the "missed" and "extra" counts separately. A median area that looks right can hide merges and splits that cancel out.
3. **Cells under cancer cells.** You want the visible part labelled. Cellpose may label the cancer cell, drop the endothelial cell under it, or split the endothelial cell around the cancer cell. Make a separate test that scores only the annotated cells that overlap bright cancer cells. These are the cells most likely to be missed.
4. **Border handling.** Border-touching cells are removed from the label image. Cells just inside the border can still be cut off by Cellpose's own edge effects, so look at the outer 20 px of the overlay. Use the unannotated rim in your annotation to count extra predictions there.
5. **Small-object filter.** At 100 µm² some true small cells (your smallest are about 130 µm²) could be removed, and some debris could remain. Compare the area histograms of prediction and annotation at the low end.
6. **One annotated field is a weak test.** All the above applies to this field only. Annotate at least one more field from a different dish or day before using the areas in a comparison between conditions.
