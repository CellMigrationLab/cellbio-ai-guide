# advice_box1_cancer_r3

## user

You are an AI assistant chatting with a user. You can search the web (WebSearch and WebFetch; load them with ToolSearch if they are not listed). You cannot run code. Reply to the user as you normally would.

I want to segment and count the cancer cells and measure their shape (area and aspect ratio) from brightfield images of cancer cells sitting on top of a confluent endothelial monolayer. Help me choose an analysis approach.
My images are 2D, with axes Y, X, channels 1 (brightfield), data type uint16 (12-bit values), pixel/voxel size 0.65 µm, and objects of interest approximately 15–25 µm in size. I use Python 3.13 on a laptop CPU (no GPU). The output I need is a label image with one integer per cancer cell (0 = background) and a table with the area (µm²) and aspect ratio of each cancer cell. I can provide a manual annotation of this image (a label image).
Please:

* Clarify the task. Ask for missing information only when it could materially affect the analysis. If useful, ask me for representative images or examples of the expected result.
* Use appropriate methods. Prefer established, maintained software and documented APIs. Check current documentation rather than relying only on memory. If consequential behaviour remains unclear, inspect the source code when available rather than guessing.
* Check deep learning model suitability. If using a pre-trained model, consider whether my images match its training data, including image type, channels, dimensionality, object scale, preprocessing and post-processing.
* Write code according to best practices. Keep functions small and focused, use clear names and annotations, and separate consequential processing steps. Validate inputs, provide informative errors and do not use silent fallbacks.
* Make processing explicit. State important parameters, defaults and transformations, including resizing, resampling, normalisation, channel selection and post-processing. Preserve the original coordinate system and physical units unless a transformation is explicitly required and documented.
* Make the analysis testable. Test it on representative reference data where possible, save useful intermediate outputs and overlays, and use validation measures appropriate to the intended biological measurement rather than relying on a single generic score. Include a test I can run on my annotated example and tell me what result would mean that the analysis failed. If I ask for counts or measurements, return the masks or outlines they come from.
* Audit and challenge the result. Before finishing, assume that the analysis could be scientifically wrong even if the code runs and the output looks plausible. Identify the failure modes most likely to change the biological conclusion and suggest concrete tests or reference data that would expose them.

## assistant

I'll check the current Cellpose docs first, since the right model choice depends on them.

## assistant (tool call: WebFetch)

```json
{
 "url": "https://cellpose.readthedocs.io/en/latest/",
 "prompt": "Which models exist in current Cellpose (cpsam, Cellpose-SAM)? Python version support, CPU use, how to fine-tune/train on own labels, API for models.CellposeModel eval and train (train_seg), diameter handling, input channel handling, normalization defaults."
}
```

## assistant (tool call: WebFetch)

```json
{
 "url": "https://cellpose.readthedocs.io/en/latest/train.html",
 "prompt": "Give the exact Python API for fine-tuning: train.train_seg arguments, models.CellposeModel arguments (pretrained_model, gpu), data loading, recommended number of epochs, CPU notes."
}
```

## tool result

```
The page confirms some of what you asked about, but most details (Python versions, CPU use, training steps, diameter, channels, normalization defaults) appear only as section titles. The full content of those sections isn't included.

**Models**
- The page announces **Cellpose-SAM**, described as offering "superhuman generalization for cellular segmentation." It doesn't name the model "cpsam" in the text, though the API reference lists a `CPSAM` class and a `CPDINO` class.
- Older releases (Cellpose 2.0, Cellpose 3, original Cellpose) are listed separately.
- A "Built-in models" section exists, but its contents aren't shown.

**Python version and CPU use**
- Not specified. The page says cellpose "is an anatomical segmentation algorithm written in Python 3."
- Install is via `pip install cellpose[gui]`. Installation sub-pages cover M1–M3 Mac and AMD GPU (ROCm), but their contents aren't included.
- The API lists `assign_device()` and `use_gpu()`. A "Timing + memory usage" page exists, but its contents aren't shown.

**Fine-tuning and training on your own labels**
- Relevant sections exist: "Training your own cellpose model" (GUI), "Training" with CLI training options, "Re-training a model," and "User-trained models."
- The API lists `train_seg()` in the training module.
- The page gives no steps, data formats, or parameters for these.

**API: `models.CellposeModel`**
- Members listed: `diam_mean`, `builtin`, `device`, `nclasses`, `nbase`, `net`, `pretrained_model`, `backbone`, `__init__()`, and `eval()`.
- The page lists these names only, with no signatures or parameter descriptions.
- `train_seg()` is listed under Training, with no signature or parameters shown.

**Diameter handling**
- A "Diameter" entry exists under Settings, and `CellposeModel.diam_mean` is listed. No behavior is described.

**Input channel handling**
- A "Channels" entry exists under Settings. No details are given.

**Normalization defaults**
- The transforms module lists `normalize99()`, `normalize99_tile()`, and `normalize_img()`. The page doesn't say what the defaults are.

For these details, check the Settings, Training, and API Guide pages linked from the site, or the Cellpose-SAM paper on bioRxiv.
```

