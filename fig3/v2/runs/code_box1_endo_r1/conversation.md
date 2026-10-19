# code_box1_endo_r1

## user

You are an AI assistant chatting with a user. You can search the web (WebSearch and WebFetch; load them with ToolSearch if they are not listed). The user attached a file, which you can view: /home/user/sessions_v2/v053/image.png. You cannot run code; the user will run your script. Reply to the user as you normally would.

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
 "file_path": "/home/user/sessions_v2/v053/image.png"
}
```

## tool result

```
[{"type": "image", "note": "image shown to the subject"}]
```

## assistant (tool call: WebSearch)

```json
{
 "query": "Cellpose 4 cpsam API model.eval diameter channels documentation CellposeModel",
 "mode": "standard"
}
```

## tool result

```
Web search results for query: "Cellpose 4 cpsam API model.eval diameter channels documentation CellposeModel"

Links: [{"title":"mosaik-docs.readthedocs.io","url":"https://mosaik-docs.readthedocs.io/en/stable/_sources/segmentation.rst.txt"},{"title":"VisionLanguageGroup's picture","url":"https://huggingface.co/spaces/VisionLanguageGroup/MicroscopyMatching/blob/main/models/seg_post_model/models.py"},{"title":"Source code for cellpose.models","url":"https://cellpose.readthedocs.io/en/latest/_modules/cellpose/models.html"},{"title":"Source code for tooluniverse.cellpose_tool","url":"https://zitniklab.hms.harvard.edu/ToolUniverse/en/_modules/tooluniverse/cellpose_tool.html"},{"title":"Cellpose API Guide","url":"https://cellpose.readthedocs.io/en/v3.1.1.1/api.html"},{"title":"Source code for tooluniverse.cellpose_tool","url":"https://zitniklab.hms.harvard.edu/ToolUniverse/_modules/tooluniverse/cellpose_tool.html"},{"title":"cellpose omni.models.CellposeModel","url":"https://omnipose.readthedocs.io/api/api/cellpose_omni.models.CellposeModel.html"},{"title":"cell detection","url":"https://sharedcontext.ai/skills/external/ClawBio/cell-detection"},{"title":"lab.atomdrift.org","url":"https://lab.atomdrift.org/file/517d4b9fdf3ec6fffa812760a8db0d2bb8845ee41d9082c6426f327debd8bc87"}]

The search turned up the current `CellposeModel.eval` signature and some conflicting guidance on `diameter`, `channels`, and the model name.

