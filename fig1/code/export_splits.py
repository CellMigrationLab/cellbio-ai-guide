"""Split-view widgets for row A: left half = input, right half = AI output, same field (linear display only)."""
import numpy as np
import tifffile
from PIL import Image
from skimage.segmentation import find_boundaries
from scipy import ndimage as ndi

from common.paths import RAW as U
OUT = 360   # output pixels per widget side
COLS = ["#ff4fa3", "#ffd23f", "#3ec1ff", "#b07cff", "#2ee59d", "#ff7a3d", "#ff3d5a", "#44e0d6", "#a8f03e", "#5a8bff"]


def lin(a, ref=None, p=(0.3, 99.7)):
    lo, hi = np.percentile(a if ref is None else ref, p)
    return np.clip((a - lo) / (hi - lo), 0, 1)


def resize(a, n=OUT, nearest=True):
    k = n / a.shape[0]
    idx = np.minimum((np.arange(n) / k).astype(int), a.shape[0] - 1)
    return a[idx][:, idx]


def overlay(gray, lab, lift=True):
    o = np.stack([(0.15 + 0.8 * gray) if lift else gray] * 3, -1)
    edge = ndi.binary_dilation(find_boundaries(lab, mode="inner"), iterations=1)
    for i, l in enumerate(np.unique(lab[lab > 0])):
        c = np.array([int(COLS[i % len(COLS)][k:k + 2], 16) / 255 for k in (1, 3, 5)])
        m = lab == l
        o[m] = 0.55 * o[m] + 0.45 * c
        o[m & edge] = c
    return o


def split(left, right, name):
    h = OUT // 2
    out = np.concatenate([left[:, :h], right[:, h:]], 1)
    Image.fromarray(np.round(np.clip(out, 0, 1) * 255).astype(np.uint8)).save(f"data5/{name}.png", optimize=True)


rgb = lambda g: np.stack([g] * 3, -1)

# 1 nuclei (HPMEC, Cellpose): region of the 600x800 crop, 360 x 360 px, split through the touching pair
hp = tifffile.imread(U + "hpmec_nuclei_max_projection.tif")[1248:2048, 0:600].astype(float)
hl = tifffile.imread("data/panelA_cellpose_labels.tif").astype(int)
y, x, n = 280, 20, 480
g = lin(hp[y:y + n, x:x + n], hp)
split(rgb(resize(g)), overlay(resize(g), resize(hl[y:y + n, x:x + n]), lift=False), "split_nuclei")

# 2 cancer cells (brightfield, StarDist): 210 x 210 px of the full BF
bf = tifffile.imread(U + "field104_brightfield.tif").astype(float)
sd = tifffile.imread(U + "field104_cancer_cells_stardist_custom_labels.tif").astype(int)
y, x, n = 60, 200, 210
g = lin(bf[y:y + n, x:x + n])
split(rgb(resize(g)), overlay(resize(g), resize(sd[y:y + n, x:x + n])), "split_cells")

# 3 super-resolution: LR (nearest-upsampled 2x) vs prediction, 180 LR px = 360 HR px
lr = tifffile.imread(U + "biosr_er_lowres_input.tif").astype(float)
pr = tifffile.imread(U + "biosr_er_rcan_prediction.tif").astype(float)
hr = tifffile.imread(U + "biosr_er_highres_reference.tif").astype(float)
y, x = 150, 160                 # HR coordinates (LR = /2)
a = lin(lr[y // 2:y // 2 + 180, x // 2:x // 2 + 180])
b = lin(pr[y:y + 360, x:x + 360])
split(rgb(resize(a)), rgb(b), "split_sr")
c = lin(hr[y:y + 360, x:x + 360])
Image.fromarray(np.round(np.stack([c] * 3, -1) * 255).astype(np.uint8)).save("data5/sr_hr_region.png")

# 4 artificial labelling: BF vs pix2pix DAPI (magenta) + PECAM (green), another area of the field
pd = tifffile.imread(U + "field104_pix2pix_predicted_dapi.tif")[1:1023].astype(float)
pp = tifffile.imread(U + "field104_pix2pix_predicted_pecam1.tif")[1:1023].astype(float)
y, x, n = 560, 620, 210
g = lin(bf[y:y + n, x:x + n])
d, p_ = lin(pd[y:y + n, x:x + n]), lin(pp[y:y + n, x:x + n])
split(rgb(resize(g)), resize(np.stack([d, p_, d], -1)), "split_label")

# LLM card result: QC overlay of the Cellpose nuclei (outlines on the raw image), same region as widget 1
y, x, n = 280, 20, 480
g = resize(lin(hp[y:y + n, x:x + n], hp))
lab = resize(hl[y:y + n, x:x + n])
o = rgb(g)
o[ndi.binary_dilation(find_boundaries(lab, mode="inner"), iterations=1)] = [1, 0.24, 0.82]
Image.fromarray(np.round(o * 255).astype(np.uint8)).save("data5/llm_qc.png")
print("ok")

# --- super-resolution, zoomed in so the low-res pixels are visible (140 HR px = 8.8 um; 70 LR px)
y, x = 160, 600
a = lin(lr[y // 2:y // 2 + 70, x // 2:x // 2 + 70])
b = lin(pr[y:y + 140, x:x + 140])
split(rgb(resize(a)), rgb(resize(b)), "split_sr_zoom")

# --- denoising: raw (noisy) vs network output, nuclei, 200 x 200 px (0.6337 um/px)
raw = tifffile.imread(U + "care_denoising_acquired.tif").astype(float)
den = tifffile.imread(U + "care_denoising_restored.tif").astype(float)
y, x, n = 640, 520, 200
split(rgb(resize(lin(raw[y:y + n, x:x + n]))), rgb(resize(lin(den[y:y + n, x:x + n]))), "split_denoise")

# --- tracking: TrackMate capture (brightfield + spots + tracks, RGB), 300 x 300 px crop
cap = tifffile.imread(U + "trackmate_capture_tracks.tif").astype(float) / 255
y, x, n = 380, 260, 300
Image.fromarray(np.round(resize(cap[y:y + n, x:x + n]) * 255).astype(np.uint8)).save("data5/tracking.png")
print("extra widgets ok")