## tool result

```
The page documents one fine-tuning path, a notebook workflow built on `train.train_seg`:

```python
from cellpose import io, models, train
io.logger_setup()

# Load paired images and masks; masks are named with the mask_filter suffix
output = io.load_train_test_data(train_dir, test_dir, image_filter="_img",
                                 mask_filter="_masks", look_one_level_down=False)
images, labels, image_names, test_images, test_labels, image_names_test = output

model = models.CellposeModel(gpu=True)

model_path, train_losses, test_losses = train.train_seg(model.net,
                            train_data=images, train_labels=labels,
                            test_data=test_images, test_labels=test_labels,
                            weight_decay=0.1, learning_rate=1e-5,
                            n_epochs=100, model_name="my_new_model")
```

**Data loading:** `io.load_train_test_data(train_dir, test_dir, image_filter, mask_filter, look_one_level_down)`. Masks are separate files, with 0 as background and 1, 2, ... as mask IDs. For example, `wells_000.tif` pairs with `wells_000_masks.tif`. The example uses `image_filter="_img"` and `mask_filter="_masks"`.

**Model:** `models.CellposeModel(gpu=True)`. The page's example uses only the `gpu` argument. It does not document `pretrained_model`, so I can't confirm its signature here. The page does say to start fine-tuning from the built-in cpsam model, which is the default.

**train.train_seg arguments shown on the page:**
- `model.net` (positional network argument)
- `train_data`, `train_labels`
- `test_data`, `test_labels` (optional test set)
- `weight_decay`: 0.1
- `learning_rate`: 1e-5
- `n_epochs`: 100
- `model_name`: output name, e.g. "my_new_model"

It returns `model_path, train_losses, test_losses`. The page does not list other arguments, such as the batch size, which is set as `train_batch_size` in the CLI (default 1).

**Epochs:** The recommended value is 100, which is also the default.

**CPU:** The page does not cover CPU training. Its examples use `gpu=True`.

**Other notes:**
- The page warns that starting from a previous retrained model biases the network toward earlier images, so keep all training images for one model in one folder.
- Normalization happens per training image, and the default percentile for training crops is [1, 99]. For full-image adjustments at inference, the page suggests `normalize={"tile_norm_blocksize": 128}` or a percentile such as `[3, 98]`.
```

## assistant

# Recommended approach

**Cellpose-SAM (Cellpose 4, `cpsam`) first, zero-shot, as a baseline. Then fine-tune it on your annotation if the baseline fails the acceptance test below.** Its docs describe it as a generalist model, and it is the default model in current Cellpose.

Why not the alternatives:
- **Classical thresholding or watershed:** brightfield cells on a confluent monolayer have weak, uneven contrast, and the endothelial cells are also visible. Global methods are unlikely to separate the two cell types.
- **StarDist:** its pre-trained models are for fluorescence or H&E, not brightfield, so you would have to train it from scratch.

**What I could and couldn't verify.** I read the Cellpose docs home page and training page. They confirm the `cpsam` default and the `train.train_seg` fine-tuning API. They don't cover CPU training, diameter handling, or Python 3.13 support. I couldn't confirm any of those, so run `pip install cellpose` in your 3.13 environment and check that it works. I also can't run code here, so **none of the code below has been run**.

