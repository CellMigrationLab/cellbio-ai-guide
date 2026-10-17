# advice_box1_cancer_r1

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

I'll check the current Cellpose documentation first, since that's the likely candidate.

## assistant (tool call: WebFetch)

```json
{
 "url": "https://cellpose.readthedocs.io/en/latest/api.html",
 "prompt": "Current Cellpose version, how to load models (CellposeModel, cpsam), eval() parameters (diameter, flow_threshold, cellprob_threshold, normalize, channels), input formats, GPU/CPU notes, and fine-tuning/train API (train_seg) signature."
}
```

## assistant (tool call: WebFetch)

```json
{
 "url": "https://cellpose.readthedocs.io/en/latest/train.html",
 "prompt": "How to fine-tune the cpsam model: train_seg arguments, data format, recommended number of epochs, learning rate, CPU feasibility, and how to evaluate."
}
```

## tool result

```
To fine-tune Cellpose-SAM (cpsam), start from the built-in cpsam model, which is the default. The page warns that restarting from a previous retraining biases the network toward earlier images.

**Data format**
- Put each image and its mask in the same folder. Masks are a separate file, e.g. `wells_000.tif` and `wells_000_masks.tif`, with 0 for background and 1, 2, ... for each mask.
- If your names differ, use `--mask_filter` (e.g. `_masks_2022`) or `--img_filter`. To train from GUI annotations, use `--mask_filter _seg.npy`.
- `--dir` and `--test_dir` should be absolute paths.
- Training uses images with at least `--min_train_masks` masks (default 5).

**Recommended settings**
- Learning rate: 1e-5
- Weight decay: 0.1
- Epochs: 100 (default)
- Batch size: 1

**Command line**
```
python -m cellpose --train --dir ~/images/train/ --test_dir ~/images/test/ --learning_rate 0.00001 --weight_decay 0.1 --n_epochs 100 --train_batch_size 1
```

**Notebook (`train.train_seg`)**
Load data with `io.load_train_test_data(...)`, create `models.CellposeModel(gpu=True)`, then call `train.train_seg` with `train_data`, `train_labels`, `test_data`, `test_labels`, `weight_decay=0.1`, `learning_rate=1e-5`, `n_epochs=100`, and `model_name`. It returns `model_path`, `train_losses`, and `test_losses`.

**Evaluation**
The page doesn't describe evaluation metrics. The main signal it provides is the `test_losses` returned by `train_seg`, which requires a test set. For inference, you can adjust normalization with `model.eval`, e.g. `normalize={"tile_norm_blocksize": 128}` or a percentile range, since normalization is applied per training image or crop.

**CPU feasibility**
The page doesn't say whether CPU training is feasible. Its examples use `gpu=True`, and it doesn't give CPU timings or requirements. The Timing and memory usage page linked from the site may cover this, but I can't confirm that from this content.
```

## tool result

