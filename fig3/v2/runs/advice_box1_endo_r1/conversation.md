# advice_box1_endo_r1

## user

You are an AI assistant chatting with a user. You can search the web (WebSearch and WebFetch; load them with ToolSearch if they are not listed). You cannot run code. Reply to the user as you normally would.

I want to segment and count the endothelial cells and measure their shape (area and aspect ratio) from brightfield images of a confluent endothelial monolayer (some cancer cells sit on top). Help me choose an analysis approach.
My images are 2D, with axes Y, X, channels 1 (brightfield), data type uint16 (12-bit values), pixel/voxel size 0.65 µm, and objects of interest approximately 25–50 µm in size. I use Python 3.13 on a laptop CPU (no GPU). The output I need is a label image with one integer per endothelial cell (0 = background) and a table with the area (µm²) and aspect ratio of each endothelial cell. I can provide a manual annotation of this image (a label image).
Please:

* Clarify the task. Ask for missing information only when it could materially affect the analysis. If useful, ask me for representative images or examples of the expected result.
* Use appropriate methods. Prefer established, maintained software and documented APIs. Check current documentation rather than relying only on memory. If consequential behaviour remains unclear, inspect the source code when available rather than guessing.
* Check deep learning model suitability. If using a pre-trained model, consider whether my images match its training data, including image type, channels, dimensionality, object scale, preprocessing and post-processing.
* Write code according to best practices. Keep functions small and focused, use clear names and annotations, and separate consequential processing steps. Validate inputs, provide informative errors and do not use silent fallbacks.
* Make processing explicit. State important parameters, defaults and transformations, including resizing, resampling, normalisation, channel selection and post-processing. Preserve the original coordinate system and physical units unless a transformation is explicitly required and documented.
* Make the analysis testable. Test it on representative reference data where possible, save useful intermediate outputs and overlays, and use validation measures appropriate to the intended biological measurement rather than relying on a single generic score. Include a test I can run on my annotated example and tell me what result would mean that the analysis failed. If I ask for counts or measurements, return the masks or outlines they come from.
* Audit and challenge the result. Before finishing, assume that the analysis could be scientifically wrong even if the code runs and the output looks plausible. Identify the failure modes most likely to change the biological conclusion and suggest concrete tests or reference data that would expose them.

## assistant

I'll check the current Cellpose docs first, since the API changed between versions.

## assistant (tool call: WebFetch)

```json
{
 "url": "https://cellpose.readthedocs.io/en/latest/api.html",
 "prompt": "How to instantiate CellposeModel in Cellpose 4 (cpsam), eval() arguments (diameter, flow_threshold, cellprob_threshold, channels, normalize, batch_size), whether diameter is used, and the fine-tuning/training API (train_seg). Also CPU usage notes."
}
```

## assistant (tool call: WebSearch)

```json
{
 "query": "Cellpose-SAM cpsam brightfield endothelial monolayer segmentation fine-tune CPU",
 "mode": "standard"
}
```

## tool result

```
Web search results for query: "Cellpose-SAM cpsam brightfield endothelial monolayer segmentation fine-tune CPU"

Links: [{"title":"Cellpose-SAM: superhuman generalization for cellular segmentation","url":"https://www.biorxiv.org/content/10.1101/2025.04.28.651001.full.pdf"},{"title":"HyperBank: A Differentiable Bank of Classical Priors for Few-Shot Spheroid Microscopy Segmentation","url":"https://arxiv.org/pdf/2607.10684"},{"title":"Bridging Foundation Models and ASTM Metallurgical Standards for Automated Grain Size Estimation from Microscopy Images","url":"https://arxiv.org/pdf/2604.18957"},{"title":"mosaik-docs.readthedocs.io","url":"https://mosaik-docs.readthedocs.io/en/latest/segmentation.html"},{"title":"Cellpose SAM","url":"https://scrapbox.io/AokiLab/Cellpose-SAM"},{"title":"mosaik-docs.readthedocs.io","url":"https://mosaik-docs.readthedocs.io/en/stable/segmentation.html"},{"title":"mosaik-docs.readthedocs.io","url":"https://mosaik-docs.readthedocs.io/en/stable/_sources/segmentation.rst.txt"},{"title":"CellposeSAM for cellular segmentation [paper] [github] [talk]","url":"https://klimjoa1-cellpose.hf.space/"},{"title":"planitpurple.northwestern.edu","url":"https://planitpurple.northwestern.edu/event/629142"}]

The search turned up general Cellpose-SAM material but nothing specific to brightfield endothelial monolayers or CPU fine-tuning.

- **Architecture:** Cellpose-SAM keeps the pretrained SAM image encoder and drops the SAM decoder. A transposed convolution layer then predicts flow fields and cell probabilities, which feed Cellpose's gradient-tracking step (3-4,3-5).
- **Fine-tuning:** One paper fine-tuned the Cellpose-SAM generalist model on a small number of support images per dataset (2-12). The Cellpose ecosystem includes fine-tuning and human-in-the-loop training (9-7). I found no details on compute requirements for fine-tuning.
- **CPU inference:** A community tutorial runs the model on CPU by setting `models.CellposeModel(gpu=False)` and calling `model.eval` with flow and cell-probability thresholds (5-1). This shows inference, not training, on CPU.
- **Newer checkpoint:** A hosted demo mentions a model named 'cpsam_v2' updated in June 2026 (8-2). Check the Cellpose GitHub release notes to confirm which weights you should use.

Gaps: no source covered endothelial monolayer or brightfield segmentation, or the practical CPU training time. The Cellpose GitHub documentation and its fine-tuning guide are the next places to check.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
```