**Main risk: model suitability.**
- Cellpose is trained to find *all* cells.
- In your images it will probably also segment endothelial cells, because "cancer cell" versus "endothelial cell" is a semantic distinction, not just an edge-detection one.
- Zero-shot output may therefore need a classification step, or fine-tuning on your annotation, where only cancer cells are labelled and the rest is background.
- Fine-tuning on CPU should be feasible with small crops. Expect it to be slow.

## Questions that could change the plan
1. How many images do you have, and how large are they (in pixels)? You've offered one annotated image. That is enough to test, but thin for training.
2. Does your annotation label only cancer cells, with endothelial cells left as 0?
3. Do cancer cells touch or form clusters? Are some spread flat, rounded, or dividing? This affects both splitting and how meaningful aspect ratio is.
4. Should cells cut off by the image border be counted? They are always bad for area and aspect ratio. I assume they are **excluded from the shape table but reported**.
5. Which aspect ratio do you want? I assume the major/minor axis length of the ellipse with the same second moments (`skimage.measure.regionprops`). Feret or min-area-rectangle ratios differ.
6. Could you share the image, or a crop, with your annotation overlaid? I'd like to see how distinct the cancer cells are.

## Code

```python
"""Segment cancer cells in brightfield 2D images and measure area and aspect ratio."""
from pathlib import Path

import numpy as np
import pandas as pd
from skimage import io as skio, measure, segmentation

PIXEL_SIZE_UM = 0.65          # µm per pixel, Y and X
MIN_AREA_UM2 = 50.0           # below this is debris, not a 15-25 µm cell
MAX_AREA_UM2 = 1500.0         # above this is probably a merge


def load_image(path: Path) -> np.ndarray:
    """Load a single-channel 2D image. Raise if it is not (Y, X)."""
    image = skio.imread(path)
    if image.ndim != 2:
        raise ValueError(f"{path}: expected 2D (Y, X), got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"{path}: expected uint16, got {image.dtype}")
    return image


def segment(image: np.ndarray, model_path: str | None = None) -> np.ndarray:
    """Run Cellpose-SAM. Returns an int label image; 0 is background.

    Uses Cellpose defaults (flow_threshold=0.4, cellprob_threshold=0.0).
    The image is NOT rescaled to 16-bit; Cellpose normalizes per image
    (1st-99th percentile), so the 12-bit range is handled.
    """
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model=model_path or "cpsam")
    masks, _flows, _styles = model.eval(image)
    return masks.astype(np.int32)


def filter_labels(labels: np.ndarray) -> tuple[np.ndarray, pd.DataFrame]:
    """Drop border-touching and out-of-range objects. Record why, don't hide it."""
    kept = labels.copy()
    rows = []
    h, w = labels.shape
    for r in measure.regionprops(labels):
        area_um2 = r.area * PIXEL_SIZE_UM**2
        y0, x0, y1, x1 = r.bbox
        reason = None
        if y0 == 0 or x0 == 0 or y1 == h or x1 == w:
            reason = "touches_border"
        elif not MIN_AREA_UM2 <= area_um2 <= MAX_AREA_UM2:
            reason = "area_out_of_range"
        if reason:
            kept[kept == r.label] = 0
            rows.append({"label": r.label, "area_um2": area_um2, "reason": reason})
    return kept, pd.DataFrame(rows, columns=["label", "area_um2", "reason"])


def measure_cells(labels: np.ndarray) -> pd.DataFrame:
    """Area (µm²) and aspect ratio (major/minor axis of the moment ellipse)."""
    rows = []
    for r in measure.regionprops(labels):
        if r.axis_minor_length == 0:
            raise ValueError(f"label {r.label} is degenerate (zero minor axis)")
        rows.append({
            "label": r.label,
            "area_um2": r.area * PIXEL_SIZE_UM**2,
            "aspect_ratio": r.axis_major_length / r.axis_minor_length,
            "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
            "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
        })
    return pd.DataFrame(rows)


def save_outputs(out_dir: Path, stem: str, image, labels, table, excluded) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    skio.imsave(out_dir / f"{stem}_labels.tif", labels.astype(np.uint16), check_contrast=False)
    table.to_csv(out_dir / f"{stem}_cells.csv", index=False)
    excluded.to_csv(out_dir / f"{stem}_excluded.csv", index=False)
    lo, hi = np.percentile(image, (1, 99))
    display = np.clip((image - lo) / (hi - lo), 0, 1)
    overlay = segmentation.mark_boundaries(display, labels, color=(1, 0, 0))
    skio.imsave(out_dir / f"{stem}_overlay.png", (overlay * 255).astype(np.uint8))
```