```
**Cellpose API summary (from the page)**

- **Version:** The page doesn't state a current version number. It mentions "v4.0.1+" in the `train_seg` docs (SGD deprecation) and keeps a "CP3" compatibility note.

**Loading models**
- Use `cellpose.models.CellposeModel(gpu=False, pretrained_model='cpsam_v2', model_type=None, diam_mean=None, device=None, nchan=None, use_bfloat16=True)`.
- The page's `__init__` entry lists different defaults (`pretrained_model=False`, `diam_mean=30.`), so check the source if behavior differs.
- `pretrained_model` accepts a built-in name (e.g., "cpdino", "cpsam_v2") or a path to a custom model.

**`eval()` parameters (main ones)**
- `x`: list or array of 2D/3D/4D images. The docs say images "must have 3 channels," though `convert_image` also handles other channel counts.
- `batch_size=8`, `resample=True`, `channels=None`, `channel_axis=None`, `z_axis=None`
- `normalize=True`: 1st–99th percentile normalization per channel. Accepts a dict for finer control.
- `diameter=None`: "diameters are used to rescale the image to 30 pix cell diameter." `rescale` applies only when `diameter` is None.
- `flow_threshold=0.4`, `cellprob_threshold=0.0`
- `do_3D=False`, `anisotropy=None`, `flow3D_smooth=0`, `stitch_threshold=0.0`
- `min_size=15`, `max_size_fraction=0.4`, `niter=None`
- `augment=False`, `tile_overlap=0.1`, `bsize` (256 for cpsam; 384 suggested for cpdino), `compute_masks=True`
- **Returns:** `(masks, flows, styles)`. Styles are zero vectors, kept for CP3 compatibility.

**Input formats**
- 2D images, 2D with channels, batches shaped (N, H, W, C), and 3D with or without channels.
- `channel_axis` and `z_axis` can be set manually. `cellpose.io.imread` loads without automatic axis selection; `imread_3D` guesses axes.

**GPU/CPU notes**
- `gpu=False` by default. `assign_device` supports CPU, CUDA GPU, and mps.
- `use_gpu()` checks availability. Passing `device` explicitly is an option.
- `use_bfloat16=True` by default.

**Training: `cellpose.train.train_seg`**
- Signature: `train_seg(net, train_data=None, train_labels=None, train_files=None, train_labels_files=None, train_probs=None, test_data=None, test_labels=None, test_files=None, test_labels_files=None, test_probs=None, channel_axis=None, load_files=True, batch_size=1, learning_rate=1e-05, SGD=False, n_epochs=100, weight_decay=0.1, normalize=True, compute_flows=False, save_path=None, save_every=100, save_each=False, nimg_per_epoch=None, nimg_test_per_epoch=None, rescale=False, scale_range=None, bsize=None, min_train_masks=5, model_name=None, class_weights=None)`
- `SGD` is deprecated; AdamW is always used.
- `bsize` must be 256 for cpsam.
- Returns a tuple of saved weight path, training losses, and test losses.

[WebFetch note: this page's text is 100080 characters long and the answer above covers only characters 0 to 100000; the final 80 were not read — to read on, call WebFetch again with the same url and offset: 100000.]
```

## assistant

# Recommended approach: Cellpose-SAM baseline, then fine-tune on your annotation

I checked the current Cellpose docs. I haven't run anything on your data, so the performance statements below are expectations that the validation test should confirm or refute.

## Before you start: questions that change the plan

1. **Do the cancer cells look different from the endothelial cells in brightfield?** For example, are they round and refractile with a bright halo, while the endothelium is flat? This matters most. A generic cell segmenter will probably also outline endothelial cells, and your task is to separate the two classes. If the cancer cells are only distinguishable by a fluorescent label, tell me, because that label would give you automatic ground truth.
2. **How many images do you have, and how many cancer cells are in your annotation?** If it's one image with a few dozen cells, fine-tuning is possible but the evaluation will be weak.
3. **Does your annotation label only cancer cells, with the endothelium left as 0?** I'm assuming it does.
4. **Do cancer cells touch or overlap, or form clusters? Are some partly out of focus or on top of each other?**
5. **What does "aspect ratio" mean to you?** I'll use the fitted-ellipse major axis divided by minor axis, so it is ≥1.

Please send a representative crop of about 500×500 px and the matching annotation overlay if you can. It would settle question 1 immediately.

## Why this method

- **Scale fits.** 20 µm at 0.65 µm/px is about 31 px, close to the 30 px diameter Cellpose rescales to. You can run at native resolution with `diameter=None` and no resampling, so measurements stay in the original coordinates.
- **Cellpose-SAM.** The docs show `CellposeModel(gpu=False, pretrained_model=...)` (default `cpsam`, listed as `cpsam_v2` in the current API page). It takes a 2D array directly, applies 1st–99th percentile normalisation by default, and returns `(masks, flows, styles)`. It is a generalist model, but nothing guarantees it matches this contrast type or this cancer-versus-endothelium distinction. Treat it as a baseline.
- **Fine-tuning.** The docs recommend `learning_rate=1e-5`, `weight_decay=0.1`, `n_epochs=100`, `batch_size=1`, and `bsize=256` for cpsam. They give no CPU timings, so I can't promise it is practical on your laptop. Try a few epochs and time them first.
- **Fallback if Cellpose confuses the two cell types.** Segment everything, then classify each object as cancer or endothelium using features and your annotation. Tools for this include ilastik object classification and napari-accelerated-pixel-and-object-classification. Fine-tuning is the simpler first attempt.