## tool result

```
**Instantiating CellposeModel (Cellpose 4, cpsam)**

The class signature is `CellposeModel(gpu=False, pretrained_model='cpsam_v2', model_type=None, diam_mean=None, device=None, nchan=None, use_bfloat16=True)`. The default pretrained model is `cpsam_v2`. The separate `__init__` listing shows older defaults (`pretrained_model=False`, `diam_mean=30.`), so the class signature is the better reference.

**eval() arguments**

- **batch_size**: Defaults to 8 in the signature. The parameter description says 64, which conflicts with that.
- **diameter**: Defaults to None. The docs say diameters are used to rescale the image to a 30-pixel cell diameter.
- **flow_threshold**: Defaults to 0.4. It is not used for 3D.
- **cellprob_threshold**: Defaults to 0.0. Lower values find more and larger masks.
- **channels**: Appears in the signature but is not described in the parameter list. The documented channel option is `channel_axis`.
- **normalize**: Defaults to True, scaling each channel between its 1st and 99th percentile intensities. It also accepts a dictionary of options.
- **bsize**: Must be 256 for cpsam. The docs say it cannot be changed for cpsam.

**Whether diameter is used**

Yes, when provided it is used to rescale the image. The `rescale` parameter applies only when `diameter` is None. The docs do not explicitly say whether `diameter` is ignored for cpsam.

**Training API (train_seg)**

- Signature: `cellpose.train.train_seg(net, train_data, train_labels, ...)`, with optional file paths, test sets, and probabilities.
- Defaults: `learning_rate=1e-5`, `n_epochs=100`, `weight_decay=0.1`, `batch_size=1`, `save_every=100`.
- `SGD` is deprecated, and AdamW is always used.
- For cpsam, `bsize` must be 256.
- bfloat16 models are converted to float32 for training. Saved models are float32, and the original model is returned in its original dtype.
- Returns a tuple of the saved model path, training losses, and test losses.

**CPU usage notes**

- `gpu=False` is the default, so the model runs on CPU unless GPU is requested.
- The `device` argument and `assign_device` helper select CPU, GPU, or mps.
- The excerpt contains no CPU-specific performance guidance, and the page content is truncated, so the full documentation may include more.

[WebFetch note: this page's text is 100080 characters long and the answer above covers only characters 0 to 100000; the final 80 were not read — to read on, call WebFetch again with the same url and offset: 100000.]
```

## assistant

# Approach for endothelial cell segmentation and shape measurement in brightfield

I haven't run any of this, because I can't execute code here and don't have your data. The Cellpose API details come from the current docs, which I checked. The CPU speed and accuracy claims are my expectations, not measurements.

## Recommendation

1. **Run Cellpose-SAM zero-shot first.** Use `CellposeModel` with the default pretrained weights, which are `cpsam_v2` in the current docs. Score it on your annotated image.
2. **Fine-tune only if the test below fails.** Use your manual labels, and hold out part of the image for testing.
3. **Don't use StarDist or a classical pipeline.** StarDist assumes star-convex shapes, which fits elongated or irregular endothelial cells poorly. Thresholding or watershed on brightfield fails because cell borders are faint and intensity isn't a reliable foreground signal.

