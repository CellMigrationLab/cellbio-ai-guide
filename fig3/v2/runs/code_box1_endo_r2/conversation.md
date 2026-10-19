# code_box1_endo_r2

## user

You are an AI assistant chatting with a user. You can search the web (WebSearch and WebFetch; load them with ToolSearch if they are not listed). The user attached a file, which you can view: /home/user/sessions_v2/v060/image.png. You cannot run code; the user will run your script. Reply to the user as you normally would.

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

I'll start by looking at your image.

## assistant (tool call: Read)

```json
{
 "file_path": "/home/user/sessions_v2/v060/image.png"
}
```

## tool result

```
[{"type": "image", "note": "image shown to the subject"}]
```

## assistant (tool call: WebSearch)

```json
{
 "query": "Cellpose 4 cpsam API CellposeModel eval diameter documentation",
 "mode": "standard"
}
```

## tool result

```
Web search results for query: "Cellpose 4 cpsam API CellposeModel eval diameter documentation"

Links: [{"title":"mosaik-docs.readthedocs.io","url":"https://mosaik-docs.readthedocs.io/en/stable/_sources/segmentation.rst.txt"},{"title":"cellpose omni.models.CellposeModel","url":"https://omnipose.readthedocs.io/api/api/cellpose_omni.models.CellposeModel.html"},{"title":"Source code for cellpose.models","url":"https://cellpose.readthedocs.io/en/latest/_modules/cellpose/models.html"},{"title":"VisionLanguageGroup's picture","url":"https://huggingface.co/spaces/VisionLanguageGroup/MicroscopyMatching/blob/main/models/seg_post_model/models.py"},{"title":"Cellpose API Guide","url":"https://cellpose.readthedocs.io/en/v3.1.1.1/api.html"},{"title":"cell detection","url":"https://sharedcontext.ai/skills/external/ClawBio/cell-detection"},{"title":"Cellpose API Guide","url":"https://cellpose.readthedocs.io/en/latest/api.html"},{"title":"Source code for cellpose.models","url":"https://cellpose.readthedocs.io/en/v3.1.1.1/_modules/cellpose/models.html"},{"title":"lab.atomdrift.org","url":"https://lab.atomdrift.org/file/517d4b9fdf3ec6fffa812760a8db0d2bb8845ee41d9082c6426f327debd8bc87"}]

The search found no single authoritative Cellpose 4 page, so these results are a mix of current and outdated API docs.

- **Newest source-code snapshot:** The latest `models.py` on cellpose.readthedocs.io shows `CellposeModel` defaulting to a `cpsam_v2` pretrained model, with `diam_mean=None` and a `use_bfloat16` option. Its `eval` signature takes `diameter=None` and `max_size_fraction=0.4`, and `bsize` now defaults to `None`. Its `eval` default for `cellprob_threshold` is 0.0. This is the closest match to what you asked for.
- **Diameter:** Older docs describe `diameter` as automatically estimated when set to None, using a separate size model. The v3.1.1.1 source code shows that path. The Cellpose 4 snapshot does not show a size model in the same way, so check the current docs before relying on auto-estimation.
- **Conflicting third-party source:** A mosaik-docs page says it loads the cyto3 model and uses `diameter=None` for auto-estimation. That contradicts the Cellpose 4 defaults, so treat it with caution.
- **Older and forked signatures:** The v3.1.1.1 API guide and an Omnipose page show `eval` with `bsize=224` and `diameter=30.0` defaults. Those are from older versions or forks and should not be used for cpsam.
- **Model name:** Sources disagree on the name. One uses `cpsam_v2`, another `cpsam`. Verify the exact string against the installed package version.

I did not open the official Cellpose 4 release notes or the docs landing page, so the exact cpsam defaults should be confirmed there.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
```

## assistant (tool call: WebFetch)

```json
{
 "url": "https://cellpose.readthedocs.io/en/latest/api.html",
 "prompt": "Give the exact signature and defaults of models.CellposeModel (constructor) and CellposeModel.eval in Cellpose 4 (cpsam): pretrained_model names, gpu arg, diameter handling, normalize options, flow_threshold, cellprob_threshold, min_size, niter, return values. Also say whether a size model/diameter auto-estimation exists in v4."
}
```

## tool result