I would not use classical thresholding or watershed. Brightfield has halos and low contrast, and the confluent monolayer produces texture that these methods can't distinguish from the cells.

## Explicit processing choices

| Step | Choice |
|---|---|
| Channel | Single 2D plane, passed as `(Y, X)` |
| dtype | uint16 to float32. Do **not** divide by 65535, because the data are 12-bit. Cellpose's percentile normalisation handles the range. |
| Normalisation | Cellpose default (1–99 percentile per image). It depends on how much of the field is covered by cells, so check it across images. |
| Resampling | None. `diameter=None` means no rescale. |
| Thresholds | `flow_threshold=0.4`, `cellprob_threshold=0.0` (defaults), to be tuned on the validation split only |
| Post-processing | Remove objects smaller than a minimum area in µm². Flag edge-touching cells. |
| Units | Area = pixel count × 0.65² µm² |

## Code

This is a sketch. Check the `eval` signature against your installed Cellpose version, because v3 and v4 differ in how `channels` is handled.

```python
"""Segment cancer cells in brightfield and measure area and aspect ratio."""
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from skimage.measure import regionprops_table
from skimage.segmentation import find_boundaries

PIXEL_SIZE_UM = 0.65
MIN_AREA_UM2 = 50.0  # ~8 µm diameter; placeholder, set from your smallest real cell


def load_brightfield(path: Path) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    if image.max() > 4095:
        raise ValueError(f"Max {image.max()} exceeds 12-bit range; check the data")
    return image.astype(np.float32)


def segment_cells(image: np.ndarray, model_path: str | None = None,
                  flow_threshold: float = 0.4,
                  cellprob_threshold: float = 0.0) -> np.ndarray:
    from cellpose import models
    kwargs = {"pretrained_model": model_path} if model_path else {}
    model = models.CellposeModel(gpu=False, **kwargs)
    masks, _, _ = model.eval(
        image, diameter=None, normalize=True,
        flow_threshold=flow_threshold, cellprob_threshold=cellprob_threshold,
    )
    return masks.astype(np.int32)


def remove_small_objects(labels: np.ndarray, min_area_um2: float) -> np.ndarray:
    min_px = min_area_um2 / PIXEL_SIZE_UM**2
    ids, counts = np.unique(labels[labels > 0], return_counts=True)
    small = ids[counts < min_px]
    out = labels.copy()
    out[np.isin(out, small)] = 0
    return out


def measure_cells(labels: np.ndarray) -> pd.DataFrame:
    table = pd.DataFrame(regionprops_table(
        labels, properties=("label", "area", "axis_major_length",
                            "axis_minor_length", "bbox")))
    if (table["axis_minor_length"] <= 0).any():
        raise ValueError("Degenerate object with zero minor axis; inspect labels")
    height, width = labels.shape
    out = pd.DataFrame({
        "label": table["label"],
        "area_um2": table["area"] * PIXEL_SIZE_UM**2,
        "aspect_ratio": table["axis_major_length"] / table["axis_minor_length"],
        "touches_border": (table["bbox-0"] == 0) | (table["bbox-1"] == 0)
                          | (table["bbox-2"] == height) | (table["bbox-3"] == width),
    })
    return out


def save_outputs(labels, table, image, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    tifffile.imwrite(out_dir / "labels.tif", labels.astype(np.uint16))
    table.to_csv(out_dir / "cells.csv", index=False)
    lo, hi = np.percentile(image, (1, 99))
    gray = np.clip((image - lo) / (hi - lo), 0, 1)
    overlay = np.stack([gray] * 3, axis=-1)
    overlay[find_boundaries(labels, mode="outer")] = (1, 0, 0)
    tifffile.imwrite(out_dir / "overlay.tif", (overlay * 255).astype(np.uint8))
```