Model suitability:
- Cellpose-SAM is a generalist model trained on many modalities. Brightfield monolayers are not its strongest case, so treat zero-shot performance as untested until you score it.
- Grayscale 2D input with no channel handling fits the model. The docs don't describe a `channels` argument for cpsam, so I don't pass one.
- The docs say `diameter` rescales cells to about 30 px, and they don't say whether cpsam needs it. Your cells are about 38–77 px (25–50 µm at 0.65 µm/px). I'd compare `diameter=None` with `diameter≈58` px (37.5 µm) on your annotation and keep whichever scores better.
- By default `normalize=True` rescales each image to its 1st–99th percentile. That handles your 12-bit uint16 data. Don't rescale to 16-bit yourself.
- On a CPU, inference is feasible but slow, since the encoder is a ViT with a fixed 256 px tile. Fine-tuning on a CPU will be slow. I couldn't find CPU training times, so test it on a small crop first.

## Questions that could change the analysis

These don't block the code below.
1. **Cancer cells:** should they be label 0, and does your annotation already exclude them? This is the main one. Without a rule, the model may label them as endothelial cells.
2. **Image size and count:** how large is each image, and how many are there? A single annotated image only supports a rough test.
3. **Contrast mode:** is this plain brightfield or phase-like? Please send one representative crop with your annotation overlaid if you can.
4. **Border cells:** I keep them in the label image but exclude them from shape statistics. Tell me if you want something different.

## Code

The code is in modules with small functions. It raises errors rather than falling back silently.

```python
"""Endothelial monolayer segmentation (Cellpose-SAM) and shape measurement."""
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy.optimize import linear_sum_assignment
from skimage.measure import regionprops_table
from skimage.segmentation import find_boundaries

PIXEL_SIZE_UM = 0.65


def load_image(path: Path) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    return image.astype(np.float32)  # values stay in the original 12-bit range


def segment(image: np.ndarray, diameter_px: float | None,
            flow_threshold: float = 0.4, cellprob_threshold: float = 0.0) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False)  # default pretrained weights
    masks = model.eval(image, diameter=diameter_px, normalize=True,
                       flow_threshold=flow_threshold,
                       cellprob_threshold=cellprob_threshold)[0]
    if masks.shape != image.shape:
        raise RuntimeError(f"Mask shape {masks.shape} != image shape {image.shape}")
    return masks.astype(np.int32)


def measure(labels: np.ndarray, pixel_size_um: float = PIXEL_SIZE_UM) -> pd.DataFrame:
    table = pd.DataFrame(regionprops_table(
        labels, properties=("label", "area", "major_axis_length",
                            "minor_axis_length", "bbox")))
    if table.empty:
        raise ValueError("No objects to measure")
    h, w = labels.shape
    table["area_um2"] = table["area"] * pixel_size_um**2
    # aspect ratio = major/minor axis of the ellipse with the same second moments (>= 1)
    table["aspect_ratio"] = table["major_axis_length"] / table["minor_axis_length"]
    table["touches_border"] = ((table["bbox-0"] == 0) | (table["bbox-1"] == 0) |
                               (table["bbox-2"] == h) | (table["bbox-3"] == w))
    return table[["label", "area_um2", "aspect_ratio", "touches_border"]]


def match_labels(truth: np.ndarray, pred: np.ndarray, iou_min: float = 0.5):
    """One-to-one matching of objects by IoU. Returns (truth_ids, pred_ids, ious)."""
    t_ids, p_ids = np.unique(truth[truth > 0]), np.unique(pred[pred > 0])
    t_idx = {v: i for i, v in enumerate(t_ids)}
    p_idx = {v: i for i, v in enumerate(p_ids)}
    overlap = np.zeros((len(t_ids), len(p_ids)))
    both = (truth > 0) & (pred > 0)
    for t, p in zip(truth[both], pred[both]):
        overlap[t_idx[t], p_idx[p]] += 1
    t_area = np.bincount(truth.ravel())[t_ids]
    p_area = np.bincount(pred.ravel())[p_ids]
    iou = overlap / (t_area[:, None] + p_area[None, :] - overlap)
    rows, cols = linear_sum_assignment(-iou)
    keep = iou[rows, cols] >= iou_min
    return t_ids[rows[keep]], p_ids[cols[keep]], iou[rows[keep], cols[keep]]


def evaluate(truth: np.ndarray, pred: np.ndarray) -> dict:
    t_tab = measure(truth).set_index("label")
    p_tab = measure(pred).set_index("label")
    t_ids, p_ids, _ = match_labels(truth, pred)
    tp = len(t_ids)
    fp, fn = len(p_tab) - tp, len(t_tab) - tp
    t_m, p_m = t_tab.loc[t_ids], p_tab.loc[p_ids]
    return {
        "n_true": len(t_tab), "n_pred": len(p_tab),
        "count_error_pct": 100 * (len(p_tab) - len(t_tab)) / len(t_tab),
        "F1@0.5": 2 * tp / (2 * tp + fp + fn),
        "median_area_rel_error_pct": float(np.median(
            100 * (p_m["area_um2"].values - t_m["area_um2"].values) / t_m["area_um2"].values)),
        "median_abs_aspect_error": float(np.median(
            np.abs(p_m["aspect_ratio"].values - t_m["aspect_ratio"].values))),
        "median_area_um2_true_vs_pred": (float(t_tab["area_um2"].median()),
                                         float(p_tab["area_um2"].median())),
        "median_aspect_true_vs_pred": (float(t_tab["aspect_ratio"].median()),
                                       float(p_tab["aspect_ratio"].median())),
    }


def save_outputs(out_dir: Path, image: np.ndarray, labels: np.ndarray, table: pd.DataFrame):
    out_dir.mkdir(parents=True, exist_ok=True)
    tifffile.imwrite(out_dir / "labels.tif", labels.astype(np.int32))
    table.to_csv(out_dir / "cells.csv", index=False)
    lo, hi = np.percentile(image, (1, 99))
    gray = np.clip((image - lo) / (hi - lo), 0, 1)
    overlay = np.stack([gray] * 3, axis=-1)
    overlay[find_boundaries(labels, mode="inner")] = (1, 0, 0)
    tifffile.imwrite(out_dir / "overlay.tif", (overlay * 255).astype(np.uint8))


if __name__ == "__main__":
    import sys
    image_path, truth_path, out = map(Path, sys.argv[1:4])
    image, truth = load_image(image_path), tifffile.imread(truth_path)
    if truth.shape != image.shape:
        raise ValueError("Annotation and image shapes differ")
    for name, diameter in {"auto": None, "58px": 58.0}.items():
        labels = segment(image, diameter)
        save_outputs(out / name, image, labels, measure(labels))
        print(name, evaluate(truth, labels))
```

