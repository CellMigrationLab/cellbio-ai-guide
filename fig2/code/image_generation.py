"""Data for panels c and e. Denoising (panel c): nuclei segmented on the restored image, outlines reused on the acquired image, and per-nucleus
mean intensity in both. Super-resolution (panel e): low-res input, prediction and acquired high-res image of the same region."""
import json
import numpy as np
import tifffile
from PIL import Image
from scipy import ndimage as ndi
from skimage import filters, measure, morphology, segmentation, feature
from export_window import contours

from common.paths import RAW as U
from common.metadata import BIOSR_GRID_PX_NM, BIOSR_LOWRES_PX_NM
from common.stats import pearson_r
def lin(a, p=(0.3, 99.7)):
    lo, hi = np.percentile(a, p)
    return np.clip((a - lo) / (hi - lo), 0, 1)


def save(a, path, k=2):
    Image.fromarray(np.round(np.repeat(np.repeat(a, k, 0), k, 1) * 255).astype(np.uint8)).save(path)


# ---- denoising (CARE output provided by the authors), 0.6337 µm/px
raw = tifffile.imread(U + "care_denoising_acquired.tif").astype(float)
den = tifffile.imread(U + "care_denoising_restored.tif").astype(float)
m = den > filters.threshold_otsu(den)
m = morphology.remove_small_objects(morphology.binary_opening(m, morphology.disk(1)), 30)
dist = ndi.distance_transform_edt(m)
pk = feature.peak_local_max(dist, min_distance=5, labels=measure.label(m), exclude_border=False)
mk = np.zeros_like(m, int)
mk[tuple(pk.T)] = np.arange(1, len(pk) + 1)
lab = segmentation.watershed(-dist, mk, mask=m)
y, x, n = 640, 520, 200
save(lin(raw[y:y + n, x:x + n]), "panels/dn_acquired.png")
save(lin(den[y:y + n, x:x + n]), "panels/dn_restored.png")
json.dump({"w": n, "h": n, "contours": contours(lab, x, y, n, n)}, open("panels/dn_mask.json", "w"))
props_r = measure.regionprops(lab, intensity_image=raw)
props_d = measure.regionprops(lab, intensity_image=den)
ir = np.array([p.intensity_mean for p in props_r])
idn = np.array([p.intensity_mean for p in props_d])
bg_r, bg_d = np.median(raw[~m]), np.median(den[~m])
json.dump({"n_nuclei": int(lab.max()), "acquired": ir.round(1).tolist(), "restored": idn.round(1).tolist(),
           "r": round(pearson_r(ir, idn, name="denoising per nucleus"), 3), "bg_acquired": float(bg_r), "bg_restored": float(bg_d),
           "ratio_median": round(float(np.median((idn - bg_d) / (ir - bg_r))), 3)},
          open("panels/dn_intensity.json", "w"))
print("denoise nuclei", lab.max(), "r", np.corrcoef(ir, idn)[0, 1], "bg", bg_r, bg_d)

# ---- super-resolution: same region as Fig. 1a. BioSR pixel sizes (Qiao et al. 2021; not in the TIFF metadata):
# low-res input 62.6 nm/px (502 x 502); prediction and high-res reference on the 2x grid, 31.3 nm/px (1004 x 1004)
lr = tifffile.imread(U + "biosr_er_lowres_input.tif").astype(float)
pr = tifffile.imread(U + "biosr_er_rcan_prediction.tif").astype(float)
hr = tifffile.imread(U + "biosr_er_highres_reference.tif").astype(float)
y, x, n = 160, 600, 140
a = lin(lr[y // 2:y // 2 + n // 2, x // 2:x // 2 + n // 2])
save(a, "panels/sr_input.png", 6)
save(lin(pr[y:y + n, x:x + n]), "panels/sr_predicted.png", 3)
save(lin(hr[y:y + n, x:x + n]), "panels/sr_hr.png", 3)
np.save("panels/sr_pred_crop.npy", pr[y:y + n, x:x + n]); np.save("panels/sr_hr_crop.npy", hr[y:y + n, x:x + n])
print("sr ok")

# line profile across ER tubules: row 85 of the crop (3-row mean). Its predicted-vs-high-res correlation (0.93) is at the
# 15th percentile of rows 15-120 (median 0.95), computed below: a typical row, not a favourable choice.
ROW = 85
row_r = lambda R: np.corrcoef(pr[y + R - 1:y + R + 2, x:x + n].mean(0), hr[y + R - 1:y + R + 2, x:x + n].mean(0))[0, 1]
all_r = np.array([row_r(R) for R in range(15, 121)])
print(f"profile row {ROW}: r {row_r(ROW):.3f}, percentile {100 * (all_r < row_r(ROW)).mean():.0f} of rows 15-120 "
      f"(median r {np.median(all_r):.3f})")
nz = lambda a: (a - a.min()) / (a.max() - a.min())
P = nz(pr[y + ROW - 1:y + ROW + 2, x:x + n].mean(0))
Hh = nz(hr[y + ROW - 1:y + ROW + 2, x:x + n].mean(0))
L = nz(np.repeat(lr[(y + ROW) // 2, x // 2:x // 2 + n // 2], 2))
json.dump({"row": ROW, "px_nm": BIOSR_GRID_PX_NM, "lowres_px_nm": BIOSR_LOWRES_PX_NM, "predicted": P.round(3).tolist(), "high_res": Hh.round(3).tolist(), "low_res": L.round(3).tolist(),
           "r_pred_hr": round(pearson_r(P, Hh, name="line profile"), 3)}, open("panels/sr_profile.json", "w"))