## Test on your annotated image

```python
def match_by_iou(pred: np.ndarray, truth: np.ndarray, threshold: float = 0.5):
    """One-to-one matching of predicted to true labels. Returns (pred_id, true_id) pairs."""
    pairs = []
    for t in np.unique(truth[truth > 0]):
        t_mask = truth == t
        candidates, counts = np.unique(pred[t_mask & (pred > 0)], return_counts=True)
        best, best_iou = None, 0.0
        for p, inter in zip(candidates, counts):
            union = t_mask.sum() + (pred == p).sum() - inter
            if inter / union > best_iou:
                best, best_iou = p, inter / union
        if best is not None and best_iou >= threshold:
            pairs.append((best, t))
    return pairs


def evaluate(pred, truth) -> dict:
    pairs = match_by_iou(pred, truth)
    n_pred, n_true, tp = len(np.unique(pred)) - 1, len(np.unique(truth)) - 1, len(pairs)
    pred_t = measure_cells(pred).set_index("label")
    true_t = measure_cells(truth).set_index("label")
    area_err = [(pred_t.area_um2[p] - true_t.area_um2[t]) / true_t.area_um2[t] for p, t in pairs]
    ar_err = [pred_t.aspect_ratio[p] - true_t.aspect_ratio[t] for p, t in pairs]
    return {
        "count_pred": n_pred, "count_true": n_true,
        "count_error_pct": 100 * (n_pred - n_true) / n_true,
        "precision": tp / n_pred, "recall": tp / n_true,
        "median_area_error_pct": 100 * np.median(area_err),
        "median_abs_aspect_error": np.median(np.abs(ar_err)),
        "median_aspect_bias": np.median(ar_err),
    }
```

Run the test this way:
- **Zero-shot:** apply it to the whole annotated image. Run `filter_labels` on **both** prediction and annotation first, so the comparison is fair.
- **After fine-tuning:** train on one spatial half of the image and test on the other half. Testing on the training area would only measure memorisation.

**The analysis has failed if any of these is true.** These thresholds are my suggestions, so adjust them to the precision your biology needs and fix them before you look at results:
- Precision or recall at IoU 0.5 is below 0.8. A low precision usually means endothelial cells are being called cancer cells.
- The count error is more than ±10%.
- The median area error is more than ±15%, or the median aspect-ratio error is more than 0.15.
- The overlay shows systematic merges or splits, or the outlines sit visibly inside or outside the cell edge.

## Audit: how this could be wrong while looking fine

1. **Endothelial cells counted as cancer cells.** Counts look plausible, but they are inflated. Check precision, not just the count, and look at the overlay.
2. **Halo and boundary bias.** In brightfield, the dark rim and bright halo make outlines shift. Area and aspect ratio then carry a systematic bias even when IoU is good. The signed `median_area_error_pct` and `median_aspect_bias` expose it. Compare with a fluorescence-labelled cancer cell channel if you have one.
3. **Your annotation as the reference.** Check how consistent it is. Have a second person annotate a crop, or re-annotate it yourself later, to get the human-to-human IoU. If that is about 0.8, you can't expect the model to beat it.
4. **Overfitting to one image.** One annotated image is a weak basis for fine-tuning. Annotate a few more fields from different wells, days, and cell densities before trusting the model on a new condition.
5. **Condition-dependent failure.** A model tuned on sparse cells may merge clusters at high density, or miss treated cells that are rounded, spread, or dying. Biological conclusions are often drawn from exactly these differences, so check them directly. Spot-check overlays for each condition.
6. **Border and size filters.** These change the counts and the shape distribution, for example by removing large spread cells. The excluded-objects CSV lets you see how many are dropped per condition.
7. **Aspect ratio of small objects.** At 0.65 µm per pixel, a 15 µm cell is about 23 px across, so one boundary pixel changes the aspect ratio by a few percent. Don't over-interpret small differences between conditions. Check them with a bootstrap.
8. **Batch effects.** Different illumination, focus, or exposure between experiments can shift performance. Test on at least one image from a different session.