Run it with `python script.py image.tif annotation.tif results/`. It writes `labels.tif`, `cells.csv` and `overlay.tif` for each setting, so every count and measurement can be traced to its mask.

## Test on your annotation

I suggest setting pass criteria before you look at the results. These numbers are my starting point, not a standard, so adjust them to the precision your biology needs.

**The analysis has failed if any of these holds:**
- `|count_error_pct|` is over 10%.
- F1@0.5 is under 0.8.
- `|median_area_rel_error_pct|` is over 10%.
- `median_abs_aspect_error` is over about 0.15.
- The overlay shows labels sitting on cancer cells.

Check the overlay by eye whatever the numbers say. F1 can look fine while all the borders are shifted. That shifts area and aspect ratio, and those are what you want to measure.

If you fine-tune, evaluate only on a region the model never saw. Split the image into spatial blocks and don't test on training crops. If you have only one image, report the result as a feasibility check and not as validation.

## Audit: how this could be wrong while looking fine

1. **Cancer cells counted as endothelial.** This inflates the count and distorts area and shape. Check the overlay specifically, or compare the area fraction of labels in cancer-cell regions to your annotation. If it's a problem, fine-tune with those regions left as label 0, or mask them first with a separate classifier.
2. **Over- or under-segmentation in faint-border regions.** Splits produce too many small cells and merges produce too few large ones. The two errors can cancel in the total count while area is still wrong. This is why the median area and the F1 score both matter.
3. **Border placement bias.** Systematic dilation or erosion by 1–3 px (0.65–2 µm) matters little for a 30 µm cell. It still shifts area by 10% or more, and it hits small cells hardest. Compare your area distribution with the annotation's.
4. **Annotation is not ground truth.** Brightfield borders are ambiguous. Have a second person annotate the same crop and compare them to each other. The model can't be expected to agree with your annotation better than they agree with each other.
5. **Aspect ratio definition.** I used the ellipse-fit ratio, major axis divided by minor axis. Bounding-box or Feret-based ratios give different numbers, so state your definition. For roughly round cells with ratios near 1, the measure is noisy.
6. **Border-touching cells.** These are truncated and bias area and aspect ratio. The `touches_border` column lets you exclude them from statistics.
7. **Generalisation.** One image, one condition, and one focus setting won't tell you how the method performs on other days, densities, or treatments. Annotate at least one more image from a different experiment and test on it.

