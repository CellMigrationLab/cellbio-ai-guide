# code_specific_prompt

## USER (2026-10-16T18:00:46.882Z)

Act as a helpful coding assistant for a cell biologist. Do not use any tools (no files, no code execution).

The user writes: "Please write a Python script to segment the nuclei in nuclei.tif using Cellpose (I have Cellpose 4 installed, CPU only). The image is a single-channel 2D DAPI image (Y, X), 16-bit, pixel size 0.65 µm; nuclei are about 10–20 µm across and some touch. Do not resize or normalise the image yourself. Save the label image as labels.tif and the nuclear areas in µm² as areas.csv, and print the number of nuclei."

Reply with one complete script in a single ```python block and nothing else.

## HARNESS NOTE (2026-10-16T18:00:46.909Z)

<system-reminder>
Your final report is delivered through SubagentHandback: when your work is complete, call SubagentHandback({message: <your full report>}). The call ends your run, so make it your last step. Only a SubagentHandback call reaches your caller as your result; plain text you write at the end is not delivered. Do not also send the report with SendMessage: your caller would get it twice.
</system-reminder>

## ASSISTANT (final report)

```python
import numpy as np
import pandas as pd
import tifffile
from cellpose import models
from skimage.measure import regionprops

PIXEL_SIZE_UM = 0.65

# Load the image as-is (single-channel 2D, Y x X, 16-bit). No resizing or normalisation here.
img = tifffile.imread("nuclei.tif")
if img.ndim != 2:
    raise ValueError(f"Expected a 2D (Y, X) image, got shape {img.shape}")

# Cellpose 4 (Cellpose-SAM) on CPU. The default pretrained model is used.
# No diameter is passed, so Cellpose does not rescale the image; the model
# handles the nuclear size range here (about 15-30 px across) without it.
# Cellpose applies its own internal intensity normalisation by default.
model = models.CellposeModel(gpu=False)
masks, flows, styles = model.eval(img)

# Save the label image (0 = background, 1..N = nuclei)
n_nuclei = int(masks.max())
label_dtype = np.uint16 if n_nuclei < 65535 else np.uint32
tifffile.imwrite("labels.tif", masks.astype(label_dtype))

# Nuclear areas in um^2 (pixel count * pixel area)
pixel_area_um2 = PIXEL_SIZE_UM ** 2
rows = [
    {"label": int(p.label), "area_um2": float(p.area * pixel_area_um2)}
    for p in regionprops(masks)
]
pd.DataFrame(rows, columns=["label", "area_um2"]).to_csv("areas.csv", index=False)

print(f"Number of nuclei: {len(rows)}")
```
