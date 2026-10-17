"""Nuclei segmentation: Cellpose-SAM (diameter 23 px) + removal of small fragments.
Usage: python pipeline.py <input.tif> <output_labels.tif>   (run with the cellpose interpreter)"""
import sys, numpy as np, tifffile
from skimage.measure import regionprops, label
DIAMETER=23; FLOW_T=0.4; CELLPROB_T=0.0; MIN_AREA=150
def segment(img):
    from cellpose import models
    m=models.CellposeModel(gpu=False)
    lab,_,_=m.eval(img.astype(np.float32),diameter=DIAMETER,flow_threshold=FLOW_T,cellprob_threshold=CELLPROB_T)
    out=np.zeros(lab.shape,np.int32); k=0
    for r in regionprops(lab):
        if r.area>=MIN_AREA:
            k+=1; out[lab==r.label]=k
    return out
if __name__=="__main__":
    lab=segment(tifffile.imread(sys.argv[1]))
    tifffile.imwrite(sys.argv[2],lab)
    areas=[r.area*0.65**2 for r in regionprops(lab)]
    print("nuclei: %d, mean area %.1f um2, median %.1f um2"%(len(areas),np.mean(areas),np.median(areas)))