Send me an example crop and your annotation, and I'll turn this into a fine-tuning script with a spatial train/test split.

Sources:
- https://cellpose.readthedocs.io/en/latest/
- https://cellpose.readthedocs.io/en/latest/train.html

## user

I have more fields of the same kind, from the same microscope and settings. My images are 1024 × 1022 pixels (width × height), uint16. They are rounded and sit on top of the endothelial monolayer; touching cells should be counted individually. Cells cut by the image border can be left out of the area and shape statistics. Major axis divided by minor axis of the fitted ellipse. I don't have an example image to share in this conversation. I don't know.

## assistant

Your answers settle most of the design. Here is what I'm assuming, and what the plan looks like now.

**Assumptions. Tell me if any are wrong.**
- Arrays are `(1022, 1024)` as `(Y, X)`, uint16, one channel, at 0.65 µm per pixel.
- Touching rounded cells must be split into separate labels. I'll measure merges explicitly.
- Border-cut cells stay in the label image and in the count, but are flagged and left out of area and aspect-ratio statistics. I'm assuming you still want them counted. If you don't, say so.
- Your "I don't know" didn't match any single question, so I'm guessing it was about whether your annotation labels only cancer cells. **Please check this before anything else.** If the annotation also contains endothelial cells, every score below is meaningless.
- I still don't know how many fields you have. That decides whether fine-tuning is realistic.

## Plan
1. **Zero-shot baseline.** Run `cpsam` on your annotated field and score it. It costs nothing, and the result tells you whether to continue.
2. **If it fails, fine-tune.** The most likely failure is endothelial cells being segmented. Annotate 3–5 more fields, only the cancer cells, with the same rules as your first annotation.
3. **Split by field, never by tile.** Train on some fields, and hold out whole fields for testing. Neighbouring tiles of one field share cells and illumination, so a tile split would leak.
4. **Fix the settings, then run the batch.** After tuning, make no per-image adjustments.

## Code (not run, since I can't run code here)

```python
"""cellcount.py: cancer cell segmentation and shape measurement, brightfield 2D."""
from pathlib import Path

import numpy as np
import pandas as pd
from skimage import io as skio, measure, segmentation

PIXEL_SIZE_UM = 0.65
EXPECTED_SHAPE = (1022, 1024)     # (Y, X)
AREA_RANGE_UM2 = (50.0, 1500.0)   # flag only; objects are never silently removed


def load_image(path: Path) -> np.ndarray:
    image = skio.imread(path)
    if image.shape != EXPECTED_SHAPE:
        raise ValueError(f"{path}: expected {EXPECTED_SHAPE} (Y, X), got {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"{path}: expected uint16, got {image.dtype}")
    return image


def segment(image: np.ndarray, pretrained_model: str = "cpsam") -> np.ndarray:
    """Cellpose-SAM on CPU with default eval settings. Image is not rescaled by us."""
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model=pretrained_model)
    masks, _flows, _styles = model.eval(image)
    if masks.shape != image.shape:
        raise RuntimeError(f"Output {masks.shape} != input {image.shape}")
    return masks.astype(np.int32)


def measure_cells(labels: np.ndarray) -> pd.DataFrame:
    """One row per label. Border and size are flagged, not filtered."""
    h, w = labels.shape
    rows = []
    for r in measure.regionprops(labels):
        if r.axis_minor_length == 0:
            raise ValueError(f"label {r.label} has zero minor axis (degenerate)")
        y0, x0, y1, x1 = r.bbox
        area_um2 = r.area * PIXEL_SIZE_UM**2
        rows.append({
            "label": r.label,
            "area_um2": area_um2,
            "aspect_ratio": r.axis_major_length / r.axis_minor_length,
            "touches_border": y0 == 0 or x0 == 0 or y1 == h or x1 == w,
            "area_out_of_range": not AREA_RANGE_UM2[0] <= area_um2 <= AREA_RANGE_UM2[1],
            "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
            "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
        })
    return pd.DataFrame(rows)


def shape_statistics(table: pd.DataFrame) -> pd.DataFrame:
    """Rows used for area/aspect-ratio statistics: not touching the border."""
    return table[~table.touches_border]


def save_outputs(out_dir: Path, stem: str, image: np.ndarray,
                 labels: np.ndarray, table: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    skio.imsave(out_dir / f"{stem}_labels.tif", labels.astype(np.uint16), check_contrast=False)
    table.to_csv(out_dir / f"{stem}_cells.csv", index=False)
    lo, hi = np.percentile(image, (1, 99))
    display = np.clip((image.astype(float) - lo) / (hi - lo), 0, 1)
    overlay = segmentation.mark_boundaries(display, labels, color=(1, 0, 0))
    skio.imsave(out_dir / f"{stem}_overlay.png", (overlay * 255).astype(np.uint8))
```