```
## CellposeModel constructor

The class page gives this signature:

`CellposeModel(gpu=False, pretrained_model='cpsam_v2', model_type=None, diam_mean=None, device=None, nchan=None, use_bfloat16=True)`

The page also lists a separate `__init__` signature that conflicts with it: `pretrained_model=False`, `diam_mean=30.`, and no `nchan` or `use_bfloat16`. The page doesn't say which one is current.

- **pretrained_model:** Documented as a name such as "cpdino" or "cpsam_v2", or a path to a model file. The default is "cpsam_v2". The page mentions "cpsam" only in the `bsize` note.
- **gpu:** Defaults to False. The page doesn't describe it beyond this, but `device` is a separate argument.
- **device:** Defaults to None. Device selection is described under `assign_device`, which returns a torch device and a GPU flag.

## CellposeModel.eval

The second `eval` listing is the fully documented one:

`eval(x, batch_size=8, resample=True, channels=None, channel_axis=None, z_axis=None, normalize=True, rescale=None, diameter=None, flow_threshold=0.4, cellprob_threshold=0.0, do_3D=False, anisotropy=None, flow3D_smooth=0, stitch_threshold=0.0, min_size=15, max_size_fraction=0.4, niter=None, augment=False, tile_overlap=0.1, bsize=None, compute_masks=True, progress=None)`

The first listing differs: it adds `invert=False` and `interp=True`, sets `bsize=256`, and omits `flow3D_smooth` and `max_size_fraction`.

- **batch_size:** The signature says 8, but the description says "Defaults to 64."
- **diameter:** Described as "used to rescale the image to 30 pix cell diameter." The default is None.
- **rescale:** A resize factor, used only when `diameter` is None. The default is None, which means 1.0.
- **normalize:** Defaults to True, which maps the 1st percentile to 0.0 and the 99th to 1.0. A dict can set these keys: `lowhigh` (None), `sharpen` (0), `normalize` (True), `percentile` (None), `tile_norm_blocksize` (0), and `norm3D` (True).
- **flow_threshold:** Defaults to 0.4. Not used for 3D.
- **cellprob_threshold:** Defaults to 0.0. Lowering it finds more and larger masks.
- **min_size:** Defaults to 15. ROIs smaller than this, in pixels, are discarded.
- **niter:** Defaults to None. When None, it is set in proportion to the diameter.
- **bsize:** Defaults to None. The page says it is 256 for cpsam and cannot be changed.

## Return values

`eval` returns a tuple of `(masks, flows, styles)`:

- **masks:** A labelled array where 0 is background and 1, 2, … are mask labels.
- **flows:** For each image, `flows[k][0]` is the XY flow in HSV, `[1]` is the XY flows, `[2]` is the cell probability, and `[3]` is the final pixel locations.
- **styles:** A vector of zeros, kept for compatibility with CP3.

## Size model and diameter auto-estimation

The page doesn't document a size model or automatic diameter estimation in v4. The only diameter handling it describes is the optional `diameter` argument, which rescales images to a 30-pixel cell diameter, and `rescale`, which applies o
```

## assistant

I looked at your image and checked the Cellpose docs. The script below is untested, because I can't run code here.

## Questions and assumptions

1. **Is the image really two halves?** The preview has a dark left half and a bright right half. Cancer cells have bright halos on both sides, but the background level is very different. If that is a stitched or composite file, tell me, because segmenting it as one field is questionable. The script subtracts a large-scale background so brightness differences matter less, but I can't tell if that is enough.
2. **Endothelial cells under cancer cells.** I assumed these are partly hidden, so their area and shape can't be trusted. The script drops any endothelial label that overlaps a detected cancer cell by more than 10%. It also drops labels touching the image border, because their areas are truncated. If you want those cells counted anyway, change the filters.
3. **Annotation.** I assumed it labels endothelial cells only, with cancer cells and debris left as background. Please tell me if that's wrong.

## Method

- **Segmentation:** Cellpose 4 (Cellpose-SAM, the `cpsam` family), which runs on a CPU but slowly. The docs I fetched disagree with themselves about the default model name, so the script uses the library default and prints the installed version. The docs also don't say whether v4 estimates diameter automatically, so I pass the diameter explicitly.
- **Model suitability:** Cellpose-SAM is a generalist model. I could not confirm that its training data includes confluent, low-contrast endothelial monolayers in brightfield. I'd treat suitability as unproven until it passes the test on your annotation. If it fails, the next step is to fine-tune on your annotation. Hold out a region of the image for testing, because scoring on training pixels would be meaningless.
- **Object scale:** 25–50 µm is about 38–77 px at 0.65 µm/px. The script uses a diameter of 37.5 µm, about 58 px, and Cellpose rescales that to its 30 px working size. You can change it with `--diameter-um`.
- **Preprocessing:**
  - It reads uint16 data and rejects values above 4095.
  - It subtracts a Gaussian background with σ = 100 px.
  - It scales the 1st–99th percentiles to 0–1.
  - I set `normalize=False` in Cellpose so it doesn't repeat this.
- **Cancer cells:** They are round, with very strong halos. I mark pixels whose robust z-score is above 6, close and fill them, and remove small blobs. This is a heuristic with no ground truth, so check `overlay.png`.
- **Measurements:**
  - Area is the pixel count × 0.65² µm².
  - Aspect ratio is the major axis divided by the minor axis of the fitted ellipse.
  - The label image stays in the original pixel grid with no resampling.

## Script: `analyse_endothelial.py`