### Validation against your annotation

```python
def match_by_iou(truth: np.ndarray, pred: np.ndarray, threshold: float = 0.5):
    """Return list of (truth_id, pred_id, iou). IoU > 0.5 guarantees unique matches."""
    pairs = []
    for t in np.unique(truth[truth > 0]):
        t_mask = truth == t
        candidates, counts = np.unique(pred[t_mask & (pred > 0)], return_counts=True)
        for p, inter in zip(candidates, counts):
            union = t_mask.sum() + (pred == p).sum() - inter
            if inter / union > threshold:
                pairs.append((t, p, inter / union))
    return pairs


def validate(truth: np.ndarray, pred: np.ndarray) -> dict:
    pairs = match_by_iou(truth, pred)
    n_truth = len(np.unique(truth[truth > 0]))
    n_pred = len(np.unique(pred[pred > 0]))
    tp = len(pairs)
    t_table = measure_cells(truth).set_index("label")
    p_table = measure_cells(pred).set_index("label")
    t_ids = [t for t, _, _ in pairs]
    p_ids = [p for _, p, _ in pairs]
    area_err = (p_table.loc[p_ids, "area_um2"].values
                / t_table.loc[t_ids, "area_um2"].values - 1)
    ar_diff = (p_table.loc[p_ids, "aspect_ratio"].values
               - t_table.loc[t_ids, "aspect_ratio"].values)
    return {
        "n_truth": n_truth, "n_pred": n_pred,
        "count_error_pct": 100 * (n_pred - n_truth) / n_truth,
        "precision": tp / n_pred, "recall": tp / n_truth,
        "F1_at_IoU0.5": 2 * tp / (n_truth + n_pred),
        "median_abs_area_err_pct": 100 * np.median(np.abs(area_err)),
        "area_bias_pct": 100 * np.median(area_err),
        "aspect_ratio_bias": float(np.median(ar_diff)),
        "aspect_ratio_MAE": float(np.mean(np.abs(ar_diff))),
    }
```

## The test to run on your annotated image

1. **Run the zero-shot baseline** on the annotated image and call `validate`. If the image was never used to train the model, this is a fair test.
2. **If you fine-tune,** split the image spatially, for example train on the left 70% and test on the right 30%, with a gap of at least one cell diameter (about 30 px) between them. Don't tune thresholds on the test region. A random tile split on a single image leaks information between the two sets.
3. **Look at the overlay.** Check that no endothelial cells are outlined and that touching cancer cells are separated.

**Suggested failure criteria.** These are my numbers, so set them from the effect size you need to detect:

- Precision < 0.85. This usually means endothelial cells are being counted.
- Recall < 0.80.
- Count error beyond ±10%.
- Median absolute area error above 15%, or area bias beyond ±10%.
- Aspect ratio bias beyond ±0.1, or an aspect ratio MAE that is larger than the difference you hope to detect between your biological conditions.

A high F1 with a biased area or aspect ratio still counts as a failure, because those are the measurements you care about.

## Audit: how this could be scientifically wrong

1. **Endothelial cells counted as cancer cells.** This is the most likely failure, and it inflates counts. Check precision separately from recall. Also include a control image with endothelium only, where the correct count is 0.
2. **Cancer cells missed because they are low-contrast or sit in a different focal plane.** Look at recall as a function of cell brightness or local contrast. Counts could drop systematically in one condition.
3. **Boundary placement.** The halo in brightfield makes the apparent edge depend on focus. Area can be biased by 10–30% without the F1 changing much. Compare the outlines against your annotation, and also check that your annotation followed a consistent edge rule.
4. **Aspect ratio from small or merged objects.** Merged touching cells give a high aspect ratio, and cells that are over-split give a low one. Check the distribution of aspect ratio against area, and look at outliers by eye.
5. **Border cells.** Cut-off cells have wrong shapes, so exclude them from the shape statistics. The table has a flag for this.
6. **Generalisation.** One annotated image won't tell you whether the model works across wells, days, cell lines, or illumination settings. Annotate at least one image from each condition you will compare, and hold out entire images for testing.
7. **Annotator variability.** If you can, have a second person annotate a subset. Model error that is similar to inter-annotator disagreement is a reasonable ceiling.
8. **Normalisation drift.** Percentile normalisation changes with the fraction of the field covered by cells. Test on an image with few cells and one with many.
9. **Fine-tuning overfit.** If training loss falls but the held-out F1 doesn't improve over the zero-shot baseline, you gain nothing from fine-tuning. Report both numbers.