```python
"""evaluate.py: score a prediction against a manual annotation of the same field."""
import numpy as np
from cellcount import measure_cells


def iou_matrix(pred, truth):
    """IoU for every (true, pred) pair that overlaps. Returns dict[(t, p)] -> iou."""
    both = (pred > 0) & (truth > 0)
    pairs, inter = np.unique(np.stack([truth[both], pred[both]]), axis=1, return_counts=True)
    t_area = dict(zip(*np.unique(truth[truth > 0], return_counts=True)))
    p_area = dict(zip(*np.unique(pred[pred > 0], return_counts=True)))
    return {(t, p): n / (t_area[t] + p_area[p] - n) for (t, p), n in zip(pairs.T, inter)}


def evaluate(pred, truth, iou_threshold=0.5) -> dict:
    ious = iou_matrix(pred, truth)
    # IoU >= 0.5 gives at most one match per object, so greedy matching is unambiguous.
    matches = {t: p for (t, p), v in ious.items() if v >= iou_threshold}
    n_true, n_pred = len(np.unique(truth)) - 1, len(np.unique(pred)) - 1
    tp = len(matches)

    # Merges: one prediction overlapping >=2 true cells; splits: the reverse.
    overlap_p = [p for (t, p), v in ious.items() if v > 0.1]
    overlap_t = [t for (t, p), v in ious.items() if v > 0.1]
    merges = sum(c > 1 for c in np.unique(overlap_p, return_counts=True)[1]) if overlap_p else 0
    splits = sum(c > 1 for c in np.unique(overlap_t, return_counts=True)[1]) if overlap_t else 0

    pt = measure_cells(pred).set_index("label")
    tt = measure_cells(truth).set_index("label")
    inner = [(t, p) for t, p in matches.items()
             if not tt.touches_border[t] and not pt.touches_border[p]]
    area_err = np.array([(pt.area_um2[p] - tt.area_um2[t]) / tt.area_um2[t] for t, p in inner])
    ar_err = np.array([pt.aspect_ratio[p] - tt.aspect_ratio[t] for t, p in inner])
    return {
        "n_true": n_true, "n_pred": n_pred,
        "count_error_pct": 100 * (n_pred - n_true) / n_true,
        "precision": tp / n_pred, "recall": tp / n_true,
        "merged_predictions": merges, "split_true_cells": splits,
        "n_shape_pairs": len(inner),
        "median_area_error_pct": 100 * float(np.median(area_err)),
        "median_abs_area_error_pct": 100 * float(np.median(np.abs(area_err))),
        "median_aspect_bias": float(np.median(ar_err)),
        "median_abs_aspect_error": float(np.median(np.abs(ar_err))),
    }
```

```python
"""run_zero_shot.py <image.tif> <annotation.tif> <out_dir>"""
import json, sys
from pathlib import Path
from skimage import io as skio
from cellcount import load_image, segment, measure_cells, save_outputs
from evaluate import evaluate

image_path, truth_path, out_dir = map(Path, sys.argv[1:4])
image = load_image(image_path)
truth = skio.imread(truth_path)
if truth.shape != image.shape:
    raise ValueError(f"annotation {truth.shape} != image {image.shape}")

labels = segment(image)
save_outputs(out_dir, image_path.stem, image, labels, measure_cells(labels))
skio.imsave(out_dir / "annotation_overlay_check.tif", truth.astype("uint16"), check_contrast=False)
print(json.dumps(evaluate(labels, truth.astype("int32")), indent=2))
```

