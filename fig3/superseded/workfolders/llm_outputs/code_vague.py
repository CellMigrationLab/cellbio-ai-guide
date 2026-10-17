import csv
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import filters, measure, morphology, segmentation, feature

IMAGE_PATH = "nuclei.tif"
OUTPUT_CSV = "areas.csv"
PIXEL_SIZE_UM = None   # set e.g. 0.325 (um/pixel) to also report area in um^2
MIN_AREA_PX = 30       # discard debris smaller than this (pixels)

# Load image; reduce to 2D if it is a stack or multichannel
img = tifffile.imread(IMAGE_PATH)
if img.ndim > 2:
    print(f"Image has shape {img.shape}; using a max projection over leading axes.")
    while img.ndim > 2:
        img = img.max(axis=0)
img = img.astype(np.float32)

# Smooth and subtract background
smooth = filters.gaussian(img, sigma=1)
background = filters.gaussian(img, sigma=50)
corrected = smooth - background
corrected[corrected < 0] = 0

# Otsu threshold
mask = corrected > filters.threshold_otsu(corrected)
mask = morphology.remove_small_objects(mask, MIN_AREA_PX)
mask = ndi.binary_fill_holes(mask)

# Split touching nuclei with a distance-transform watershed
distance = ndi.distance_transform_edt(mask)
distance_smooth = filters.gaussian(distance, sigma=2)
coords = feature.peak_local_max(distance_smooth, min_distance=7, labels=measure.label(mask))
markers = np.zeros(mask.shape, dtype=int)
markers[tuple(coords.T)] = np.arange(1, len(coords) + 1)
labels = segmentation.watershed(-distance_smooth, markers, mask=mask)

# Remove nuclei touching the image border (incomplete nuclei)
labels = segmentation.clear_border(labels)

# Measure areas
props = [p for p in measure.regionprops(labels) if p.area >= MIN_AREA_PX]

with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.writer(f)
    header = ["nucleus_id", "area_px"]
    if PIXEL_SIZE_UM:
        header.append("area_um2")
    writer.writerow(header)
    for i, p in enumerate(props, start=1):
        row = [i, int(p.area)]
        if PIXEL_SIZE_UM:
            row.append(round(p.area * PIXEL_SIZE_UM ** 2, 3))
        writer.writerow(row)

areas = np.array([p.area for p in props])
print(f"Measured {len(props)} nuclei. Median area: {np.median(areas):.1f} px. Saved to {OUTPUT_CSV}")
