"""DAPI nuclei segmentation: sqrt transform -> local threshold -> distance-transform watershed -> QC filters."""
import numpy as np, tifffile, pandas as pd
from scipy import ndimage as ndi
from skimage import measure, morphology, segmentation, filters, feature
from PIL import Image
UM = 0.65
img = tifffile.imread('dapi.tif').astype(np.float32)

g = np.sqrt(img)                       # compress the huge dynamic range (dim endothelial vs bright cancer nuclei)
s = ndi.gaussian_filter(g, 1.0)
fg = s > filters.threshold_local(s, 41, method='gaussian', offset=-0.5)   # local threshold removes cytoplasmic haze
fg = ndi.binary_opening(fg, morphology.disk(2))
fg = ndi.binary_fill_holes(fg)
fg = morphology.remove_small_objects(fg, max_size=80)
d = ndi.gaussian_filter(ndi.distance_transform_edt(fg), 1.0)
pk = feature.peak_local_max(d, min_distance=7, labels=measure.label(fg), exclude_border=False)
mk = np.zeros(img.shape, int); mk[tuple(pk.T)] = np.arange(1, len(pk) + 1)
lab = segmentation.watershed(-d, mk, mask=fg)

# QC: drop small fragments and low-contrast debris (contrast = mean inside / mean in 5-px ring outside)
sm = ndi.gaussian_filter(img, 1)
out = np.zeros(lab.shape, np.uint16); k = 0
for r in measure.regionprops(lab):
    if r.area < 100: continue
    m = lab == r.label
    ring = ndi.binary_dilation(m, iterations=5) & ~ndi.binary_dilation(m, iterations=1) & (lab == 0)
    if ring.sum() < 10: contrast = 9.
    else: contrast = sm[m].mean() / (sm[ring].mean() + 1e-6)
    if contrast < 1.35 or r.solidity < 0.8: continue
    k += 1; out[m] = k
tifffile.imwrite('labels.tif', out)

rows = []
for r in measure.regionprops(out, intensity_image=img):
    rows.append(dict(label=r.label, area_px=int(r.area), area_um2=r.area * UM**2,
                     centroid_y=r.centroid[0], centroid_x=r.centroid[1],
                     mean_intensity=r.intensity_mean, solidity=r.solidity, eccentricity=r.eccentricity,
                     touches_border=bool(r.bbox[0] == 0 or r.bbox[1] == 0 or r.bbox[2] == out.shape[0] or r.bbox[3] == out.shape[1])))
df = pd.DataFrame(rows)
# very bright nuclei = probably cancer cells on top (flag only; all are counted)
df['bright_cancer_like'] = df.mean_intensity > 2.5 * df.mean_intensity.median()
df.to_csv('areas.csv', index=False)
print(len(df), df.area_um2.describe().round(1).to_dict(), 'bright:', int(df.bright_cancer_like.sum()))

b = np.clip(img / np.percentile(img, 99.7), 0, 1) ** 0.6
rgb = np.dstack([b] * 3); rgb[segmentation.find_boundaries(out, mode='outer')] = [1, .1, .1]
Image.fromarray((rgb * 255).astype('uint8')).save('overlay.png')