Fine-tuning, only if the baseline fails. It uses the `train.train_seg` call from the docs, with arrays passed directly. I haven't confirmed that in-memory arrays work for 2D grayscale in your installed version, so check against the installed docs.

```python
"""finetune.py: train on whole annotated fields, test on other whole fields."""
from pathlib import Path
from skimage import io as skio
from cellpose import models, train
from cellcount import load_image

def load_pairs(image_dir: Path, mask_suffix="_masks.tif"):
    images, masks = [], []
    for p in sorted(image_dir.glob("*.tif")):
        if p.name.endswith(mask_suffix):
            continue
        mask_path = p.with_name(p.stem + mask_suffix)
        if not mask_path.exists():
            raise FileNotFoundError(f"no annotation for {p.name}: {mask_path.name}")
        images.append(load_image(p)); masks.append(skio.imread(mask_path).astype("int32"))
    if not images:
        raise ValueError(f"no images found in {image_dir}")
    return images, masks

train_x, train_y = load_pairs(Path("train_fields"))
test_x, test_y = load_pairs(Path("test_fields"))   # different fields from train
model = models.CellposeModel(gpu=False)            # starts from cpsam
model_path, train_loss, test_loss = train.train_seg(
    model.net, train_data=train_x, train_labels=train_y,
    test_data=test_x, test_labels=test_y,
    weight_decay=0.1, learning_rate=1e-5, n_epochs=20,   # docs default is 100
    model_name="cancer_brightfield")
print("saved:", model_path)
```

I set `n_epochs=20` as a time-test, because I couldn't verify CPU training speed. Run it and time one epoch. Then raise it only if the test loss is still falling.

## Pass/fail for your annotated field
Fix these before you look at the numbers. They're my suggested thresholds, so adjust them to your biology:
- **Fail if** precision or recall is below 0.8, or the count error is beyond ±10%.
- **Fail if** `merged_predictions + split_true_cells` is more than about 5% of `n_true`. You asked for touching cells to be counted individually, so merges are the key error.
- **Fail if** `median_abs_area_error_pct` is above 15%, or `median_abs_aspect_error` is above 0.15.
- **Fail if** `|median_aspect_bias|` is above 0.05 or `|median_area_error_pct|` is above 5%. That means a systematic outline bias, and it would shift every comparison between conditions.
- **Look at the overlay regardless.** The metrics can pass while endothelial structures are labelled in areas your annotation doesn't cover.

## Audit: what is most likely to be wrong
1. **Rounded cells in brightfield have a bright halo and a dark rim.** Cellpose may include or exclude the rim, which biases area and also aspect ratio. Check this against an independent reference, such as a fluorescent cancer-cell label on a few fields. If you don't have one, measure the same cells on a different focus plane.
2. **Clusters.** The aspect ratio of a merged pair is large, so merges inflate the shape tail. Check the largest 5% of objects by area in the overlay.
3. **Annotation consistency.** One person annotating one field is a single sample of how "the correct outline" looks. Re-annotate a crop a week later and score it against your first pass. If that human-to-human agreement is below your pass thresholds, the thresholds are too strict.
4. **Hidden variation between fields.** "Same microscope and settings" doesn't guarantee the same density, focus, or endothelial texture. Hold out whole fields from different wells or days, and compare their metrics with your first field.
5. **Border-cell exclusion.** This biases shape statistics against large cells, because large cells are more likely to touch the border. Keep the counts of excluded cells per field, and check that the proportion doesn't differ between conditions.
6. **Aspect ratio precision.** A 15 µm cell is only about 23 px across. Compare conditions with bootstrapped confidence intervals, not raw means.

Next steps: check your annotation, then run `run_zero_shot.py` and send me the metrics JSON. I can also look at the numbers if you paste them. Please also tell me how many fields you have. That decides whether we fine-tune or only tune post-processing.