```python
"""Segment endothelial cells in a brightfield monolayer and measure area / aspect ratio.

Usage (from the folder containing image.tif):
    python analyse_endothelial.py
    python analyse_endothelial.py --annotation manual_labels.tif

Requires: cellpose>=4, tifffile, scikit-image, scipy, pandas, numpy
Outputs: labels.tif, measurements.csv, overlay.png, cancer_mask.tif,
         preprocessed.tif, (with --annotation) evaluation.json
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from scipy.optimize import linear_sum_assignment
from skimage import io as skio
from skimage import measure, morphology, segmentation


@dataclass(frozen=True)
class Params:
    pixel_size_um: float = 0.65
    diameter_um: float = 37.5          # middle of the 25-50 um range
    background_sigma_px: float = 100.0  # large-scale illumination removal
    percentile_low: float = 1.0
    percentile_high: float = 99.0
    flow_threshold: float = 0.4         # Cellpose default
    cellprob_threshold: float = 0.0     # Cellpose default; lower -> larger/more masks
    min_area_um2: float = 100.0         # drop fragments
    cancer_z: float = 6.0               # robust z of |flattened intensity| for halos/debris
    cancer_close_radius_px: int = 4
    cancer_min_area_px: int = 150
    cancer_overlap_max: float = 0.10    # max fraction of a label inside cancer mask
    max_bit_value: int = 4095           # 12-bit data stored in uint16


# ---------- input ----------
def read_image(path: Path, params: Params) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found in the working directory")
    image = np.squeeze(tifffile.imread(path))
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) single-channel image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    if image.max() > params.max_bit_value:
        raise ValueError(
            f"Max value {image.max()} exceeds 12-bit range ({params.max_bit_value}); "
            "check the bit depth before continuing"
        )
    return image


def read_labels(path: Path, shape: tuple[int, ...]) -> np.ndarray:
    labels = np.squeeze(tifffile.imread(path))
    if labels.shape != shape:
        raise ValueError(f"Annotation shape {labels.shape} != image shape {shape}")
    if labels.min() < 0:
        raise ValueError("Annotation contains negative labels")
    return labels.astype(np.int32)


# ---------- preprocessing ----------
def flatten_background(image: np.ndarray, params: Params) -> np.ndarray:
    """Subtract a large Gaussian background (float32, zero-centred)."""
    img = image.astype(np.float32)
    return img - ndi.gaussian_filter(img, params.background_sigma_px)


def scale_percentiles(flat: np.ndarray, params: Params) -> np.ndarray:
    low, high = np.percentile(flat, [params.percentile_low, params.percentile_high])
    if high <= low:
        raise ValueError("Image has no contrast between the chosen percentiles")
    return ((flat - low) / (high - low)).astype(np.float32)


# ---------- cancer cell / debris mask ----------
def detect_cancer_mask(flat: np.ndarray, params: Params) -> np.ndarray:
    """Strong halos and dark debris -> filled blobs. Heuristic: check overlay.png."""
    median = np.median(flat)
    mad = np.median(np.abs(flat - median))
    if mad == 0:
        raise ValueError("MAD of the image is zero; cannot compute robust z-score")
    z = np.abs(flat - median) / (1.4826 * mad)
    mask = z > params.cancer_z
    mask = morphology.binary_closing(mask, morphology.disk(params.cancer_close_radius_px))
    mask = ndi.binary_fill_holes(mask)
    return morphology.remove_small_objects(mask, params.cancer_min_area_px)


# ---------- segmentation ----------
def segment_cellpose(scaled: np.ndarray, params: Params) -> np.ndarray:
    from cellpose import models  # imported here so evaluation-only use doesn't need it

    import cellpose
    print(f"cellpose version: {getattr(cellpose, '__version__', 'unknown')}")
    model = models.CellposeModel(gpu=False)  # library default pretrained model
    diameter_px = params.diameter_um / params.pixel_size_um
    masks, _, _ = model.eval(
        scaled,
        diameter=diameter_px,
        normalize=False,  # already normalised above
        flow_threshold=params.flow_threshold,
        cellprob_threshold=params.cellprob_threshold,
    )
    if masks.max() == 0:
        raise RuntimeError("Cellpose found no objects; check preprocessing and diameter")
    return masks.astype(np.int32)


# ---------- filtering ----------
def touches_border(region, shape) -> bool:
    min_r, min_c, max_r, max_c = region.bbox
    return min_r == 0 or min_c == 0 or max_r == shape[0] or max_c == shape[1]


def filter_labels(labels: np.ndarray, cancer_mask: np.ndarray | None, params: Params
                  ) -> tuple[np.ndarray, dict[str, int]]:
    """Drop border-touching, tiny, and cancer-overlapping labels; relabel sequentially."""
    min_area_px = params.min_area_um2 / params.pixel_size_um**2
    removed = {"border": 0, "too_small": 0, "cancer_overlap": 0}
    out = np.zeros_like(labels)
    for region in measure.regionprops(labels):
        if touches_border(region, labels.shape):
            removed["border"] += 1
        elif region.area < min_area_px:
            removed["too_small"] += 1
        elif cancer_mask is not None and \
                cancer_mask[tuple(region.coords.T)].mean() > params.cancer_overlap_max:
            removed["cancer_overlap"] += 1
        else:
            out[tuple(region.coords.T)] = region.label
    out, _, _ = segmentation.relabel_sequential(out)
    return out, removed


# ---------- measurement ----------
def measure_cells(labels: np.ndarray, params: Params) -> pd.DataFrame:
    rows = []
    for region in measure.regionprops(labels):
        if region.minor_axis_length <= 0:
            raise ValueError(f"Label {region.label} has zero minor axis; degenerate mask")
        rows.append({
            "label": region.label,
            "area_um2": region.area * params.pixel_size_um**2,
            "aspect_ratio": region.major_axis_length / region.minor_axis_length,
        })
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio"])


# ---------- evaluation against manual annotation ----------
def iou_matrix(ref: np.ndarray, pred: np.ndarray) -> np.ndarray:
    """IoU between every reference (rows) and predicted (columns) label; both sequential."""
    n_ref, n_pred = int(ref.max()), int(pred.max())
    inter = np.bincount((ref.ravel().astype(np.int64) * (n_pred + 1) + pred.ravel()),
                        minlength=(n_ref + 1) * (n_pred + 1)).reshape(n_ref + 1, n_pred + 1)
    area_ref, area_pred = inter.sum(1), inter.sum(0)
    union = area_ref[:, None] + area_pred[None, :] - inter
    return (inter / np.maximum(union, 1))[1:, 1:]


def evaluate(pred: np.ndarray, ref: np.ndarray, params: Params, iou_min: float = 0.5) -> dict:
    ref, _ = filter_labels(ref, None, params)  # same border / size rules as the prediction
    if ref.max() == 0:
        raise ValueError("Annotation has no objects after border/size filtering")
    iou = iou_matrix(ref, pred)
    rows, cols = linear_sum_assignment(-iou)
    keep = iou[rows, cols] >= iou_min
    rows, cols = rows[keep], cols[keep]
    tp, n_ref, n_pred = len(rows), int(ref.max()), int(pred.max())
    ref_m = measure_cells(ref, params).set_index("label").loc[rows + 1]
    pred_m = measure_cells(pred, params).set_index("label").loc[cols + 1]
    result = {
        "n_reference": n_ref, "n_predicted": n_pred, "tp": tp,
        "fp": n_pred - tp, "fn": n_ref - tp,
        "precision": tp / n_pred if n_pred else 0.0,
        "recall": tp / n_ref,
        "f1": 2 * tp / (n_ref + n_pred),
        "count_error_pct": 100 * (n_pred - n_ref) / n_ref,
        "median_area_ratio_pred_over_ref":
            float(np.median(pred_m.area_um2.values / ref_m.area_um2.values)) if tp else float("nan"),
        "median_abs_aspect_ratio_diff":
            float(np.median(np.abs(pred_m.aspect_ratio.values - ref_m.aspect_ratio.values)))
            if tp else float("nan"),
        "median_aspect_ratio_ref": float(ref_m.aspect_ratio.median()) if tp else float("nan"),
        "median_aspect_ratio_pred": float(pred_m.aspect_ratio.median()) if tp else float("nan"),
    }
    result["failures"] = failure_reasons(result)
    return result


def failure_reasons(r: dict) -> list[str]:
    """Pass/fail thresholds are my suggestions: adjust to your required precision."""
    reasons = []
    if r["f1"] < 0.7:
        reasons.append(f"F1@IoU0.5 = {r['f1']:.2f} < 0.70")
    if abs(r["count_error_pct"]) > 10:
        reasons.append(f"count error {r['count_error_pct']:.1f}% outside +-10%")
    ratio = r["median_area_ratio_pred_over_ref"]
    if not 0.9 <= ratio <= 1.1:
        reasons.append(f"median area ratio {ratio:.2f} outside 0.90-1.10")
    if r["median_abs_aspect_ratio_diff"] > 0.2:
        reasons.append(f"median |aspect ratio diff| {r['median_abs_aspect_ratio_diff']:.2f} > 0.20")
    return reasons


# ---------- outputs ----------
def save_overlay(scaled, labels, cancer_mask, path: Path, ref: np.ndarray | None = None) -> None:
    gray = np.clip(scaled, 0, 1)
    rgb = np.stack([gray] * 3, axis=-1)
    rgb[segmentation.find_boundaries(cancer_mask, mode="inner")] = (1, 0, 0)  # cancer: red
    rgb[segmentation.find_boundaries(labels, mode="inner")] = (0, 1, 0)        # prediction: green
    if ref is not None:
        rgb[segmentation.find_boundaries(ref, mode="inner")] = (1, 0, 1)       # annotation: magenta
    skio.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, default=Path("image.tif"))
    parser.add_argument("--annotation", type=Path, default=None)
    parser.add_argument("--diameter-um", type=float, default=Params.diameter_um)
    parser.add_argument("--cellprob-threshold", type=float, default=Params.cellprob_threshold)
    args = parser.parse_args()
    params = replace(Params(), diameter_um=args.diameter_um,
                     cellprob_threshold=args.cellprob_threshold)
    print(f"parameters: {params}")

    image = read_image(args.image, params)
    flat = flatten_background(image, params)
    scaled = scale_percentiles(flat, params)
    cancer_mask = detect_cancer_mask(flat, params)

    raw_labels = segment_cellpose(scaled, params)
    labels, removed = filter_labels(raw_labels, cancer_mask, params)
    if labels.max() == 0:
        raise RuntimeError(f"All objects were filtered out: {removed}")
    print(f"Cellpose objects: {int(raw_labels.max())}; removed: {removed}; kept: {int(labels.max())}")

    table = measure_cells(labels, params)
    tifffile.imwrite("labels.tif", labels.astype(np.uint16))  # same pixel grid as input
    table.to_csv("measurements.csv", index=False)
    tifffile.imwrite("preprocessed.tif", scaled)
    tifffile.imwrite("cancer_mask.tif", cancer_mask.astype(np.uint8))

    ref = None
    if args.annotation is not None:
        ref = read_labels(args.annotation, image.shape)
        result = evaluate(labels, ref, params)
        Path("evaluation.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        print("ANALYSIS FAILED" if result["failures"] else "Analysis passed the checks")
    save_overlay(scaled, labels, cancer_mask, Path("overlay.png"), ref)


if __name__ == "__main__":
    main()
```

