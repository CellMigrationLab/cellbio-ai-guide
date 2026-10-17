"""Export the BF / Pix2Pix / ground-truth crops used in panels A and B (linear display only, no processing)."""
import numpy as np
import tifffile
from PIL import Image
from scipy import ndimage as ndi
from skimage.segmentation import find_boundaries

from common.paths import RAW as U
OFF = 1  # 1024-row Pix2Pix files carry one padded row at the top (DAPI cross-correlation peak at a 1-row shift)
bf = tifffile.imread(U + "field104_brightfield.tif").astype(np.float64)                 # 1022 x 1024, 0.649614 um/px
gt_d = tifffile.imread(U + "field104_dapi.tif").astype(np.float64)           # acquired DAPI
gt_p = tifffile.imread(U + "field104_pecam1.tif").astype(np.float64)          # acquired PECAM
pr_d = tifffile.imread(U + "field104_pix2pix_predicted_dapi.tif")[OFF:OFF + 1022]           # Pix2Pix DAPI
pr_p = tifffile.imread(U + "field104_pix2pix_predicted_pecam1.tif")[OFF:OFF + 1022]         # Pix2Pix PECAM
cancer = tifffile.imread(U + "field104_cancer_cells_stardist_custom_labels.tif").astype(int)        # StarDist on BF

X, Y, W, H = 200, 0, 210, 280             # shared crop for A and B
SX, SY, SW, SH = 60, 140, 100, 135         # crop-local sub-crop for the step-2 tiles (clearest acquired junctions)


def crop(a, sub=False):
    c = a[Y:Y + H, X:X + W]
    return c[SY:SY + SH, SX:SX + SW] if sub else c


def lin(a, ref):
    """Linear display: 0.3-99.7th percentile of the reference crop -> 0-1."""
    lo, hi = np.percentile(ref, [0.3, 99.7])
    return np.clip((a - lo) / (hi - lo), 0, 1), (float(lo), float(hi))


def save(arr, name, up=1):
    if up > 1:
        arr = np.repeat(np.repeat(arr, up, 0), up, 1)
    Image.fromarray(np.round(np.clip(arr, 0, 1) * 255).astype(np.uint8)).save("data3/" + name, optimize=True)


log = {}
b, log["BF"] = lin(crop(bf), crop(bf))
save(b, "A_bf.png")

# A output: StarDist labels drawn over the (dimmed) brightfield: 35 % fill + solid outline, 3x nearest upsampling
COLS = ["#ff4fa3", "#ffd23f", "#3ec1ff", "#b07cff", "#2ee59d", "#ff7a3d", "#ff3d5a", "#44e0d6", "#a8f03e", "#5a8bff"]
UP = 3
lab = np.repeat(np.repeat(crop(cancer), UP, 0), UP, 1)
base = np.repeat(np.repeat(b, UP, 0), UP, 1)
ov = np.stack([0.25 + 0.6 * base] * 3, -1)
edge = ndi.binary_dilation(find_boundaries(lab, mode="inner"), iterations=1)
for i, l in enumerate(np.unique(lab[lab > 0])):
    c = np.array([int(COLS[i % len(COLS)][k:k + 2], 16) / 255 for k in (1, 3, 5)])
    m = lab == l
    ov[m] = 0.65 * ov[m] + 0.35 * c
    ov[m & edge] = c
save(ov, "A_cancer_labels_overlay.png")


def composite(d, p):
    """DAPI -> magenta, PECAM -> green (additive)."""
    return np.stack([d, p, d], -1)


d, log["pred DAPI"] = lin(crop(pr_d), crop(pr_d))
p, log["pred PECAM"] = lin(crop(pr_p), crop(pr_p))
save(composite(d, p), "B_predicted_composite.png")
for tag, dd, pp in [("predicted", pr_d, pr_p), ("acquired", gt_d, gt_p)]:
    d, log[f"{tag} DAPI tile"] = lin(crop(dd, True), crop(dd))
    p, log[f"{tag} PECAM tile"] = lin(crop(pp, True), crop(pp))
    save(composite(d, p), f"B_tile_{tag}.png")

n_in = len(np.unique(crop(cancer))) - 1
r = {k: round(float(np.corrcoef(crop(a).ravel(), crop(g).ravel())[0, 1]), 3)
     for k, a, g in [("DAPI", pr_d, gt_d), ("PECAM", pr_p, gt_p)]}
print("display ranges:", {k: [round(v, 3) for v in lr] for k, lr in log.items()})
print("cancer objects in crop:", n_in, "| pixel correlation predicted vs acquired in crop:", r)

# Step-2 tiles: green PECAM (predicted / acquired) + Cellpose cells segmented on the predicted PECAM as vector contours
import json
from skimage.measure import find_contours, approximate_polygon
cells = tifffile.imread(U + "field104_pix2pix_pecam1_cellpose_cell_labels.tif")[OFF:OFF + 1022].astype(int)   # Cellpose on predicted PECAM
for tag, pp in [("predicted", pr_p), ("acquired", gt_p)]:
    g, _ = lin(crop(pp, True), crop(pp))
    save(np.stack([0.12 * g, g, 0.12 * g], -1), f"B_PECAM_{tag}.png", up=2)
