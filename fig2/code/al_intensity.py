"""Panel d, measurement itself: predicted vs acquired intensity per object, whole field.
DAPI: mean intensity per manually annotated HUVEC nucleus (field104_endothelial_nuclei_manual_labels.tif). PECAM-1:
mean intensity in a 3-px band along the border of each cell outlined by annotator 1
(field104_endothelial_junctions_annotator1.tif, regions enclosed by the drawn lines). Each channel is background-
subtracted (median outside the objects / outside the junction bands) and the two images are compared by Pearson r.
Predicted images: rows 1-1022 of the pix2pix output (1-row padding offset). Also exports the full-field display images."""
import json
import numpy as np
import tifffile
from PIL import Image
from skimage.measure import label, regionprops
from skimage.segmentation import clear_border, expand_labels, find_boundaries

from common.paths import RAW as U
from common.pix2pix import read_pix2pix
acq_d = tifffile.imread(U + "field104_dapi.tif").astype(float)
acq_p = tifffile.imread(U + "field104_pecam1.tif").astype(float)
prd_d = read_pix2pix("field104_pix2pix_predicted_dapi.tif").astype(float)
prd_p = read_pix2pix("field104_pix2pix_predicted_pecam1.tif").astype(float)
nuc = tifffile.imread(U + "field104_endothelial_nuclei_manual_labels.tif").astype(int)
lines = tifffile.imread(U + "field104_endothelial_junctions_annotator1.tif") > 0
cells = clear_border(expand_labels(label(~lines, connectivity=1), 2))
sizes = np.bincount(cells.ravel())
cells[np.isin(cells, np.where(sizes < 150)[0])] = 0
band = expand_labels(np.where(find_boundaries(cells, mode="inner"), cells, 0), 1)      # ~3-px junction band per cell
band[cells == 0] = 0


def per_object(img, lab, bgmask):
    bg = np.median(img[bgmask])
    return np.array([r.intensity_mean - bg for r in regionprops(lab, intensity_image=img)])


out = {}
for key, lab, a, p, bgm in [("DAPI", nuc, acq_d, prd_d, nuc == 0), ("PECAM-1", band, acq_p, prd_p, band == 0)]:
    xa, xp = per_object(a, lab, bgm), per_object(p, lab, bgm)
    out[key] = {"n": int(len(xa)), "r": round(float(np.corrcoef(xa, xp)[0, 1]), 3),
                "acquired": np.round(xa, 3).tolist(), "predicted": np.round(xp, 4).tolist()}
    print(key, out[key]["n"], out[key]["r"])
json.dump(out, open("panels/al_intensity.json", "w"))


def lin(x):
    lo, hi = np.percentile(x, [0.3, 99.7])
    return np.clip((x - lo) / (hi - lo), 0, 1)


bf = tifffile.imread(U + "field104_brightfield.tif").astype(float)
g = lin(bf)
Image.fromarray((np.stack([g] * 3, -1) * 255).astype(np.uint8)).save("panels/al_bf_full.png")
d, p_ = lin(prd_d), lin(prd_p)
Image.fromarray((np.stack([d, p_, d], -1) * 255).astype(np.uint8)).save("panels/al_pred_full.png")
print("full images", bf.shape)