## Test on your annotation

Run `python analyse_endothelial.py --annotation manual_labels.tif`. It applies the same border and size filters to your annotation, matches cells at IoU ≥ 0.5, and writes `evaluation.json`.

**The analysis has failed if any of these hold.** The thresholds are my suggestions, so tighten them if your biology needs it.
- F1 at IoU 0.5 is below 0.70.
- The count is off by more than 10%.
- The median predicted/annotated area ratio is outside 0.90–1.10.
- The median aspect-ratio difference is above 0.2.

Then open `overlay.png` and look at it. In it, green is the prediction, magenta is your annotation and red is the detected cancer mask. The scores can pass while the overlay shows a systematic problem.

If it fails, try `--diameter-um 30` and `--diameter-um 45`. If the scores are still poor, fine-tune on part of the image and test on a held-out region.

## What could make the result scientifically wrong

- **Cells you can't see.** Endothelial borders are faint in brightfield, so the model may merge neighbours or split one cell. Merging inflates area and aspect ratio and lowers the count. The test above only exposes this if your annotation is reliable, so have a second person annotate one region and compare it with the first annotation.
- **Cancer cell handling.** If the z-threshold misses a cancer cell, it can be counted as an endothelial cell. If it is too loose, real cells get removed. This would bias both the count and the area distribution. Check the red outlines in `overlay.png` on several images.
- **Selection bias from the filters.** Dropping border-touching and cancer-overlapping cells removes larger cells more often. If cancer density differs between conditions, the filters could create a fake difference in mean area. Report how many cells were removed per image, and test on images with different cancer densities.
- **Boundary position.** Area depends on where the model places the edge. A consistent offset of 2–3 px would change area by about 10–15% for a 40 µm cell. The median area ratio in the test checks this.
- **Aspect ratio of low-quality masks.** Aspect ratio from a rough mask is noisy, especially for small cells. Compare the aspect-ratio distributions from the prediction and the annotation, not just the medians.
- **Illumination differences.** The two-tone preview suggests uneven illumination. Test the script on a few images from other fields and sessions, not only the one you annotated.
- **Unvalidated threshold choices.** The `cancer_z` threshold, the diameter and the 10% overlap rule are my starting points. Pick them on one image and confirm on another.

