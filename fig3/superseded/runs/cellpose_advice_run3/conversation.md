# cellpose_advice_run3

## USER (2026-10-16T17:20:15.256Z)

Act as a helpful assistant answering a cell biologist. Do not use any tools: no file reading, no web search, no code execution. Answer from your own knowledge only.

The user writes:
"How should I segment nuclei in 2D fluorescence (DAPI) images with Cellpose in Python? Which model and parameters should I use? Please give a short code example."

Reply as you normally would, including the code example.

## HARNESS NOTE (2026-10-16T17:20:15.290Z)

<system-reminder>
Your final report is delivered through SubagentHandback: when your work is complete, call SubagentHandback({message: <your full report>}). The call ends your run, so make it your last step. Only a SubagentHandback call reaches your caller as your result; plain text you write at the end is not delivered. Do not also send the report with SendMessage: your caller would get it twice.
</system-reminder>

## ASSISTANT (final report)

**Short answer:** for DAPI nuclei in 2D, start with Cellpose's `nuclei` model, or `cyto3` if you are on Cellpose 3 and the nuclei are dense or have mixed brightness. Set `diameter` to your nuclei size in pixels. Then adjust `flow_threshold` and `cellprob_threshold` only if the result looks wrong. This is from memory, so check the current docs for your installed version, because the API changed between releases.

**Model choice**
- **`nuclei`** is the classic specialist model and a good default for DAPI/Hoechst.
- **`cyto3`** (Cellpose 3) is a more general model and often copes better with dense or heterogeneous nuclei. Cellpose 3 also has denoising/restoration models (e.g. `denoise_cyto3`) for noisy or low-signal images.
- **Cellpose-SAM** (Cellpose 4, `cpsam`) is a single generalist model. It is largely size-agnostic, so you usually don't need to set `diameter`. If you have Cellpose 4, try it first.
- If none of these work on your data, fine-tune on a few of your own annotated images using the GUI or the training API. This usually helps more than tuning parameters.

**Key parameters**
- **`diameter`:** the typical nucleus diameter in pixels. This matters most. Measure a few nuclei in Fiji. Use `None` to auto-estimate, which works less reliably for nuclei. For `nuclei` the training size is about 17 px, so images are rescaled to match.
- **`flow_threshold`** (default 0.4): lower it to discard more doubtful masks, raise it to keep more. Raise it (e.g. 0.6 to 1.0) if real nuclei are missing.
- **`cellprob_threshold`** (default 0.0, range about -6 to 6): lower it (e.g. -2) to get larger masks and more detected objects. Raise it to shrink masks or remove dim false positives.
- **`channels`:** for a single-channel grayscale DAPI image use `[0, 0]` (Cellpose 3 and earlier). Cellpose 4 ignores or deprecates this argument.
- **`min_size`** (default 15): removes tiny objects.
- **`normalize`:** the default percentile normalisation is usually fine. Adjust it if the brightness varies a lot across the image.
- **`gpu=True`** if you have a CUDA GPU, which is much faster.

**Example (Cellpose 3.x)**

```python
import numpy as np
from skimage import io
from cellpose import models, plot
import matplotlib.pyplot as plt

img = io.imread("dapi.tif")          # 2D array (Y, X)

model = models.Cellpose(gpu=True, model_type="nuclei")   # or "cyto3"

masks, flows, styles, diams = model.eval(
    img,
    diameter=30,               # nucleus diameter in pixels; None = auto-estimate
    channels=[0, 0],           # grayscale
    flow_threshold=0.4,
    cellprob_threshold=0.0,
    min_size=15,
)

print(f"{masks.max()} nuclei detected")
io.imsave("dapi_masks.tif", masks.astype(np.uint16))

fig = plt.figure(figsize=(10, 5))
plot.show_segmentation(fig, img, masks, flows[0])
plt.show()
```

In newer Cellpose 3 releases, `models.CellposeModel(gpu=True, model_type="nuclei")` is the usual class, and it returns three values instead of four:

```python
model = models.CellposeModel(gpu=True, model_type="nuclei")
masks, flows, styles = model.eval(img, diameter=30, channels=[0, 0])
```

**Example (Cellpose 4 / Cellpose-SAM)**

```python
from cellpose import models
model = models.CellposeModel(gpu=True)   # loads cpsam by default
masks, flows, styles = model.eval(img, flow_threshold=0.4, cellprob_threshold=0.0)
```

**Practical tips**
- Check the result by overlaying the outlines on the image. Don't judge by the mask count alone.
- If touching nuclei are merged, lower `diameter` a little and raise `flow_threshold`. If single nuclei are split, increase `diameter`.
- If dim nuclei are missed, lower `cellprob_threshold` (e.g. -1 to -3).
- For large images or tiles, Cellpose tiles automatically. For many images, pass a list of images to `eval` or use the batch/CLI mode (`python -m cellpose --dir ... --pretrained_model nuclei --diameter 30 --save_tif`).
- Save the label image as 16-bit (or 32-bit if you have more than 65,535 objects). You can then measure intensity and shape with `skimage.measure.regionprops_table`.
