"""Panel g data. Denoising: nuclei segmented on the restored image, outlines reused on the acquired image, and per-nucleus
mean intensity in both. Super-resolution: low-res input, prediction and acquired high-res image of the same region."""
import json
import numpy as np
import tifffile
from PIL import Image
from scipy import ndimage as ndi
from skimage import filters, measure, morphology, segmentation, feature
from export_window import contours

from common.paths import RAW as U
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
save(lin(raw[y:y + n, x:x + n]), "data/dn_acquired.png")
save(lin(den[y:y + n, x:x + n]), "data/dn_restored.png")
json.dump({"w": n, "h": n, "contours": contours(lab, x, y, n, n)}, open("data/dn_mask.json", "w"))
props_r = measure.regionprops(lab, intensity_image=raw)
props_d = measure.regionprops(lab, intensity_image=den)
ir = np.array([p.intensity_mean for p in props_r])
idn = np.array([p.intensity_mean for p in props_d])
bg_r, bg_d = np.median(raw[~m]), np.median(den[~m])
json.dump({"n_nuclei": int(lab.max()), "acquired": ir.round(1).tolist(), "restored": idn.round(1).tolist(),
           "r": round(float(np.corrcoef(ir, idn)[0, 1]), 3), "bg_acquired": float(bg_r), "bg_restored": float(bg_d),
           "ratio_median": round(float(np.median((idn - bg_d) / (ir - bg_r))), 3)},
          open("data/dn_intensity.json", "w"))
print("denoise nuclei", lab.max(), "r", np.corrcoef(ir, idn)[0, 1], "bg", bg_r, bg_d)

# ---- super-resolution: same region as Fig. 1a (HR px 62.6 nm; LR = HR / 2)
lr = tifffile.imread(U + "biosr_er_lowres_input.tif").astype(float)
pr = tifffile.imread(U + "biosr_er_rcan_prediction.tif").astype(float)
hr = tifffile.imread(U + "biosr_er_highres_reference.tif").astype(float)
y, x, n = 160, 600, 140
a = lin(lr[y // 2:y // 2 + n // 2, x // 2:x // 2 + n // 2])
save(a, "data/sr_input.png", 6)
save(lin(pr[y:y + n, x:x + n]), "data/sr_predicted.png", 3)
save(lin(hr[y:y + n, x:x + n]), "data/sr_hr.png", 3)
np.save("data/sr_pred_crop.npy", pr[y:y + n, x:x + n]); np.save("data/sr_hr_crop.npy", hr[y:y + n, x:x + n])
print("sr ok")

# line profile across ER tubules: row 85 of the crop (3-row mean); its predicted-vs-high-res correlation is near the
# median over rows 15-120, so it is a typical row, not a selected best or worst case
ROW = 85
nz = lambda a: (a - a.min()) / (a.max() - a.min())
P = nz(pr[y + ROW - 1:y + ROW + 2, x:x + n].mean(0))
Hh = nz(hr[y + ROW - 1:y + ROW + 2, x:x + n].mean(0))
L = nz(np.repeat(lr[(y + ROW) // 2, x // 2:x // 2 + n // 2], 2))
json.dump({"row": ROW, "px_nm": 62.6, "predicted": P.round(3).tolist(), "high_res": Hh.round(3).tolist(), "low_res": L.round(3).tolist(),
           "r_pred_hr": round(float(np.corrcoef(P, Hh)[0, 1]), 3)}, open("data/sr_profile.json", "w"))
