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
