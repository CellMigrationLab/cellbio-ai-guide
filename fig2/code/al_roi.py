"""Panel d ROI: predicted and acquired DAPI + PECAM-1 composites for one region, with vector outlines.
Predicted image: model outlines (Cellpose on predicted PECAM-1 = cells; StarDist on predicted DAPI = nuclei).
Acquired image: manual outlines (annotators 1 and 2 = cells, drawn on acquired PECAM-1; manual nuclei).
Pix2pix-derived files carry one padded row at the top (rows 1-1022 used)."""
import sys, json
import numpy as np
import tifffile
from PIL import Image
from export_window import export

from common.annotations import lines_to_cells
from common.paths import RAW as U
X, Y, W, H = [int(v) for v in sys.argv[1:5]] if len(sys.argv) > 4 else (220, 110, 200, 200)




def comp(d, p):
    def lin(a):
        lo, hi = np.percentile(a, [0.3, 99.7])
        return np.clip((a - lo) / (hi - lo), 0, 1)
    d, p = lin(d[Y:Y + H, X:X + W]), lin(p[Y:Y + H, X:X + W])
    return np.round(np.repeat(np.repeat(np.stack([d, p, d], -1), 2, 0), 2, 1) * 255).astype(np.uint8)


acq_d = tifffile.imread(U + "field104_dapi.tif").astype(float)
acq_p = tifffile.imread(U + "field104_pecam1.tif").astype(float)
prd_d = tifffile.imread(U + "field104_pix2pix_predicted_dapi.tif")[1:1023].astype(float)
prd_p = tifffile.imread(U + "field104_pix2pix_predicted_pecam1.tif")[1:1023].astype(float)
Image.fromarray(comp(prd_d, prd_p)).save("panels/roi_pred.png")
Image.fromarray(comp(acq_d, acq_p)).save("panels/roi_acq.png")
layers = {"model_cells": tifffile.imread(U + "field104_pix2pix_pecam1_cellpose_cell_labels.tif")[1:1023],
          "model_nuclei": tifffile.imread(U + "field104_pix2pix_dapi_stardist_nuclei_labels.tif")[1:1023],
          "annot1_cells": lines_to_cells(tifffile.imread(U + "field104_endothelial_junctions_annotator1.tif") > 0),
          "annot2_cells": lines_to_cells(tifffile.imread(U + "field104_endothelial_junctions_annotator2.tif") > 0),
          "manual_nuclei": tifffile.imread(U + "field104_endothelial_nuclei_manual_labels.tif")}
for k, L in layers.items():
    export(L.astype(int), X, Y, W, H, f"panels/roi_{k}.json")
json.dump({"x": X, "y": Y, "w": W, "h": H}, open("panels/roi.json", "w"))
print("roi", X, Y, W, H)