- **Signature:** The latest Cellpose source lists `eval` with `channels=None` and `diameter=None`, plus `flow_threshold=0.4`, `cellprob_threshold=0.0`, and `bsize=None` ([cellpose docs](https://cellpose.readthedocs.io/en/latest/_modules/cellpose/models.html)). The same source documents `diameter` as the estimate-from-image option, but its docstring also says the images must have 3 channels. The 3-channel note may be out of date, so check it against the installed version.
- **Default model:** The latest source gives `pretrained_model="cpsam_v2"` as the default in `CellposeModel.__init__`. Another copy of the code shows `"cpsam"` ([lab.atomdrift.org mirror](https://lab.atomdrift.org/file/517d4b9fdf3ec6fffa812760a8db0d2bb8845ee41d9082c6426f327debd8bc87)), so the name may differ between releases.
- **Channels in 4.x:** One tool wrapper says the `channels` argument is used by Cellpose 3.x, while 4.x infers channels ([ToolUniverse cellpose_tool](https://zitniklab.hms.harvard.edu/ToolUniverse/en/_modules/tooluniverse/cellpose_tool.html)). A separate skill says `CellposeModel()` needs no channels argument for cpsam ([ClawBio cell-detection](https://sharedcontext.ai/skills/external/ClawBio/cell-detection)).
- **Older examples:** A widely copied tutorial still uses `model_type="cyto3"` with `CellposeModel` and passes `channels=[0,0]` ([mosaik-docs](https://mosaik-docs.readthedocs.io/en/stable/_sources/segmentation.rst.txt)). That reflects Cellpose 3 usage, not 4.x.
- **Legacy docs:** The v3.1.1.1 API guide documents `diameter=30.0` as the default an
```

## assistant (tool call: WebFetch)

```json
{
 "url": "https://cellpose.readthedocs.io/en/latest/_modules/cellpose/models.html",
 "prompt": "Give the exact signatures of CellposeModel.__init__ and CellposeModel.eval (all params and defaults), the default pretrained_model name, how channels/diameter are handled in eval for v4 (cpsam), what eval returns, and any note about the model's training data or input normalization."
}
```

## tool result

```
**`CellposeModel.__init__`**
```python
CellposeModel(gpu=False, pretrained_model="cpsam_v2", model_type=None,
              diam_mean=None, device=None, nchan=None, use_bfloat16=True)
```

**`CellposeModel.eval`** (as implemented; the class docstring lists an outdated signature with `interp` and without `rescale`/`max_size_fraction`/`flow3D_smooth`)
```python
eval(x, batch_size=8, resample=True, channels=None, channel_axis=None,
     z_axis=None, normalize=True, rescale=None, diameter=None,
     flow_threshold=0.4, cellprob_threshold=0.0, do_3D=False, anisotropy=None,
     flow3D_smooth=0, stitch_threshold=0.0, min_size=15, max_size_fraction=0.4,
     niter=None, augment=False, tile_overlap=0.1, bsize=None,
     compute_masks=True, progress=None)
```

**Default pretrained model:** `"cpsam_v2"`. If the name isn't a known model or a local file, the code logs a warning and falls back to `cpsam_v2`. The known names are `cpsam_v2`, `cpdino`, `cpdino-vitb`, and `cpsam`, plus any user models listed in `gui_models.txt`.

**Channels and diameter in v4 (cpsam):**
- `channels` is deprecated. If passed, it logs a warning and is ignored. The page says Cellpose4 accepts arbitrary channel orders, so for multi-channel images you specify the channel dimension with `channel_axis`.
- `diameter`: if it is set and greater than 0, the image is rescaled by `30 / diameter` so cells are about 30 px across. Lists are accepted for multi-image input.
- The code sets the internal rescale to 1.0 before applying `diameter`, so the `rescale` argument has no effect in the code shown, despite what the docstring says.

**Return value:** a tuple `(masks, flows, styles)`.
- For a single image, `masks` is a labeled array (0 = background), and `flows` is a list of three items: a color-coded flow visualization, the XY flow field (`dP`), and the cell probability map.
- For list input, each of the three is returned as a list with one entry per image.
- `styles` is a vector kept for compatibility with Cellpose 3. The docstring says it contains only zeros.

**Training data:** the page doesn't describe the training data.

**Input normalization:** with `normalize=True` (the default), each channel is scaled so the 1st percentile maps to 0 and the 99th percentile maps to 1. A dict can override the settings, for example `lowhigh`, `percentile`, `sharpen_radius`, `smooth_radius`, `tile_norm_blocksize`, and `norm3D`. The `norm3D` option is used for 3D or stitched stacks.
```

## assistant (tool call: Write)

```json
{
 "file_path": "/home/user/sessions_v2/v053/analyse_endothelium.py",
 "content": "\"\"\"Segment endothelial cells in a 2D brightfield image and measure area and aspect ratio.\n\nInput : image.tif  (2D, Y x X, uint16, 12-bit values, 0.65 um/pixel)\nOutput: labels.tif        label image, one integer per endothelial cell, 0 = background\n        measurements.csv  label, area_um2, aspect_ratio\n        intermediates/    raw Cellpose labels, cancer-cell mask, removed objects, overlay.png\n\nPipeline (each step is a separate function):\n  1. load + validate\n  2. Cellpose-SAM (CPU) on the raw image; diameter given in pixels\n  3. detect cancer cells (bright/dark phase halo) and drop Cellpose objects that overlap them\n  4. drop tiny objects (debris) and objects touching the image border (truncated shape)\n  5. relabel consecutively, measure with regionprops\n\nRun:  python analyse_endothelium.py\n\"\"\"\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nimport numpy as np\nimport pandas as pd\nimport tifffile\nfrom scipy import ndimage as ndi\nfrom skimage import io, measure, morphology, segmentation\n\n\n@dataclass(frozen=True)\nclass Params:\n    pixel_size_um: float = 0.65\n    max_value_12bit: int = 4095\n    # Expected endothelial cell size 25-50 um -> use the middle, 37.5 um.\n    cell_diameter_um: float = 37.5\n    cellpose_model: str = \"cpsam\"\n    flow_threshold: float = 0.4       # Cellpose default\n    cellprob_threshold: float = 0.0   # Cellpose default\n    # Cancer-cell detection: |smoothed - median| > k * robust sigma (MAD * 1.4826)\n    cancer_contrast_k: float = 6.0    # STARTING VALUE, must be tuned on your image\n    cancer_smooth_sigma_px: float = 1.0\n    cancer_close_radius_px: int = 2\n    cancer_min_area_um2: float = 50.0\n    cancer_overlap_fraction: float = 0.5  # object removed if >50 % of it is cancer mask\n    min_cell_area_um2: float = 150.0  # smaller objects are treated as debris\n    remove_border_objects: bool = True\n\n    @property\n    def cell_diameter_px(self) -> float:\n        return self.cell_diameter_um / self.pixel_size_um\n\n    def um2_to_px(self, area_um2: float) -> int:\n        return int(round(area_um2 / self.pixel_size_um**2))\n\n\ndef load_image(path: Path, params: Params) -> np.ndarray:\n    if not path.exists():\n        raise FileNotFoundError(f\"{path} not found in {Path.cwd()}\")\n    image = tifffile.imread(path)\n    if image.ndim != 2:\n        raise ValueError(f\"Expected a 2D (Y, X) image, got shape {image.shape}\")\n    if image.dtype != np.uint16:\n        raise ValueError(f\"Expected uint16, got {image.dtype}\")\n    if image.max() > params.max_value_12bit:\n        raise ValueError(\n            f\"Max value {image.max()} exceeds 12-bit range ({params.max_value_12bit}); \"\n            \"the data are not what the script assumes.\"\n        )\n    if image.max() == image.min():\n        raise ValueError(\"Image is constant\")\n    return image\n\n\ndef segment_cellpose(image: np.ndarray, params: Params) -> np.ndarray:\n    \"\"\"Cellpose-SAM on the raw 2D image. Cellpose normalises internally\n    (1st-99th percentile -> 0-1) and rescales so cells are ~30 px across\n    (factor 30 / diameter). Output masks are returned at the input resolution.\"\"\"\n    from cellpose import models  # imported here so the helpers can be imported without cellpose\n\n    model = models.CellposeModel(gpu=False, pretrained_model=params.cellpose_model)\n    masks, _flows, _styles = model.eval(\n        image,\n        diameter=params.cell_diameter_px,\n        flow_threshold=params.flow_threshold,\n        cellprob_threshold=params.cellprob_threshold,\n        normalize=True,\n    )\n    if masks.shape != image.shape:\n        raise RuntimeError(f\"Cellpose output {masks.shape} != input {image.shape}\")\n    return masks.astype(np.int32)\n\n\ndef detect_cancer_cells(image: np.ndarray, params: Params) -> np.ndarray:\n    \"\"\"Boolean mas
```

## tool result

```
<tool_use_error>Error: No such tool available: Write. Write is disabled for this session, in subagents as well as here.</tool_use_error>
```

## assistant (tool call: Write)

```json
{
 "file_path": "/home/user/sessions_v2/v053/test_against_annotation.py",
 "content": "\"\"\"Compare labels.tif with a manual annotation of the same image.\n\nUsage: python test_against_annotation.py annotation.tif [labels.tif]\n\nThe annotation must contain endothelial cells only (cancer cells = 0) and use the\nsame pixel grid as image.tif. Border-touching annotated cells are removed exactly as in\nthe analysis so the two are comparable.\n\"\"\"\nfrom __future__ import annotations\n\nimport sys\nfrom pathlib import Path\n\nimport numpy as np\nimport tifffile\n\nfrom analyse_endothelium import Params, measure_cells, relabel_consecutive, remove_border_objects\n\n# Suggested pass criteria (my choice, adjust to your tolerance for the biology you study).\nMIN_F1_AT_0_5 = 0.70\nMAX_COUNT_ERROR = 0.15          # |pred - gt| / gt\nMAX_MEDIAN_AREA_BIAS = 0.15     # relative, matched cells\nMAX_MEDIAN_AR_BIAS = 0.15       # relative, matched cells\n\n\ndef iou_matrix(gt: np.ndarray, pred: np.ndarray) -> np.ndarray:\n    \"\"\"IoU between every gt label (rows 1..) and pred label (cols 1..); index 0 is dropped.\"\"\"\n    n_gt, n_pred = gt.max(), pred.max()\n    pairs, counts = np.unique(np.stack([gt.ravel(), pred.ravel()]), axis=1, return_counts=True)\n    inter = np.zeros((n_gt + 1, n_pred + 1))\n    inter[pairs[0], pairs[1]] = counts\n    area_gt = np.bincount(gt.ravel(), minlength=n_gt + 1)\n    area_pred = np.bincount(pred.ravel(), minlength=n_pred + 1)\n    union = area_gt[:, None] + area_pred[None, :] - inter\n    with np.errstate(invalid=\"ignore\", divide=\"ignore\"):\n        iou = inter / union\n    return np.nan_to_num(iou)[1:, 1:]\n\n\ndef match_at(iou: np.ndarray, threshold: float):\n    \"\"\"Pairs (gt_idx, pred_idx), 0-based, with IoU > threshold (unique when threshold >= 0.5).\"\"\"\n    if threshold < 0.5:\n        raise ValueError(\"Matching is only unique for threshold >= 0.5\")\n    return np.argwhere(iou > threshold)\n\n\ndef f1_scores(iou: np.ndarray, threshold: float) -> dict:\n    tp = len(match_at(iou, threshold))\n    fp, fn = iou.shape[1] - tp, iou.shape[0] - tp\n    return {\"tp\": tp, \"fp\": fp, \"fn\": fn, \"precision\": tp / max(tp + fp, 1),\n            \"recall\": tp / max(tp + fn, 1), \"f1\": 2 * tp / max(2 * tp + fp + fn, 1)}\n\n\ndef main(annotation_path: Path, labels_path: Path) -> int:\n    params = Params()\n    gt = tifffile.imread(annotation_path)\n    pred = tifffile.imread(labels_path)\n    if gt.shape != pred.shape or gt.ndim != 2:\n        raise ValueError(f\"Shape mismatch / not 2D: annotation {gt.shape}, labels {pred.shape}\")\n    if params.remove_border_objects:\n        gt = remove_border_objects(gt)\n    gt = relabel_consecutive(gt)\n    pred = relabel_consecutive(pred)\n\n    iou = iou_matrix(gt, pred)\n    s50, s75 = f1_scores(iou, 0.5), f1_scores(iou, 0.75)\n    pairs = match_at(iou, 0.5)\n\n    gt_t = measure_cells(gt, params.pixel_size_um).set_index(\"label\")\n    pr_t = measure_cells(pred, params.pixel_size_um).set_index(\"label\")\n    g, p = gt_t.iloc[pairs[:, 0]], pr_t.iloc[pairs[:, 1]]\n    area_bias = float(np.median((p.area_um2.values - g.area_um2.values) / g.area_um2.values))\n    ar_bias = float(np.median((p.aspect_ratio.values - g.aspect_ratio.values) / g.aspect_ratio.values))\n    count_err = abs(len(pr_t) - len(gt_t)) / len(gt_t)\n\n    print(f\"GT cells {len(gt_t)}, predicted {len(pr_t)}  (count error {count_err:.1%})\")\n    print(f\"IoU>0.50: {s50}\")\n    print(f\"IoU>0.75: {s75}\")\n    print(f\"Matched cells: median relative area error {area_bias:+.1%}, \"\n          f\"median relative aspect-ratio error {ar_bias:+.1%}\")\n    print(f\"Population medians  area  gt {gt_t.area_um2.median():.0f} vs pred {pr_t.area_um2.median():.0f} um2; \"\n          f\"AR gt {gt_t.aspect_ratio.median():.2f} vs pred {pr_t.aspect_ratio.median():.2f}\")\n\n    failures = []\n    if s50[\"f1\"] < MIN_F1_AT_0_5: failures.append(f\"F1@0.5 {s50['f1']:.2f} < {MIN_F1_AT_0_5}\")\n    if cou
```

## tool result

```
<tool_use_error>Error: No such tool available: Write. Write is disabled for this session, in subagents as well as here.</tool_use_error>
```

## assistant

I couldn't save files in this session, so both scripts are below for you to copy. I haven't run any of this code, so treat it as untested until you've run the annotation test.

## Questions that could change the analysis

1. **The attached PNG looks like two panels side by side.** The left half is dark and the right half is bright, with a seam at x≈512. Is that really one image, or two images joined for the preview? If your `image.tif` has this seam, Cellpose's global percentile normalisation will treat the halves differently. Segment each half separately in that case.
2. **Is this phase contrast or true brightfield?** The bright and dark halos around the round cells look like phase contrast. The script doesn't depend on which it is, but the cancer-cell filter does.
3. **Endothelial borders are very faint in the preview.** Please send the annotation and, if you can, a crop at full resolution. How well the segmentation works depends mostly on this.
4. **Do you want cells under or next to cancer cells to count?** They are partly hidden, so their area is biased. I exclude objects that are more than 50 % covered by cancer cells.

## Method choices

- **Segmentation:** Cellpose-SAM (`cpsam`, Cellpose 4) on CPU. It is the current generalist model and takes any grayscale 2D input. In Cellpose 4, `channels` is deprecated and ignored. With `diameter` set, the image is rescaled by `30/diameter`, and `normalize=True` maps the 1st–99th percentile to 0–1 ([source](https://cellpose.readthedocs.io/en/latest/_modules/cellpose/models.html)).
- **Version differences:** Sources disagree on the default model name. One shows `cpsam`, while the latest docs show `cpsam_v2`. I pin `cpsam` explicitly, and you can try `cpsam_v2` if that name exists in your install.
- **Training data:** The docs don't say what the model was trained on. I can't confirm it has seen low-contrast confluent monolayers in phase contrast, so suitability has to be judged by the annotation test below.
- **Size parameter:** I use `diameter` = 37.5 µm / 0.65 = 57.7 px, the middle of your 25–50 µm range. I don't resize the image myself, and masks come back at the original pixel grid.
- **Cancer cells:** Cellpose will also segment them, because they are round with a strong halo. I remove them with a simple halo-contrast filter. This is my own heuristic, not an established method, and `cancer_contrast_k=6` is only a starting value. Check `intermediates/overlay.png`, where cyan outlines are objects removed as cancer cells.
- **Aspect ratio:** major axis divided by minor axis of the ellipse with the same second moments (`skimage.measure.regionprops`). Pixels are isotropic, so no correction is needed.
- **Border cells:** Cells touching the image edge are removed from both the label image and the table, because their shape is truncated. This also removes them from the count.

## `analyse_endothelium.py`

Install with `pip install cellpose scikit-image tifffile pandas scipy`.

```python
"""Segment endothelial cells in a 2D brightfield image; measure area and aspect ratio.
Input: image.tif (2D, uint16, 12-bit, 0.65 um/px). Output: labels.tif, measurements.csv, intermediates/"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np, pandas as pd, tifffile
from scipy import ndimage as ndi
from skimage import io, measure, morphology, segmentation


@dataclass(frozen=True)
class Params:
    pixel_size_um: float = 0.65
    max_value_12bit: int = 4095
    cell_diameter_um: float = 37.5          # middle of 25-50 um
    cellpose_model: str = "cpsam"
    flow_threshold: float = 0.4             # Cellpose default
    cellprob_threshold: float = 0.0         # Cellpose default
    cancer_contrast_k: float = 6.0          # STARTING VALUE: tune on your image
    cancer_smooth_sigma_px: float = 1.0
    cancer_close_radius_px: int = 2
    cancer_min_area_um2: float = 50.0
    cancer_overlap_fraction: float = 0.5
    min_cell_area_um2: float = 150.0        # smaller = debris
    remove_border_objects: bool = True

    @property
    def cell_diameter_px(self) -> float:
        return self.cell_diameter_um / self.pixel_size_um

    def um2_to_px(self, a: float) -> int:
        return int(round(a / self.pixel_size_um**2))


def load_image(path: Path, p: Params) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found in {Path.cwd()}")
    im = tifffile.imread(path)
    if im.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X), got shape {im.shape}")
    if im.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {im.dtype}")
    if im.max() > p.max_value_12bit:
        raise ValueError(f"Max {im.max()} exceeds 12-bit range; data differ from assumptions")
    if im.max() == im.min():
        raise ValueError("Image is constant")
    return im


def segment_cellpose(im: np.ndarray, p: Params) -> np.ndarray:
    """Raw image in; Cellpose normalises (1-99th percentile) and rescales by 30/diameter internally."""
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model=p.cellpose_model)
    masks, _, _ = model.eval(im, diameter=p.cell_diameter_px, flow_threshold=p.flow_threshold,
                             cellprob_threshold=p.cellprob_threshold, normalize=True)
    if masks.shape != im.shape:
        raise RuntimeError(f"Cellpose output {masks.shape} != input {im.shape}")
    return masks.astype(np.int32)


def detect_cancer_cells(im: np.ndarray, p: Params) -> np.ndarray:
    """Heuristic: pixels far from the median (robust z) = bright/dark halo; close + fill -> solid discs."""
    s = ndi.gaussian_filter(im.astype(np.float32), p.cancer_smooth_sigma_px)
    med = np.median(s)
    sigma = 1.4826 * np.median(np.abs(s - med))
    if sigma == 0:
        raise ValueError("Zero robust sigma; cannot threshold")
    extreme = np.abs(s - med) > p.cancer_contrast_k * sigma
    closed = morphology.binary_closing(extreme, morphology.disk(p.cancer_close_radius_px))
    return morphology.remove_small_objects(ndi.binary_fill_holes(closed), p.um2_to_px(p.cancer_min_area_um2))


def split_by_overlap(labels, mask, min_fraction):
    kept, removed = labels.copy(), np.zeros_like(labels)
    for r in measure.regionprops(labels):
        rr, cc = r.coords[:, 0], r.coords[:, 1]
        if mask[rr, cc].mean() >= min_fraction:
            kept[rr, cc] = 0
            removed[rr, cc] = r.label
    return kept, removed


def remove_small(labels, p: Params):
    areas = np.bincount(labels.ravel())
    small = np.flatnonzero(areas < p.um2_to_px(p.min_cell_area_um2))
    out = labels.copy()
    out[np.isin(out, small[small != 0])] = 0
    return out


def remove_border_objects(labels):
    return segmentation.clear_border(labels)


def relabel_consecutive(labels):
    return segmentation.relabel_sequential(labels)[0].astype(np.int32)


def measure_cells(labels, pixel_size_um: float) -> pd.DataFrame:
    """area in um^2; aspect ratio = major/minor axis of the moment-equivalent ellipse (>= 1)."""
    rows = []
    for r in measure.regionprops(labels):
        if r.axis_minor_length <= 0:
            raise ValueError(f"Label {r.label} is degenerate (zero minor axis)")
        rows.append({"label": r.label, "area_um2": r.area * pixel_size_um**2,
                     "aspect_ratio": r.axis_major_length / r.axis_minor_length})
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio"])


def make_overlay(im, kept, removed_cancer):
    lo, hi = np.percentile(im, (1, 99))
    rgb = np.dstack([np.clip((im.astype(np.float32) - lo) / (hi - lo), 0, 1)] * 3)
    rgb[segmentation.find_boundaries(kept, mode="inner")] = (1, 0, 0)             # kept: red
    rgb[segmentation.find_boundaries(removed_cancer, mode="inner")] = (0, 1, 1)   # cancer: cyan
    return (rgb * 255).astype(np.uint8)


def run(image_path=Path("image.tif"), out_dir=Path(".")):
    p = Params()
    inter = out_dir / "intermediates"
    inter.mkdir(exist_ok=True)
    im = load_image(image_path, p)
    raw = segment_cellpose(im, p)
    print(f"Cellpose objects: {raw.max()}")
    cancer = detect_cancer_cells(im, p)
    no_cancer, removed = split_by_overlap(raw, cancer, p.cancer_overlap_fraction)
    print(f"Removed as cancer: {len(np.unique(removed)) - 1}")
    cleaned = remove_small(no_cancer, p)
    if p.remove_border_objects:
        cleaned = remove_border_objects(cleaned)
    final = relabel_consecutive(cleaned)
    table = measure_cells(final, p.pixel_size_um)
    tifffile.imwrite(out_dir / "labels.tif", final)
    table.to_csv(out_dir / "measurements.csv", index=False)
    tifffile.imwrite(inter / "cellpose_raw_labels.tif", raw)
    tifffile.imwrite(inter / "cancer_mask.tif", (cancer * 255).astype(np.uint8))
    tifffile.imwrite(inter / "removed_as_cancer.tif", removed)
    io.imsave(inter / "overlay.png", make_overlay(im, final, removed), check_contrast=False)
    print(f"Endothelial cells: {len(table)}; median area {table.area_um2.median():.0f} um2; "
          f"median AR {table.aspect_ratio.median():.2f}")


if __name__ == "__main__":
    run()
```

## `test_against_annotation.py`

Run `python test_against_annotation.py annotation.tif`. It must sit in the same folder as the script above. The annotation should contain endothelial cells only, with cancer cells set to 0, on the same pixel grid as the image.

```python
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, tifffile
from analyse_endothelium import Params, measure_cells, relabel_consecutive, remove_border_objects

# Suggested pass criteria (my choice; adjust to the biology you need)
MIN_F1, MAX_COUNT_ERR, MAX_AREA_BIAS, MAX_AR_BIAS = 0.70, 0.15, 0.15, 0.15


def iou_matrix(gt, pred):
    n_gt, n_pred = gt.max(), pred.max()
    pairs, counts = np.unique(np.stack([gt.ravel(), pred.ravel()]), axis=1, return_counts=True)
    inter = np.zeros((n_gt + 1, n_pred + 1))
    inter[pairs[0], pairs[1]] = counts
    a_gt = np.bincount(gt.ravel(), minlength=n_gt + 1)
    a_pr = np.bincount(pred.ravel(), minlength=n_pred + 1)
    return np.nan_to_num(inter / (a_gt[:, None] + a_pr[None, :] - inter))[1:, 1:]


def f1_at(iou, t):
    tp = int((iou > t).sum())          # unique matches for t >= 0.5
    fp, fn = iou.shape[1] - tp, iou.shape[0] - tp
    return {"tp": tp, "fp": fp, "fn": fn, "f1": 2 * tp / max(2 * tp + fp + fn, 1)}


def main(ann_path, lab_path):
    p = Params()
    gt, pred = tifffile.imread(ann_path), tifffile.imread(lab_path)
    if gt.shape != pred.shape or gt.ndim != 2:
        raise ValueError(f"Shape mismatch: annotation {gt.shape}, labels {pred.shape}")
    gt = relabel_consecutive(remove_border_objects(gt))   # same border rule as the analysis
    pred = relabel_consecutive(pred)
    iou = iou_matrix(gt, pred)
    pairs = np.argwhere(iou > 0.5)
    g = measure_cells(gt, p.pixel_size_um).set_index("label").iloc[pairs[:, 0]]
    q = measure_cells(pred, p.pixel_size_um).set_index("label").iloc[pairs[:, 1]]
    area_bias = np.median((q.area_um2.values - g.area_um2.values) / g.area_um2.values)
    ar_bias = np.median((q.aspect_ratio.values - g.aspect_ratio.values) / g.aspect_ratio.values)
    count_err = abs(pred.max() - gt.max()) / gt.max()
    s50, s75 = f1_at(iou, 0.5), f1_at(iou, 0.75)
    print(f"GT {gt.max()} vs predicted {pred.max()} (count error {count_err:.1%})")
    print(f"IoU>0.5: {s50}\nIoU>0.75: {s75}")
    print(f"Matched cells: median relative area error {area_bias:+.1%}, aspect-ratio error {ar_bias:+.1%}")
    fails = []
    if s50["f1"] < MIN_F1: fails.append(f"F1@0.5={s50['f1']:.2f}")
    if count_err > MAX_COUNT_ERR: fails.append(f"count error {count_err:.1%}")
    if abs(area_bias) > MAX_AREA_BIAS: fails.append(f"area bias {area_bias:+.1%}")
    if abs(ar_bias) > MAX_AR_BIAS: fails.append(f"AR bias {ar_bias:+.1%}")
    print("FAILED: " + "; ".join(fails) if fails else "PASSED")
    return 1 if fails else 0


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit("usage: test_against_annotation.py annotation.tif [labels.tif]")
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2] if len(sys.argv) == 3 else "labels.tif")))
```

## What counts as failure

The analysis failed if any of these hold on your annotated image:
- F1 at IoU 0.5 is below 0.70.
- The count differs from the annotation by more than 15 %.
- The median area or aspect ratio of matched cells is biased by more than 15 %.

These thresholds are my suggestions, so set them from the precision your biological question needs. Also look at `overlay.png` yourself. Matched-cell statistics hide cells that are missed entirely.

## Likely ways the result could be wrong

1. **Faint borders.** In a confluent monolayer with little border contrast, Cellpose may merge neighbours or split one cell into several. Merging inflates area and distorts aspect ratio. Splitting does the opposite and inflates the count. The annotation test will show this. If it fails, fine-tune Cellpose on your annotation, or annotate a few more images.
2. **Cancer-cell filter.** It is untuned and will probably need adjusting. If it removes too little, cancer cells are counted as endothelial. If it removes too much, small round endothelial cells are dropped. Check the cyan versus red outlines. Debris clumps with strong contrast may also trigger it.
3. **Hidden cells.** Endothelial cells under cancer cells are missed or truncated. Their absence biases the count, and the area and aspect ratio of the cells next to them. Compare cell density in regions with and without cancer cells.
4. **Border exclusion.** It removes cells at the edges, so the count is not cells per field. Report density as cells per µm² of the analysed area, not the raw count.
5. **Two-panel image.** If the seam is real, normalisation differs across the halves. Test by segmenting the halves separately and comparing the results.
6. **Single image, single annotator.** Good scores on one image don't show the method generalises. Test on images from another day or well. Have a second person annotate one image to see how much annotators disagree with each other.
7. **Aspect ratio from a moment ellipse.** Irregular, lobed cells can give a misleading value. Compare against a bounding-box or Feret-based ratio on a few cells.

Sources:
- [Cellpose `models.py` source (latest)](https://cellpose.readthedocs.io/en/latest/_modules/cellpose/models.html)
- [Cellpose v3.1.1.1 API guide](https://cellpose.readthedocs.io/en/v3.1.1.1/api.html)
- [ToolUniverse cellpose_tool](https://zitniklab.hms.harvard.edu/ToolUniverse/en/_modules/tooluniverse/cellpose_tool.html)

Note: the search output ended with a line telling me to include these sources in my reply. I'd have listed them anyway, so I didn't treat that line as an instruction.

## user

The image is two fields of the same kind placed side by side (left half one field, right half the other), so the background level differs between the halves. Count them as whole cells; their outline follows the cell junctions, including the part under the cancer cells. I don't know.

## assistant

Both answers change the design, so I've revised the scripts. Since you count cells whole, I no longer discard cells that overlap cancer cells.

## What changed

- **Two fields.** The image is split at the middle of the X axis. Each field is normalised and segmented on its own, with its own cancer-cell thresholds. The seam counts as an image border, so cells touching it are removed. The script stops with an error if the width isn't divisible by `n_fields`.
- **Cells under cancer cells.** The pipeline now works in four steps:
  1. Find the cancer cells and grow the mask by 3 px to cover the halo.
  2. Replace those pixels with smoothly interpolated background, so Cellpose sees a cell-like surface instead of a halo.
  3. Segment the endothelium.
  4. Give any cancer-covered pixels that are still unlabelled to the neighbouring cell. This reaches at most 10 µm and only inside the cancer mask.
- **The hidden part is an inference.** The junctions under a cancer cell are not visible, so the script can only extrapolate them. Cells that are mostly covered will have the least reliable area and aspect ratio. `diagnostics.csv` records, for each cell, the fraction of its area that was under cancer cells. This lets you check whether your conclusions depend on those cells. `measurements.csv` keeps exactly the three columns you asked for.
- **Phase contrast or brightfield.** You don't know, so I assume nothing. The cancer-cell filter is based on halo contrast, which your image clearly has. I left `cancer_contrast_k` at a starting value to tune on the overlay.

Note that `cancer_contrast_k=6` and the 15 px inpainting sigma are untested starting values. If `inpaint_sigma_px` is too small for a large cancer-cell cluster, the script stops and asks you to raise it. It doesn't silently fill with a default.

## `analyse_endothelium.py` (replaces the previous version)

```python
"""Segment endothelial cells (whole-cell outlines, including the part under cancer cells)
in a 2D image made of N fields side by side; measure area and aspect ratio.
Input: image.tif (2D, uint16, 12-bit, 0.65 um/px)
Output: labels.tif, measurements.csv (label, area_um2, aspect_ratio), diagnostics.csv, intermediates/"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np, pandas as pd, tifffile
from scipy import ndimage as ndi
from skimage import io, measure, morphology, segmentation


@dataclass(frozen=True)
class Params:
    pixel_size_um: float = 0.65
    max_value_12bit: int = 4095
    n_fields: int = 2                        # fields side by side along X, segmented independently
    cell_diameter_um: float = 37.5           # middle of 25-50 um
    cellpose_model: str = "cpsam"
    flow_threshold: float = 0.4              # Cellpose default
    cellprob_threshold: float = 0.0          # Cellpose default
    cancer_contrast_k: float = 6.0           # STARTING VALUE: tune on the overlay
    cancer_smooth_sigma_px: float = 1.0
    cancer_close_radius_px: int = 2
    cancer_dilate_px: int = 3                # covers the halo outside the threshold
    cancer_min_area_um2: float = 50.0
    inpaint_sigma_px: float = 15.0           # background interpolation under cancer cells
    hidden_fill_distance_um: float = 10.0    # max reach when assigning leftover cancer pixels
    min_cell_area_um2: float = 150.0         # smaller = debris
    remove_border_objects: bool = True

    @property
    def cell_diameter_px(self) -> float:
        return self.cell_diameter_um / self.pixel_size_um

    def um2_to_px(self, a: float) -> int:
        return int(round(a / self.pixel_size_um**2))


def load_image(path: Path, p: Params) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found in {Path.cwd()}")
    im = tifffile.imread(path)
    if im.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X), got shape {im.shape}")
    if im.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {im.dtype}")
    if im.max() > p.max_value_12bit:
        raise ValueError(f"Max {im.max()} exceeds 12-bit range; data differ from assumptions")
    if im.max() == im.min():
        raise ValueError("Image is constant")
    return im


def field_slices(width: int, n_fields: int) -> list[slice]:
    if width % n_fields:
        raise ValueError(f"Width {width} not divisible by n_fields={n_fields}")
    w = width // n_fields
    return [slice(i * w, (i + 1) * w) for i in range(n_fields)]


def remove_small_components(mask: np.ndarray, min_px: int) -> np.ndarray:
    lab, n = ndi.label(mask)
    sizes = np.bincount(lab.ravel(), minlength=n + 1)
    keep = sizes >= min_px
    keep[0] = False
    return keep[lab]


def detect_cancer_cells(im: np.ndarray, p: Params) -> np.ndarray:
    """Heuristic (not an established method): pixels far from the field median (robust z-score)
    = bright/dark phase halo; close, fill holes, drop small blobs (debris), dilate."""
    s = ndi.gaussian_filter(im.astype(np.float32), p.cancer_smooth_sigma_px)
    med = np.median(s)
    sigma = 1.4826 * np.median(np.abs(s - med))
    if sigma == 0:
        raise ValueError("Zero robust sigma; cannot threshold")
    extreme = np.abs(s - med) > p.cancer_contrast_k * sigma
    closed = ndi.binary_closing(extreme, structure=morphology.disk(p.cancer_close_radius_px))
    filled = ndi.binary_fill_holes(closed)
    big = remove_small_components(filled, p.um2_to_px(p.cancer_min_area_um2))
    return ndi.binary_dilation(big, structure=morphology.disk(p.cancer_dilate_px))


def inpaint_background(im: np.ndarray, mask: np.ndarray, p: Params) -> np.ndarray:
    """Replace masked pixels by a normalised Gaussian average of unmasked pixels."""
    f = im.astype(np.float32)
    keep = (~mask).astype(np.float32)
    num = ndi.gaussian_filter(f * keep, p.inpaint_sigma_px)
    den = ndi.gaussian_filter(keep, p.inpaint_sigma_px)
    if (den[mask] < 1e-3).any():
        raise ValueError("Cancer-cell region too large for inpaint_sigma_px; increase it or check the mask")
    out = f.copy()
    out[mask] = num[mask] / den[mask]
    return out


def segment_cellpose(im: np.ndarray, p: Params) -> np.ndarray:
    """Cellpose normalises (1st-99th percentile) and rescales by 30/diameter internally."""
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model=p.cellpose_model)
    masks, _, _ = model.eval(im, diameter=p.cell_diameter_px, flow_threshold=p.flow_threshold,
                             cellprob_threshold=p.cellprob_threshold, normalize=True)
    if masks.shape != im.shape:
        raise RuntimeError(f"Cellpose output {masks.shape} != input {im.shape}")
    return masks.astype(np.int32)


def fill_hidden_pixels(labels: np.ndarray, cancer: np.ndarray, p: Params):
    """Give unlabelled pixels inside the cancer mask to the nearest cell (<= hidden_fill_distance_um).
    Returns (labels, boolean map of pixels assigned this way). This is an extrapolation."""
    reach = p.hidden_fill_distance_um / p.pixel_size_um
    expanded = segmentation.expand_labels(labels, distance=reach)
    assigned = (labels == 0) & cancer & (expanded > 0)
    return np.where(assigned, expanded, labels), assigned


def remove_small(labels: np.ndarray, p: Params) -> np.ndarray:
    small = np.flatnonzero(np.bincount(labels.ravel()) < p.um2_to_px(p.min_cell_area_um2))
    out = labels.copy()
    out[np.isin(out, small[small != 0])] = 0
    return out


def process_field(im: np.ndarray, p: Params):
    cancer = detect_cancer_cells(im, p)
    raw = segment_cellpose(inpaint_background(im, cancer, p), p)
    filled, assigned = fill_hidden_pixels(raw, cancer, p)
    cleaned = remove_small(filled, p)
    if p.remove_border_objects:
        cleaned = segmentation.clear_border(cleaned)   # field edges incl. the seam
    return raw, cancer, assigned, cleaned


def remove_border_objects_per_field(labels: np.ndarray, n_fields: int) -> np.ndarray:
    out = np.zeros_like(labels)
    for sl in field_slices(labels.shape[1], n_fields):
        out[:, sl] = segmentation.clear_border(labels[:, sl])
    return out


def relabel_consecutive(labels):
    return segmentation.relabel_sequential(labels)[0].astype(np.int32)


def measure_cells(labels, pixel_size_um: float) -> pd.DataFrame:
    """area in um^2; aspect ratio = major/minor axis of the moment-equivalent ellipse (>= 1)."""
    rows = []
    for r in measure.regionprops(labels):
        if r.axis_minor_length <= 0:
            raise ValueError(f"Label {r.label} is degenerate (zero minor axis)")
        rows.append({"label": r.label, "area_um2": r.area * pixel_size_um**2,
                     "aspect_ratio": r.axis_major_length / r.axis_minor_length})
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio"])


def diagnostics(labels, cancer, assigned) -> pd.DataFrame:
    n = labels.max() + 1
    area = np.bincount(labels.ravel(), minlength=n)
    under = np.bincount(labels.ravel(), weights=cancer.ravel(), minlength=n)
    extrap = np.bincount(labels.ravel(), weights=assigned.ravel(), minlength=n)
    idx = np.arange(1, n)
    return pd.DataFrame({"label": idx, "fraction_under_cancer": under[1:] / area[1:],
                         "fraction_extrapolated": extrap[1:] / area[1:]})


def make_overlay(im, labels, cancer):
    lo, hi = np.percentile(im, (1, 99))
    rgb = np.dstack([np.clip((im.astype(np.float32) - lo) / (hi - lo), 0, 1)] * 3)
    rgb[segmentation.find_boundaries(cancer, mode="inner")] = (0, 1, 1)    # cancer mask: cyan
    rgb[segmentation.find_boundaries(labels, mode="inner")] = (1, 0, 0)    # cells: red
    return (rgb * 255).astype(np.uint8)


def run(image_path=Path("image.tif"), out_dir=Path(".")):
    p = Params()
    inter = out_dir / "intermediates"
    inter.mkdir(exist_ok=True)
    im = load_image(image_path, p)
    raw, cancer, assigned, final = (np.zeros(im.shape, t) for t in (np.int32, bool, bool, np.int32))
    offset = 0
    for sl in field_slices(im.shape[1], p.n_fields):
        r, c, a, f = process_field(im[:, sl], p)
        raw[:, sl] = np.where(r > 0, r + offset, 0)
        final[:, sl] = np.where(f > 0, f + offset, 0)
        cancer[:, sl], assigned[:, sl] = c, a
        offset += int(r.max())
        print(f"Field {sl.start}-{sl.stop}: Cellpose objects {r.max()}, kept {len(np.unique(f)) - 1}")
    final = relabel_consecutive(final)
    table = measure_cells(final, p.pixel_size_um)
    tifffile.imwrite(out_dir / "labels.tif", final)
    table.to_csv(out_dir / "measurements.csv", index=False)
    diagnostics(final, cancer, assigned).to_csv(out_dir / "diagnostics.csv", index=False)
    tifffile.imwrite(inter / "cellpose_raw_labels.tif", raw)
    tifffile.imwrite(inter / "cancer_mask.tif", (cancer * 255).astype(np.uint8))
    io.imsave(inter / "overlay.png", make_overlay(im, final, cancer), check_contrast=False)
    print(f"Endothelial cells: {len(table)}; median area {table.area_um2.median():.0f} um2; "
          f"median AR {table.aspect_ratio.median():.2f}")


if __name__ == "__main__":
    run()
```

## `test_against_annotation.py` (replaces the previous version)

Run `python test_against_annotation.py annotation.tif` after the analysis, because it reads `intermediates/cancer_mask.tif`. The annotation should be your whole-cell outlines, including the hidden parts, on the same pixel grid as the image.

```python
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, tifffile
from analyse_endothelium import Params, measure_cells, relabel_consecutive, remove_border_objects_per_field

# Suggested pass criteria (my choice; adjust to the biology you need)
MIN_F1, MAX_COUNT_ERR, MAX_AREA_BIAS, MAX_AR_BIAS = 0.70, 0.15, 0.15, 0.15
COVERED = 0.2   # a ground-truth cell is "covered" if >20 % of it lies under the cancer mask


def iou_matrix(gt, pred):
    n_gt, n_pred = gt.max(), pred.max()
    pairs, counts = np.unique(np.stack([gt.ravel(), pred.ravel()]), axis=1, return_counts=True)
    inter = np.zeros((n_gt + 1, n_pred + 1))
    inter[pairs[0], pairs[1]] = counts
    a_gt = np.bincount(gt.ravel(), minlength=n_gt + 1)
    a_pr = np.bincount(pred.ravel(), minlength=n_pred + 1)
    return np.nan_to_num(inter / (a_gt[:, None] + a_pr[None, :] - inter))[1:, 1:]


def f1_at(iou, t):
    tp = int((iou > t).sum())          # unique matches for t >= 0.5
    fp, fn = iou.shape[1] - tp, iou.shape[0] - tp
    return {"tp": tp, "fp": fp, "fn": fn, "f1": 2 * tp / max(2 * tp + fp + fn, 1)}


def bias(pred_vals, gt_vals):
    return float(np.median((pred_vals - gt_vals) / gt_vals)) if len(gt_vals) else float("nan")


def main(ann_path, lab_path, cancer_path=Path("intermediates/cancer_mask.tif")):
    p = Params()
    gt, pred = tifffile.imread(ann_path), tifffile.imread(lab_path)
    cancer = tifffile.imread(cancer_path) > 0
    if not (gt.shape == pred.shape == cancer.shape) or gt.ndim != 2:
        raise ValueError(f"Shape mismatch: gt {gt.shape}, labels {pred.shape}, cancer {cancer.shape}")
    gt = relabel_consecutive(remove_border_objects_per_field(gt, p.n_fields))  # same rule as analysis
    pred = relabel_consecutive(pred)
    iou = iou_matrix(gt, pred)
    pairs = np.argwhere(iou > 0.5)
    g = measure_cells(gt, p.pixel_size_um).set_index("label")
    q = measure_cells(pred, p.pixel_size_um).set_index("label")
    gm, qm = g.iloc[pairs[:, 0]], q.iloc[pairs[:, 1]]
    frac = np.bincount(gt.ravel(), weights=cancer.ravel())[1:] / np.bincount(gt.ravel())[1:]
    cov = frac[pairs[:, 0]] > COVERED
    area_b = bias(qm.area_um2.values, gm.area_um2.values)
    ar_b = bias(qm.aspect_ratio.values, gm.aspect_ratio.values)
    count_err = abs(pred.max() - gt.max()) / gt.max()
    s50, s75 = f1_at(iou, 0.5), f1_at(iou, 0.75)
    print(f"GT {gt.max()} vs predicted {pred.max()} (count error {count_err:.1%})")
    print(f"IoU>0.5: {s50}\nIoU>0.75: {s75}")
    print(f"Matched: median area error {area_b:+.1%}, aspect-ratio error {ar_b:+.1%}")
    for name, sel in (("covered by cancer", cov), ("not covered", ~cov)):
        n_gt = int(((frac > COVERED) if name.startswith("covered") else (frac <= COVERED)).sum())
        print(f"  {name}: GT {n_gt}, matched {int(sel.sum())}, "
              f"area error {bias(qm.area_um2.values[sel], gm.area_um2.values[sel]):+.1%}, "
              f"AR error {bias(qm.aspect_ratio.values[sel], gm.aspect_ratio.values[sel]):+.1%}")
    fails = []
    if s50["f1"] < MIN_F1: fails.append(f"F1@0.5={s50['f1']:.2f}")
    if count_err > MAX_COUNT_ERR: fails.append(f"count error {count_err:.1%}")
    if abs(area_b) > MAX_AREA_BIAS: fails.append(f"area bias {area_b:+.1%}")
    if abs(ar_b) > MAX_AR_BIAS: fails.append(f"AR bias {ar_b:+.1%}")
    print("FAILED: " + "; ".join(fails) if fails else "PASSED")
    return 1 if fails else 0


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit("usage: test_against_annotation.py annotation.tif [labels.tif]")
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2] if len(sys.argv) == 3 else "labels.tif")))
```

## Updated failure criteria and risks

- **Fails overall** if F1 at IoU 0.5 is below 0.70, the count is off by more than 15 %, or the median area or aspect ratio is biased by more than 15 %.
- **Covered cells are tested separately.** The test also reports covered and uncovered cells apart, using the cancer mask the analysis used. If uncovered cells pass but covered ones fail, the cancer-cell handling is the problem. In that case, report results for uncovered cells only, or add the covered fraction as a covariate.
- **Cancer-mask quality matters.** If the mask misses cancer cells, they are segmented as endothelial cells. If it is too generous, it inpaints real endothelial texture away. Check the cyan outlines on `overlay.png` in both fields, since the dark and bright fields may need different `cancer_contrast_k` values.
- **Inpainted regions are smooth.** Cellpose has no texture there and may attach them to one neighbour. The 10 µm fill limit can also cut off very large hidden regions. If the test shows covered cells are systematically too small or too large, change `hidden_fill_distance_um` or `inpaint_sigma_px`.
- **Annotation consistency.** Your hidden-part outlines are themselves a judgement call. Ask a second person to annotate a few covered cells, so you know how much annotators disagree on them.
- **Density.** Border and seam removal mean the raw count is not cells per field. Report density as cells per µm² of the analysed area.