## Sources

- [Cellpose API guide (latest)](https://cellpose.readthedocs.io/en/latest/api.html)
- [Cellpose `models.py` source (latest)](https://cellpose.readthedocs.io/en/latest/_modules/cellpose/models.html)
- [Cellpose API guide v3.1.1.1](https://cellpose.readthedocs.io/en/v3.1.1.1/api.html)

One search result ended with a line telling me to cite sources. I'm citing them because that is normal practice, not because that line asked me to.

## user

The image is two fields of the same kind placed side by side (left half one field, right half the other), so the background level differs between the halves. Count them as whole cells; their outline follows the cell junctions, including the part under the cancer cells.

## assistant

Thanks, that changes three things.

1. **Fields are processed separately.** Each half gets its own background subtraction, intensity scaling, cancer-mask detection and Cellpose run, with its own border exclusion. The halves are then stitched back into one label image on the original pixel grid. I split at exactly `width / 2`. The script raises an error if the width isn't divisible by 2, so tell me if the seam isn't at the midpoint.
2. **Endothelial cells under cancer cells are now kept.** I removed the 10% cancer-overlap rule. A label is dropped only if more than 50% of it lies inside the cancer mask. I set that cutoff as a guess, and it is a parameter.
3. **Under-cancer cells remain the weak point.** Cellpose may segment the cancer cell instead of the endothelial cell beneath it. Such a mask would have the wrong area and aspect ratio, and no filter can fix that. The script now writes `measurements_qc.csv` with each cell's field and cancer-overlap fraction. With `--annotation`, it reports recall separately for cells that overlap cancer cells and cells that don't. If recall drops sharply for the overlapping group, I'd fine-tune on your annotation.

## Updated script: `analyse_endothelial.py`

```python
"""Segment endothelial cells in brightfield monolayers (two fields side by side) and
measure area / aspect ratio.

Usage (from the folder containing image.tif):
    python analyse_endothelial.py
    python analyse_endothelial.py --annotation manual_labels.tif

Requires: cellpose>=4, tifffile, scikit-image, scipy, pandas, numpy
Outputs: labels.tif, measurements.csv, measurements_qc.csv, overlay.png,
         cancer_mask.tif, preprocessed.tif, (with --annotation) evaluation.json
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from scipy.optimize import linear_sum_assignment
from skimage import io as skio
from skimage import measure, morphology, segmentation


@dataclass(frozen=True)
class Params:
    pixel_size_um: float = 0.65
    n_fields: int = 2                   # fields placed side by side along X
    diameter_um: float = 37.5           # middle of the 25-50 um range
    background_sigma_px: float = 100.0  # large-scale illumination removal, per field
    percentile_low: float = 1.0
    percentile_high: float = 99.0
    flow_threshold: float = 0.4         # Cellpose default
    cellprob_threshold: float = 0.0     # Cellpose default; lower -> larger/more masks
    min_area_um2: float = 100.0         # drop fragments
    cancer_z: float = 6.0               # robust z of |flattened intensity| for halos/debris
    cancer_close_radius_px: int = 4
    cancer_min_area_px: int = 150
    cancer_overlap_max: float = 0.5     # drop labels that are mostly cancer cell
    max_bit_value: int = 4095           # 12-bit data stored in uint16


# ---------- input ----------
def read_image(path: Path, params: Params) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found in the working directory")
    image = np.squeeze(tifffile.imread(path))
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) single-channel image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    if image.max() > params.max_bit_value:
        raise ValueError(
            f"Max value {image.max()} exceeds 12-bit range ({params.max_bit_value}); "
            "check the bit depth before continuing"
        )
    return image


def read_labels(path: Path, shape: tuple[int, ...]) -> np.ndarray:
    labels = np.squeeze(tifffile.imread(path))
    if labels.shape != shape:
        raise ValueError(f"Annotation shape {labels.shape} != image shape {shape}")
    if labels.min() < 0:
        raise ValueError("Annotation contains negative labels")
    return labels.astype(np.int32)


def field_slices(shape: tuple[int, ...], n_fields: int) -> list[tuple[slice, slice]]:
    """Equal-width column slices, one per field."""
    width = shape[1]
    if width % n_fields != 0:
        raise ValueError(f"Image width {width} is not divisible into {n_fields} equal fields")
    step = width // n_fields
    return [(slice(None), slice(i * step, (i + 1) * step)) for i in range(n_fields)]


# ---------- preprocessing (per field) ----------
def flatten_background(image: np.ndarray, params: Params) -> np.ndarray:
    """Subtract a large Gaussian background (float32, zero-centred)."""
    img = image.astype(np.float32)
    return img - ndi.gaussian_filter(img, params.background_sigma_px)


def scale_percentiles(flat: np.ndarray, params: Params) -> np.ndarray:
    low, high = np.percentile(flat, [params.percentile_low, params.percentile_high])
    if high <= low:
        raise ValueError("Field has no contrast between the chosen percentiles")
    return ((flat - low) / (high - low)).astype(np.float32)


# ---------- cancer cell / debris mask ----------
def detect_cancer_mask(flat: np.ndarray, params: Params) -> np.ndarray:
    """Strong halos and dark debris -> filled blobs. Heuristic: check overlay.png."""
    median = np.median(flat)
    mad = np.median(np.abs(flat - median))
    if mad == 0:
        raise ValueError("MAD of the field is zero; cannot compute robust z-score")
    z = np.abs(flat - median) / (1.4826 * mad)
    mask = z > params.cancer_z
    mask = morphology.binary_closing(mask, morphology.disk(params.cancer_close_radius_px))
    mask = ndi.binary_fill_holes(mask)
    return morphology.remove_small_objects(mask, params.cancer_min_area_px)


# ---------- segmentation ----------
def load_model():
    import cellpose
    from cellpose import models

    print(f"cellpose version: {getattr(cellpose, '__version__', 'unknown')}")
    return models.CellposeModel(gpu=False)  # library default pretrained model


def segment_cellpose(model, scaled: np.ndarray, params: Params) -> np.ndarray:
    diameter_px = params.diameter_um / params.pixel_size_um
    masks, _, _ = model.eval(
        scaled,
        diameter=diameter_px,
        normalize=False,  # already normalised above
        flow_threshold=params.flow_threshold,
        cellprob_threshold=params.cellprob_threshold,
    )
    if masks.max() == 0:
        raise RuntimeError("Cellpose found no objects in a field; check preprocessing and diameter")
    return masks.astype(np.int32)


# ---------- filtering ----------
def touches_border(region, shape) -> bool:
    min_r, min_c, max_r, max_c = region.bbox
    return min_r == 0 or min_c == 0 or max_r == shape[0] or max_c == shape[1]


def filter_labels(labels: np.ndarray, cancer_mask: np.ndarray | None, params: Params
                  ) -> tuple[np.ndarray, dict[str, int]]:
    """Drop border-touching, tiny, and mostly-cancer labels; relabel sequentially.

    Operates on ONE field (borders are field borders, including the seam).
    """
    min_area_px = params.min_area_um2 / params.pixel_size_um**2
    removed = {"border": 0, "too_small": 0, "mostly_cancer": 0}
    out = np.zeros_like(labels)
    for region in measure.regionprops(labels):
        if touches_border(region, labels.shape):
            removed["border"] += 1
        elif region.area < min_area_px:
            removed["too_small"] += 1
        elif cancer_mask is not None and \
                cancer_mask[tuple(region.coords.T)].mean() > params.cancer_overlap_max:
            removed["mostly_cancer"] += 1
        else:
            out[tuple(region.coords.T)] = region.label
    out, _, _ = segmentation.relabel_sequential(out)
    return out, removed


def stitch_labels(per_field: list[np.ndarray], slices, shape) -> np.ndarray:
    """Place per-field label images in the full frame with globally unique labels."""
    full = np.zeros(shape, dtype=np.int32)
    offset = 0
    for labels, sl in zip(per_field, slices):
        full[sl] = np.where(labels > 0, labels + offset, 0)
        offset += int(labels.max())
    return full


def filter_reference(ref: np.ndarray, slices, params: Params) -> np.ndarray:
    """Apply the same per-field border / size rules to the manual annotation."""
    per_field = []
    for sl in slices:
        sub, _, _ = segmentation.relabel_sequential(ref[sl])
        per_field.append(filter_labels(sub, None, params)[0])
    return stitch_labels(per_field, slices, ref.shape)


# ---------- measurement ----------
def measure_cells(labels: np.ndarray, params: Params) -> pd.DataFrame:
    rows = []
    for region in measure.regionprops(labels):
        if region.minor_axis_length <= 0:
            raise ValueError(f"Label {region.label} has zero minor axis; degenerate mask")
        rows.append({
            "label": region.label,
            "area_um2": region.area * params.pixel_size_um**2,
            "aspect_ratio": region.major_axis_length / region.minor_axis_length,
        })
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio"])


def cancer_overlap_table(labels: np.ndarray, cancer_mask: np.ndarray, params: Params) -> pd.DataFrame:
    """QC: field index and fraction of each cell inside the cancer mask."""
    field_width = labels.shape[1] / params.n_fields
    rows = []
    for region in measure.regionprops(labels):
        rows.append({
            "label": region.label,
            "field": int(region.centroid[1] // field_width),
            "cancer_overlap_fraction": float(cancer_mask[tuple(region.coords.T)].mean()),
        })
    return pd.DataFrame(rows, columns=["label", "field", "cancer_overlap_fraction"])


# ---------- evaluation against manual annotation ----------
def iou_matrix(ref: np.ndarray, pred: np.ndarray) -> np.ndarray:
    """IoU between every reference (rows) and predicted (columns) label; both sequential."""
    n_ref, n_pred = int(ref.max()), int(pred.max())
    inter = np.bincount((ref.ravel().astype(np.int64) * (n_pred + 1) + pred.ravel()),
                        minlength=(n_ref + 1) * (n_pred + 1)).reshape(n_ref + 1, n_pred + 1)
    area_ref, area_pred = inter.sum(1), inter.sum(0)
    union = area_ref[:, None] + area_pred[None, :] - inter
    return (inter / np.maximum(union, 1))[1:, 1:]


def evaluate(pred: np.ndarray, ref: np.ndarray, cancer_mask: np.ndarray, params: Params,
             iou_min: float = 0.5) -> dict:
    """Both `pred` and `ref` must already be filtered and sequentially labelled."""
    if ref.max() == 0:
        raise ValueError("Annotation has no objects after border/size filtering")
    iou = iou_matrix(ref, pred)
    rows, cols = linear_sum_assignment(-iou)
    keep = iou[rows, cols] >= iou_min
    rows, cols = rows[keep], cols[keep]
    tp, n_ref, n_pred = len(rows), int(ref.max()), int(pred.max())

    ref_table = measure_cells(ref, params).set_index("label")
    ref_m = ref_table.loc[rows + 1]
    pred_m = measure_cells(pred, params).set_index("label").loc[cols + 1]

    ref_overlap = cancer_overlap_table(ref, cancer_mask, params).set_index("label")
    covered = ref_overlap.cancer_overlap_fraction.values > 0.1  # ref cell partly under cancer
    matched = np.zeros(n_ref, dtype=bool)
    matched[rows] = True

    def recall(mask: np.ndarray) -> float:
        return float(matched[mask].mean()) if mask.any() else float("nan")

    result = {
        "n_reference": n_ref, "n_predicted": n_pred, "tp": tp,
        "fp": n_pred - tp, "fn": n_ref - tp,
        "precision": tp / n_pred if n_pred else 0.0,
        "recall": tp / n_ref,
        "f1": 2 * tp / (n_ref + n_pred),
        "count_error_pct": 100 * (n_pred - n_ref) / n_ref,
        "median_area_ratio_pred_over_ref":
            float(np.median(pred_m.area_um2.values / ref_m.area_um2.values)) if tp else float("nan"),
        "median_abs_aspect_ratio_diff":
            float(np.median(np.abs(pred_m.aspect_ratio.values - ref_m.aspect_ratio.values)))
            if tp else float("nan"),
        "median_aspect_ratio_ref": float(ref_m.aspect_ratio.median()) if tp else float("nan"),
        "median_aspect_ratio_pred": float(pred_m.aspect_ratio.median()) if tp else float("nan"),
        "n_ref_under_cancer": int(covered.sum()),
        "recall_ref_under_cancer": recall(covered),
        "recall_ref_not_under_cancer": recall(~covered),
    }
    result["failures"] = failure_reasons(result)
    return result


def failure_reasons(r: dict) -> list[str]:
    """Pass/fail thresholds are my suggestions: adjust to your required precision."""
    reasons = []
    if r["f1"] < 0.7:
        reasons.append(f"F1@IoU0.5 = {r['f1']:.2f} < 0.70")
    if abs(r["count_error_pct"]) > 10:
        reasons.append(f"count error {r['count_error_pct']:.1f}% outside +-10%")
    ratio = r["median_area_ratio_pred_over_ref"]
    if not 0.9 <= ratio <= 1.1:
        reasons.append(f"median area ratio {ratio:.2f} outside 0.90-1.10")
    if r["median_abs_aspect_ratio_diff"] > 0.2:
        reasons.append(f"median |aspect ratio diff| {r['median_abs_aspect_ratio_diff']:.2f} > 0.20")
    under = r["recall_ref_under_cancer"]
    if r["n_ref_under_cancer"] >= 5 and under < 0.5:
        reasons.append(f"recall for cells under cancer cells = {under:.2f} < 0.50")
    return reasons


# ---------- outputs ----------
def save_overlay(scaled, labels, cancer_mask, path: Path, ref: np.ndarray | None = None) -> None:
    gray = np.clip(scaled, 0, 1)
    rgb = np.stack([gray] * 3, axis=-1)
    rgb[segmentation.find_boundaries(cancer_mask, mode="inner")] = (1, 0, 0)  # cancer: red
    rgb[segmentation.find_boundaries(labels, mode="inner")] = (0, 1, 0)        # prediction: green
    if ref is not None:
        rgb[segmentation.find_boundaries(ref, mode="inner")] = (1, 0, 1)       # annotation: magenta
    skio.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, default=Path("image.tif"))
    parser.add_argument("--annotation", type=Path, default=None)
    parser.add_argument("--diameter-um", type=float, default=Params.diameter_um)
    parser.add_argument("--cellprob-threshold", type=float, default=Params.cellprob_threshold)
    args = parser.parse_args()
    params = replace(Params(), diameter_um=args.diameter_um,
                     cellprob_threshold=args.cellprob_threshold)
    print(f"parameters: {params}")

    image = read_image(args.image, params)
    slices = field_slices(image.shape, params.n_fields)
    model = load_model()

    scaled_full = np.zeros(image.shape, dtype=np.float32)
    cancer_full = np.zeros(image.shape, dtype=bool)
    per_field_labels = []
    for i, sl in enumerate(slices):
        flat = flatten_background(image[sl], params)
        scaled_full[sl] = scale_percentiles(flat, params)
        cancer_full[sl] = detect_cancer_mask(flat, params)
        raw = segment_cellpose(model, scaled_full[sl], params)
        filtered, removed = filter_labels(raw, cancer_full[sl], params)
        print(f"field {i}: Cellpose objects {int(raw.max())}; removed {removed}; "
              f"kept {int(filtered.max())}")
        per_field_labels.append(filtered)

    labels = stitch_labels(per_field_labels, slices, image.shape)
    if labels.max() == 0:
        raise RuntimeError("All objects were filtered out")

    table = measure_cells(labels, params)
    qc = cancer_overlap_table(labels, cancer_full, params)
    tifffile.imwrite("labels.tif", labels.astype(np.uint16))  # same pixel grid as input
    table.to_csv("measurements.csv", index=False)
    qc.to_csv("measurements_qc.csv", index=False)
    tifffile.imwrite("preprocessed.tif", scaled_full)
    tifffile.imwrite("cancer_mask.tif", cancer_full.astype(np.uint8))

    ref = None
    if args.annotation is not None:
        ref = filter_reference(read_labels(args.annotation, image.shape), slices, params)
        result = evaluate(labels, ref, cancer_full, params)
        Path("evaluation.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        print("ANALYSIS FAILED" if result["failures"] else "Analysis passed the checks")
    save_overlay(scaled_full, labels, cancer_full, Path("overlay.png"), ref)


if __name__ == "__main__":
    main()
```

## What to run and what counts as failure

Run `python analyse_endothelial.py --annotation manual_labels.tif`. It counts as failed if any of these hold:
- F1 at IoU 0.5 is below 0.70.
- The count is off by more than 10%.
- The median area ratio is outside 0.90–1.10.
- The median aspect-ratio difference is above 0.2.
- Recall for annotated cells under cancer cells is below 0.5. This check applies only when there are at least 5 such cells.

These thresholds are my suggestions.

## Added risks from your answers

- **Hidden junctions.** Under a cancer cell the junctions may not be visible at all. Your annotation there rests on inference from the visible part of each cell. A model that matches it well would have to guess in the same way, so I wouldn't expect a generalist model to do this without fine-tuning.
- **Seam effects.** Cells that cross the seam between the fields are excluded. If you annotate a cell across the seam, it is cut and dropped from the evaluation too.
- **Cancer-cell bias in the area distribution.** If a mask under a cancer cell ends up equal to the cancer cell's outline, the area is wrong and the aspect ratio is close to 1. Compare the area distribution of cells with and without cancer overlap in `measurements_qc.csv`. A cluster of round, cancer-sized masks means this is happening.
- **Two fields are one test image.** They share the same sample and imaging session. A pass here doesn't show the script works on other sessions or cell densities. If you fine-tune, hold out one field for testing.
