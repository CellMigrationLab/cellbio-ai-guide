import sys,numpy as np,tifffile as t
from skimage.measure import regionprops
from skimage.segmentation import relabel_sequential
from cellpose import models
def run(inp,out):
    a=t.imread(inp).astype(np.float32)
    m=models.CellposeModel(gpu=False)
    lab,_,_=m.eval(a,diameter=30); print("raw cp labels:",lab.max(),lab.dtype,a.dtype,a.shape)          # v1: Cellpose-SAM, diameter 30 px (~20 um)
    H,W=lab.shape; t.imwrite("w/rawlab.tif",lab); print(lab.shape,len(regionprops(lab)))
    keep=np.zeros_like(lab)
    for r in regionprops(lab):             # v2: morphology/texture filter
        msk=lab==r.label
        border=r.bbox[0]==0 or r.bbox[1]==0 or r.bbox[2]>=H or r.bbox[3]>=W
        print(r.label,r.area,border,a[msk].std()) if r.label<4 else None
        if r.area<(100 if border else 300): continue   # debris / fragments
        if r.area>1400: continue                        # merged flat endothelium
        if a[msk].std()<95: continue                    # flat texture = endothelium, not a cell
        keep[msk]=r.label
    keep=relabel_sequential(keep)[0].astype(np.int32)
    t.imwrite(out,keep)
    ar=np.bincount(keep.ravel())[1:]*0.65**2
    print('cells:',keep.max(),'mean area um2: %.1f'%(ar.mean() if len(ar) else 0))
if __name__=='__main__': run(sys.argv[1],sys.argv[2])
