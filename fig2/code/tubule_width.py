"""ER tubule width (FWHM) at the same locations in the low-res input (bilinear-upsampled to the 2x grid), the prediction and
the higher-resolution reference. Locations: skeleton points of BOTH the thresholded reference and the thresholded prediction
(so neither image defines where tubules are), sampled on a regular grid, away from branch points and image borders; profile
perpendicular to the local tubule direction (structure tensor of the reference), 3-px wide. Noise floor: the reference
measured at the same point and 2 px (62.6 nm) further along the tubule."""
import json
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import filters, morphology, feature

from common.paths import RAW as U
PX = 31.3          # nm per pixel on the 2x grid (BioSR: raw/low-res 62.6 nm, 2x grid 31.3 nm)
lr = tifffile.imread(U + "biosr_er_lowres_input.tif").astype(float)
pr = tifffile.imread(U + "biosr_er_rcan_prediction.tif").astype(float)
hr = tifffile.imread(U + "biosr_er_highres_reference.tif").astype(float)
lr2 = ndi.zoom(lr, 2, order=1)[:hr.shape[0], :hr.shape[1]]

def line_points(im):
    gi = filters.gaussian(im, 1)
    sk_ = morphology.skeletonize(gi > filters.threshold_otsu(gi))
    nb = ndi.convolve(sk_.astype(int), np.ones((3, 3)), mode="constant") - 1
    return sk_ & (nb == 2)                           # simple line points only (no ends, no branches)


g = filters.gaussian(hr, 1)
sk = line_points(hr) | line_points(pr)
Arr, Arc, Acc = feature.structure_tensor(g, sigma=3, order="rc")
ys, xs = np.nonzero(sk)
keep = (ys > 20) & (ys < hr.shape[0] - 20) & (xs > 20) & (xs < hr.shape[1] - 20) & (ys % 12 == 0)
ys, xs = ys[keep], xs[keep]


def fwhm(p):
    p = p - p.min()
    if p.max() <= 0:
        return np.nan
    c = len(p) // 2
    pk = c - 3 + int(np.argmax(p[c - 3:c + 4]))
    half = p[pk] / 2
    l = pk
    while l > 0 and p[l] > half:
        l -= 1
    r = pk
    while r < len(p) - 1 and p[r] > half:
        r += 1
    if l == 0 or r == len(p) - 1:
        return np.nan
    lx = l + (half - p[l]) / (p[l + 1] - p[l])            # linear interpolation at half maximum
    rx = r - 1 + (p[r - 1] - half) / (p[r - 1] - p[r])
    return rx - lx


out = {k: [] for k in ("low_res", "predicted", "reference", "reference_2px")}
t_ = np.arange(-12, 12.5, 0.5)
for y, x in zip(ys, xs):
    a, b, c = Arr[y, x], Arc[y, x], Acc[y, x]
    w, v = np.linalg.eigh(np.array([[a, b], [b, c]]))
    ny, nx = v[:, 1]                                   # largest-eigenvalue direction = across the tubule
    ay, ax = v[:, 0]                                   # along the tubule
    vals = {}
    for k, im, dy, dx in (("low_res", lr2, 0, 0), ("predicted", pr, 0, 0), ("reference", hr, 0, 0), ("reference_2px", hr, 2 * ay, 2 * ax)):
        prof = np.mean([ndi.map_coordinates(im, [y + dy + t_ * ny + o * nx, x + dx + t_ * nx - o * ny], order=1) for o in (-1, 0, 1)], 0)
        vals[k] = fwhm(prof) * 0.5 * PX
    if all(np.isfinite(v_) for v_ in vals.values()):
        for k in out:
            out[k].append(round(float(vals[k]), 1))
res = {k: {"median_nm": round(float(np.median(v)), 1), "q25": round(float(np.percentile(v, 25)), 1),
           "q75": round(float(np.percentile(v, 75)), 1)} for k, v in out.items()}
res["n_locations"] = len(out["reference"])
d = np.array(out["predicted"]) - np.array(out["reference"])
dn = np.array(out["reference_2px"]) - np.array(out["reference"])
res["pred_minus_ref"] = {"median_nm": round(float(np.median(d)), 1), "q25": round(float(np.percentile(d, 25)), 1),
                         "q75": round(float(np.percentile(d, 75)), 1), "median_abs_nm": round(float(np.median(np.abs(d))), 1)}
res["noise_floor_ref_vs_ref_2px"] = {"median_nm": round(float(np.median(dn)), 1), "median_abs_nm": round(float(np.median(np.abs(dn))), 1)}
res["px_nm_assumed"] = PX
json.dump({"summary": res, "values": out}, open("panels/tubule_width.json", "w"))
print(res)