sub = crop(cells, True)
contours = []
for l in np.unique(sub[sub > 0]):
    m = np.pad(sub == l, 1)
    for cnt in find_contours(m.astype(float), 0.5):
        cnt = approximate_polygon(cnt - 1, tolerance=0.6)          # back to sub-crop pixel coords (row, col)
        contours.append([[round(float(c), 2), round(float(r), 2)] for r, c in cnt])  # [x, y]
json.dump({"w": SW, "h": SH, "contours": contours}, open("data3/B_cells_contours.json", "w"))
print("Cellpose cells in step-2 sub-crop:", len(np.unique(sub)) - 1, "contours:", len(contours))

# annotator 1 outlines (drawn on acquired PECAM) for the same sub-crop, as cell contours
from skimage.measure import label as cc_label
from skimage.segmentation import expand_labels
a1 = tifffile.imread(U + "field104_endothelial_junctions_annotator1.tif") > 0
L1 = expand_labels(cc_label(~a1, connectivity=1), 2)
sub = crop(L1, True)
contours = []
for l in np.unique(sub[sub > 0]):
    m = np.pad(sub == l, 1)
    if m.sum() < 30:
        continue
    for cnt in find_contours(m.astype(float), 0.5):
        cnt = approximate_polygon(cnt - 1, tolerance=0.6)
        contours.append([[round(float(c), 2), round(float(r), 2)] for r, c in cnt])
json.dump({"w": SW, "h": SH, "contours": contours}, open("data3/B_annotator1_contours.json", "w"))
print("annotator-1 cells in step-2 sub-crop:", len(np.unique(sub)) - 1)


def contours_json(L, path, sub_xy=(SX, SY), size=(SW, SH)):
    sx_, sy_ = sub_xy
    sub = L[Y + sy_:Y + sy_ + size[1], X + sx_:X + sx_ + size[0]]
    out = []
    for l in np.unique(sub[sub > 0]):
        m = np.pad(sub == l, 1)
        if m.sum() < 30:
            continue
        for cnt in find_contours(m.astype(float), 0.5):
            cnt = approximate_polygon(cnt - 1, tolerance=0.6)
            out.append([[round(float(c), 2), round(float(r), 2)] for r, c in cnt])
    json.dump({"w": size[0], "h": size[1], "contours": out}, open(path, "w"))
    return len(np.unique(sub)) - 1


# annotator 2 (PECAM) on the step-2 sub-crop
a2 = tifffile.imread(U + "field104_endothelial_junctions_annotator2.tif") > 0
print("annotator-2 cells in sub-crop:", contours_json(expand_labels(cc_label(~a2, connectivity=1), 2), "data3/B_annotator2_contours.json"))

# nuclei tile: manual HUVEC nuclei vs StarDist on predicted DAPI, on acquired DAPI; pick a sub-crop with cancer cells
nuc_ref = tifffile.imread(U + "field104_endothelial_nuclei_manual_labels.tif").astype(int)
nuc_sd = tifffile.imread(U + "field104_pix2pix_dapi_stardist_nuclei_labels.tif")[OFF:OFF + 1022].astype(int)
canc = tifffile.imread(U + "field104_cancer_cells_manual_labels.tif") > 0
best = None
for sy_ in range(0, H - SH + 1, 5):
    for sx_ in range(0, W - SW + 1, 5):
        win = (slice(Y + sy_, Y + sy_ + SH), slice(X + sx_, X + sx_ + SW))
        score = canc[win].mean() * 2 + len(np.unique(nuc_ref[win])) / 30
        if best is None or score > best[0]:
            best = (score, sx_, sy_)
NX, NY = best[1], best[2]
# display range from HUVEC-nucleus pixels only (bright cancer-cell nuclei saturate; noted in the legend)
huv = crop(gt_d)[(crop(nuc_ref) > 0) & ~crop(canc)]
lo_n, hi_n = np.percentile(crop(gt_d), 0.3), np.percentile(huv, 99.5)
d = np.clip((gt_d[Y + NY:Y + NY + SH, X + NX:X + NX + SW] - lo_n) / (hi_n - lo_n), 0, 1)
print(f"nuclei tile DAPI display {lo_n:.0f}-{hi_n:.0f}; saturated fraction {(d >= 1).mean():.3f}")
save(np.stack([d, d, d], -1), "B_DAPI_acquired_nuclei_tile.png", up=2)   # greyscale so outlines read
n1 = contours_json(nuc_ref, "data3/B_nuclei_manual_contours.json", (NX, NY))
n2 = contours_json(nuc_sd, "data3/B_nuclei_stardist_contours.json", (NX, NY))
print(f"nuclei tile sub-crop x {NX}-{NX+SW}, y {NY}-{NY+SH} (crop-local); manual {n1}, StarDist(pred) {n2}")

# panel A reference comparison as vector outlines on the shared crop
ca = tifffile.imread(U + "field104_cancer_cells_manual_labels.tif").astype(int)
print("A crop: manual", contours_json(ca, "data3/A_manual_contours.json", (0, 0), (W, H)),
      "| StarDist", contours_json(cancer, "data3/A_stardist_contours.json", (0, 0), (W, H)))