Send me one representative crop with your annotation overlaid and I can tighten the cancer-cell strategy and the pass criteria.

Sources:
- [Cellpose API documentation](https://cellpose.readthedocs.io/en/latest/api.html)
- [Cellpose-SAM paper (bioRxiv)](https://www.biorxiv.org/content/10.1101/2025.04.28.651001.full.pdf)

## user

Count them as whole cells; their outline follows the cell junctions, including the part under the cancer cells. My images are 1024 × 1022 pixels (width × height), uint16. I have more fields of the same kind, from the same microscope and settings. Cells cut by the image border can be left out of the area and shape statistics. I don't have an example image to share in this conversation. I don't know.

## assistant (tool call: WebFetch)

```json
{
 "url": "https://cellpose.readthedocs.io/en/latest/train.html",
 "prompt": "Exact fine-tuning code example for Cellpose 4 / cpsam: how to create the model (models.CellposeModel), call train.train_seg with arguments (train_data, train_labels, test_data, test_labels, save_path, model_name, n_epochs, learning_rate, weight_decay, batch_size, channel handling), image shape/format requirements, label requirements, and how to load the fine-tuned model (pretrained_model=path). Also any CPU/GPU memory or time guidance and recommended number of training images."
}
```

## tool result

```
The page includes a notebook fine-tuning example, but it doesn't cover several things you asked about, including `save_path`, image shape requirements, channel handling, loading with `pretrained_model`, and memory, time, or dataset-size guidance.

**Notebook fine-tuning example**

```python
from cellpose import io, models, train
io.logger_setup()

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

**Setup details**

- **Model creation:** `models.CellposeModel(gpu=True)`, with `model.net` passed to `train.train_seg`.
- **Training call:** `train_seg` takes the training and test data and labels, `weight_decay`, `learning_rate`, `n_epochs`, and `model_name`. It returns the model path and the train and test losses.
- **Batch size:** The page documents `--train_batch_size` (default 1) for the CLI. The notebook example doesn't show a batch-size argument for `train_seg`.
- **Save location:** Models are saved in a `models/` folder inside the `--dir` directory. The CLI option `--model_name_out` sets the saved name. The page doesn't document a `save_path` argument.
- **Recommended CLI settings for fine-tuning Cellpose-SAM:** learning rate 0.00001, weight decay 0.1, 100 epochs, batch size 1.

**Image and label requirements**

- Image and mask files are paired by name. For example, `wells_000.tif` pairs with `wells_000_masks.tif`.
- Masks use 0 for background and 1, 2, … for each mask.
- `--mask_filter` and `--img_filter` change the suffixes. `--mask_filter _seg.npy` trains from GUI labels.
- Training images need at least `--min_train_masks` masks (default 5).
- The page doesn't specify image shape, dimensionality, or channel handling beyond the filename filters.
- Paths given to `--dir` and `--test_dir` should be absolute.

**Starting point and data**

- Start from the built-in cpsam model. Restarting from a previous retraining biases the model toward earlier images.
- Keep all images intended for one model in the same folder so they are all used.
- By default, images and ROIs are not resized. Test images should have a diameter distribution similar to the training data.

**Normalization when retraining**

- Normalization is applied per training image, often to crops. You can approximate per-crop normalization with `model.eval(..., normalize={"tile_norm_blocksize": 128})`.
- You can also change the scaling with `normalize={"percentile": [3, 98]}`. The training default is [1, 99].

**Not cover
```

## assistant

# Updated plan: fine-tune from the start, with a held-out-field test

Your answers change the plan in two ways.

- **Junctions under cancer cells are hidden in brightfield.** Your annotation draws them anyway, so the model has to infer them. Zero-shot Cellpose-SAM is unlikely to do that, since it was not trained to follow an outline through an occluding cell. I'd still run it once as a baseline, but I'd plan to **fine-tune** on your annotations.
- **You have more fields from the same microscope and settings.** That makes honest validation possible. Train on some fields, and test on **whole fields the model never saw**.

I'm treating "I don't know" about contrast mode as not blocking.

## Data plan

- **Annotate about 5–8 fields.** Include a range of cancer-cell coverage. This is my estimate. I couldn't find an official number of training images, so start small and check whether the held-out score improves as you add fields.
- **Hold out at least 2 whole fields** for testing, chosen before you look at any results. If you can only spare one, report it as a feasibility check.
- **Add a coarse cancer-cell mask to each annotated field.** A rough polygon or brush is enough. It is used only for evaluation. It lets me report separately how the model does on cells under cancer cells versus cells without one.
- **Annotate the covered cells consistently.** These outlines are your best guess at where the junctions are. They are less certain than the visible ones, so a second annotator on one field would show how reliable they are.
- **Array shape.** Your images are (Y, X) = (1022, 1024). The loader below enforces 2D, and you can add a shape check if every field is the same size.

## Fine-tuning

The training call below comes from the Cellpose docs. I couldn't confirm how `train_seg` handles image shapes or channels beyond the file-based loader, so I use that loader.

1. Folder layout: `train/fieldA_img.tif` and `train/fieldA_masks.tif`, and the same under `test/`.
2. Keep the learning rate at 1e-5, weight decay at 0.1 and batch size at 1. The docs recommend these for Cellpose-SAM. Start from the built-in cpsam weights each time, not from a previous fine-tune.
3. Smoke-test first with `n_epochs=2` and time it. I couldn't find CPU training times, so don't plan around 100 epochs until you've measured.

```python
from pathlib import Path
from cellpose import io, models, train

def finetune(train_dir: Path, test_dir: Path, n_epochs: int, model_name: str) -> Path:
    io.logger_setup()
    images, labels, _, test_images, test_labels, _ = io.load_train_test_data(
        str(train_dir), str(test_dir), image_filter="_img",
        mask_filter="_masks", look_one_level_down=False)
    model = models.CellposeModel(gpu=False)
    model_path, train_losses, test_losses = train.train_seg(
        model.net, train_data=images, train_labels=labels,
        test_data=test_images, test_labels=test_labels,
        weight_decay=0.1, learning_rate=1e-5,
        n_epochs=n_epochs, model_name=model_name)
    return Path(model_path)
```

To use the result, change `segment` to take a model path. The constructor has a `pretrained_model` argument, but I haven't confirmed that it accepts a fine-tuned file, so check this on first use.

```python
def segment(image, diameter_px, pretrained_model: str | None = None,
            flow_threshold=0.4, cellprob_threshold=0.0):
    from cellpose import models
    kwargs = {} if pretrained_model is None else {"pretrained_model": pretrained_model}
    model = models.CellposeModel(gpu=False, **kwargs)
    masks = model.eval(image, diameter=diameter_px, normalize=True,
                       flow_threshold=flow_threshold,
                       cellprob_threshold=cellprob_threshold)[0]
    if masks.shape != image.shape:
        raise RuntimeError(f"Mask shape {masks.shape} != image shape {image.shape}")
    return masks.astype(np.int32)
```

## Evaluation: split by cancer coverage and exclude border cells

This replaces `evaluate` from before and reuses `measure` and `match_labels`. It reports global F1 and count error, and recall and shape errors separately for covered and uncovered cells. Border-touching cells are excluded from the statistics, as you asked. A cell counts as covered when at least half its area lies inside the cancer mask. I chose that cutoff, so change `min_covered_fraction` if you disagree.

```python
from scipy import ndimage

def add_covered(table, labels, cancer_mask, min_covered_fraction=0.5):
    frac = ndimage.mean(cancer_mask.astype(float), labels, index=table["label"].values)
    return table.assign(covered=np.asarray(frac) >= min_covered_fraction)

def evaluate(truth, pred, cancer_mask, min_covered_fraction=0.5) -> dict:
    if not (truth.shape == pred.shape == cancer_mask.shape):
        raise ValueError("truth, pred and cancer_mask must have the same shape")
    t_tab = add_covered(measure(truth), truth, cancer_mask, min_covered_fraction).set_index("label")
    p_tab = measure(pred).set_index("label")
    t_ids, p_ids, _ = match_labels(truth, pred)
    t_nb = set(t_tab.index[~t_tab["touches_border"]])
    p_nb = set(p_tab.index[~p_tab["touches_border"]])
    tp = len(t_nb & set(t_ids))
    fn, fp = len(t_nb) - tp, len(p_nb) - len(p_nb & set(p_ids))
    result = {
        "n_true": len(t_nb), "n_pred": len(p_nb),
        "count_error_pct": 100 * (len(p_nb) - len(t_nb)) / len(t_nb),
        "F1@0.5": 2 * tp / (2 * tp + fp + fn),
        "labelled_fraction_true_vs_pred": (float((truth > 0).mean()), float((pred > 0).mean())),
    }
    pairs = pd.DataFrame({"t": t_ids, "p": p_ids})
    pairs = pairs[pairs["t"].isin(t_nb) & pairs["p"].isin(p_nb)]
    for name, covered in (("covered", True), ("uncovered", False)):
        stratum = set(t_tab.index[(t_tab["covered"] == covered) & ~t_tab["touches_border"]])
        sub = pairs[pairs["t"].isin(stratum)]
        t_m, p_m = t_tab.loc[sub["t"]], p_tab.loc[sub["p"]]
        result[name] = {
            "n_true": len(stratum),
            "recall@0.5": len(sub) / len(stratum) if stratum else float("nan"),
            "median_area_rel_error_pct": float(np.median(
                100 * (p_m["area_um2"].values - t_m["area_um2"].values) / t_m["area_um2"].values)) if len(sub) else float("nan"),
            "median_abs_aspect_error": float(np.median(
                np.abs(p_m["aspect_ratio"].values - t_m["aspect_ratio"].values))) if len(sub) else float("nan"),
        }
    return result
```

`labelled_fraction_true_vs_pred` is a sanity check. A confluent monolayer should be almost fully labelled, so a large gap means the model leaves holes or labels background.

## Pass and fail on the held-out fields

I picked these thresholds as sensible starting points, not standards. Set yours before you look at the results.

**The analysis has failed if, on the held-out fields:**
- Global F1@0.5 is under 0.8, or `|count_error_pct|` is over 10%.
- Covered-cell `recall@0.5` is under about 0.7. The model then can't find cells under cancer cells, and the count will be too low where the biology matters most.
- Covered cells have a median area error more than about 5 percentage points worse than uncovered cells. That means a bias specific to covered cells.
- Median area error is over 10% or median aspect error is over about 0.15 in either group.
- The predicted labelled fraction is far below the annotation's.
- The overlay shows cancer cells labelled as a single endothelial cell, or holes under them.

Always check the overlay as well. For a confluent layer, also try a lower `cellprob_threshold` such as -1. Tune it on the training fields only, never on the test fields.

## Audit: what could mislead you

1. **Under cancer cells, you may be measuring the annotator's guess.** The junctions there can't be seen, so the model can only learn the annotator's habits, such as a tendency toward polygonal, roughly equal-sized cells. Any difference in shape between covered and uncovered cells could come from that prior and not from biology. The best check is an independent readout of the same fields, such as a junction stain like VE-cadherin or a fluorescence image of the same field. Compare the model's covered-cell outlines against that.
2. **Leakage inflates scores.** Don't split one field into train and test crops, because neighbouring cells look alike. Split by whole field, and by experiment day if you can.
3. **Cancer-cell density may differ between fields.** If your question is how cancer cells change endothelial shape, make sure the test fields span low and high coverage. Otherwise the covered stratum is small and its statistics are noisy.
4. **Cancer cells can look like an endothelial cell to the model.** The model may draw one object around a cancer cell and miss the 2–3 cells beneath it. The covered recall and the area error will show this.
5. **Annotation reliability.** Have a second person annotate one field, especially covered regions. If the two annotators disagree with each other as much as the model disagrees with either, the model is within the noise.
6. **Aspect ratio and area definitions.** I use the ellipse-fit ratio, major axis divided by minor axis, and area in µm² at 0.65 µm/px. Report these definitions with your results.
7. **Batch effects.** The same microscope and settings help. A new focus setting, passage number, or cell density can still shift performance, so retest with each new batch.

If you tell me how many fields you can annotate and whether a junction stain exists for them, I can adjust the train/test split and the validation plan.

Sources:
- [Cellpose API documentation](https://cellpose.readthedocs.io/en/latest/api.html)
- [Cellpose training documentation](https://cellpose.readthedocs.io/en/latest/train.html)
