"""Cancer-cell segmentation on brightfield. Usage: python pipeline.py in.tif out_labels.tif
Needs the cellpose environment (Cellpose 4 / Cellpose-SAM). Pixel size 0.65 um assumed (cell diameter ~30 px)."""
import sys, numpy as np, tifffile
from skimage.measure import regionprops, label
from cellpose import models

MIN_AREA, MAX_AREA = 280, 1300   # px; drops debris/fragments and large flat endothelial cells

def run(img):
    m = models.CellposeModel(gpu=False)
    lab, _, _ = m.eval(img.astype(np.float32), diameter=30)
    out = np.zeros(lab.shape, np.int32); k = 0
    for r in regionprops(lab):
        if MIN_AREA <= r.area <= MAX_AREA:
            k += 1; out[lab == r.label] = k
    return out

if __name__ == '__main__':
    img = tifffile.imread(sys.argv[1])
    out = run(img)
    tifffile.imwrite(sys.argv[2], out)
    areas = np.bincount(out.ravel())[1:]
    print(f'n_cells={len(areas)} mean_area_px={areas.mean():.0f} mean_area_um2={areas.mean()*0.65**2:.1f}')