If you send a crop and your answers to the five questions, I can narrow this down to a single pipeline and a tuned validation script.

Sources:
- [Cellpose API documentation](https://cellpose.readthedocs.io/en/latest/api.html)
- [Cellpose training documentation](https://cellpose.readthedocs.io/en/latest/train.html)

## user

They are rounded and sit on top of the endothelial monolayer; touching cells should be counted individually. Only this channel will be available for the analysis. The cancer cells are not fluorescently labelled. I have more fields of the same kind, from the same microscope and settings. I'd rather not say. I don't know. Major axis divided by minor axis of the fitted ellipse.

## assistant

Your answers settle the main design questions, so I'll commit to a plan. Rounded cells sitting on top of a flat monolayer is the easiest case for brightfield. They usually have a bright halo and dark rim, and the endothelium is textured but flat. I haven't run any of this on your data.

## Decision

**Cellpose-SAM, zero-shot first and then fine-tuned. Evaluate on whole held-out fields.**

- Use the 2D image at native resolution with `diameter=None`, since about 31 px is close to Cellpose's 30 px reference.
- Fine-tuning is worth trying because the model has to learn "rounded cell on top of the monolayer", not "any cell".
- You have more fields from the same microscope and settings. That is what makes honest validation possible, so use it.
- Your single annotation is not enough to tune and test on. Add a few more fields.

## Steps

1. **Check the annotation.** Overlay it on the image and confirm that only cancer cells are labelled, touching cells have separate labels, and no endothelial cell is labelled. You said you don't know whether it does. This is a ten-second check, and everything downstream depends on it.
2. **Run the zero-shot baseline** on the annotated image and compute the metrics. This is the number fine-tuning has to beat.
3. **Annotate more fields by correcting predictions.** Run the baseline on 5–10 more fields, then fix the labels in the Cellpose GUI (`python -m cellpose`, which saves `_seg.npy`). Correcting is much faster than drawing from scratch. Because the corrections start from model output, the model's errors and your labels will be correlated. Check at least a couple of fields by drawing them without looking at the predictions.
4. **Split by field.** For example, train on 4–6 fields, use 1–2 for choosing epochs and thresholds, and keep 2 or more completely untouched for the final report. With one annotated image only, use a left/right split with a 30 px gap, and report that result as a weak estimate.
5. **Fine-tune on CPU.** Time 2–3 epochs first. If 100 epochs is too slow, use fewer epochs and look at the held-out metrics. The docs give no CPU timings, so I can't predict this.
6. **Run the final pipeline** on all fields and keep the labels, overlays and table for each.

## Fine-tuning and inference code

This adds to the module from before. Check it against your installed version, because the docs showed `train_seg` with `bsize` fixed at 256 for cpsam. I haven't verified how it handles images smaller than 256 px or non-square crops.

```python
def finetune(train_images: list[np.ndarray], train_labels: list[np.ndarray],
             val_images: list[np.ndarray], val_labels: list[np.ndarray],
             model_name: str, save_dir: Path, n_epochs: int = 100) -> Path:
    """Fine-tune cpsam. lr=1e-5, weight_decay=0.1, batch_size=1 per Cellpose docs."""
    from cellpose import models, train
    if len(train_images) != len(train_labels) or len(val_images) != len(val_labels):
        raise ValueError("Image and label list lengths differ")
    for img, lab in zip(train_images + val_images, train_labels + val_labels):
        if img.shape != lab.shape:
            raise ValueError(f"Shape mismatch: image {img.shape} vs labels {lab.shape}")
    model = models.CellposeModel(gpu=False)
    model_path, train_losses, val_losses = train.train_seg(
        model.net,
        train_data=train_images, train_labels=train_labels,
        test_data=val_images, test_labels=val_labels,
        learning_rate=1e-5, weight_decay=0.1, n_epochs=n_epochs, batch_size=1,
        normalize=True, model_name=model_name, save_path=str(save_dir),
    )
    return Path(model_path)
```

For the single-image fallback, create the train and validation arrays by cropping, with the gap removed:

```python
def split_left_right(image, labels, train_frac=0.7, gap_px=30):
    x_train_end = int(image.shape[1] * train_frac)
    x_val_start = x_train_end + gap_px
    if x_val_start >= image.shape[1]:
        raise ValueError("Image too narrow for this split and gap")
    return ((image[:, :x_train_end], labels[:, :x_train_end]),
            (image[:, x_val_start:], labels[:, x_val_start:]))
```

One caveat on this split: cells cut by the split edge become partial cells. Drop them from both sets, or accept that this makes the estimate a little pessimistic.

Run the baseline and fine-tuned model through the same evaluation:

```python
labels_base = remove_small_objects(segment_cells(image), MIN_AREA_UM2)
labels_ft   = remove_small_objects(segment_cells(image, model_path=str(model_path)), MIN_AREA_UM2)
print(validate(truth, labels_base))
print(validate(truth, labels_ft))
```

Evaluate on the held-out region or fields only. `validate` includes edge-touching cells. For the final report, also run it with cells that touch the border removed from both truth and prediction. Otherwise a cut-off cell could be counted as a miss or a false match.

## What counts as failure, now that I know your cells

- **Precision below 0.85.** This means the model is still outlining endothelial structures or debris. Look at the false positives in the overlay before changing anything else.
- **Recall below 0.80.** Look at whether the missed cells are out of focus or touching.
- **Merge or split errors.** Touching cells must be counted individually. Compute how many truth cells are matched to a prediction that also covers another truth cell. A model can get a good F1 at IoU 0.5 and still merge pairs in clusters. Check cluster regions specifically, because count and aspect ratio both depend on this.
- **Area bias beyond ±10% or aspect ratio bias beyond ±0.1.** These apply even if F1 looks good.
- **Fine-tuned model no better than the baseline on held-out fields.** In that case use the baseline and don't claim a benefit from fine-tuning.

## Remaining risks to your conclusion

1. **Cells in clusters:** this is the most likely source of count errors given that touching cells must be separated. Annotate several dense regions, and report accuracy for dense and sparse regions separately.
2. **Halo and focus:** area depends on where the edge is placed in a halo. If you compare conditions, check that the bias is the same in each condition. A constant bias cancels in comparisons and a condition-dependent one doesn't.
3. **Aspect ratio of near-round cells:** for cells that are almost circular, the ratio is close to 1 and is sensitive to a few pixels of boundary error (a 25 µm cell is about 38 px across). Report the aspect ratio error against the spread you expect between conditions.
4. **Fields that differ from the annotated ones:** cell density, how many cancer cells were seeded, and monolayer quality can all vary. Choose your held-out fields to cover this range, and include one with no cancer cells (the correct count is 0).
5. **Training data leakage:** do not use any held-out field for choosing thresholds or epochs. Keep the final test fields untouched until the end.

## What I still need from you

You answered some of my questions with "I'd rather not say" and "I don't know", so I've worked around those. These two would change the plan:

- **How many annotated cells does the image have, and how many fields are available?** The answer decides whether fine-tuning is worth trying and how reliable the evaluation can be.
- **Do the annotated cells include any endothelial cells or debris?** Step 1 covers this.

If you send a crop, I can also check whether 31 px really is the right object scale and whether `MIN_AREA_UM2 = 50` is a sensible cutoff.
