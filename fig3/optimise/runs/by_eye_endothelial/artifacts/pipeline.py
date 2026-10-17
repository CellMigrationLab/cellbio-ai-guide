import numpy as np, tifffile, pandas as pd
from skimage import filters, measure, morphology, segmentation, io, exposure
from scipy import ndimage as ndi
from cellpose import models
import sys, os
D=55
a=tifffile.imread('bf.tif').astype(float)
bg=filters.gaussian(a,50)
f=a-bg
loc=np.sqrt(filters.gaussian(f**2,40))
f=f/loc
# cancer-cell/debris mask: strong contrast objects
st=np.abs(f)>2.5
st=morphology.binary_closing(st,morphology.disk(2))
st=ndi.binary_fill_holes(st)
st=morphology.remove_small_objects(st,60)
# texture-flatten for endothelium: clip strong features
g=np.clip(f,-2,2)
g=filters.gaussian(g,1.5)
g8=exposure.rescale_intensity(g,out_range=(0,255)).astype(np.uint8)
m=None if os.path.exists('raw_lab.npy') else models.CellposeModel(gpu=False)
import os
if os.path.exists('raw_lab.npy') and '--rerun' not in sys.argv:
    lab=np.load('raw_lab.npy')  # cached Cellpose output (delete or --rerun to recompute)
else:
    lab=m.eval(g8,diameter=D,flow_threshold=0.4,cellprob_threshold=-1.0)[0]
    np.save('raw_lab.npy',lab)
cancer=morphology.binary_dilation(st,morphology.disk(2))
out=np.zeros_like(lab)
k=0
for r in measure.regionprops(lab):
    mk=lab==r.label
    mk=mk&~cancer
    mk=ndi.binary_opening(mk,morphology.disk(3))
    l2=measure.label(mk)
    if l2.max()==0: continue
    sizes=np.bincount(l2.ravel())[1:]
    mk=l2==(sizes.argmax()+1)
    mk=morphology.remove_small_holes(mk,200)
    if mk.sum()<600: continue
    # skip cells mostly eaten by cancer mask
    if mk.sum()<0.6*r.area: continue
    k+=1; out[mk]=k
tifffile.imwrite('labels.tif',out.astype(np.uint16))
px=0.65
rows=[dict(label=r.label,area_px=r.area,area_um2=r.area*px*px) for r in measure.regionprops(out)]
pd.DataFrame(rows).to_csv('areas.csv',index=False)
print(k,np.median([r['area_um2'] for r in rows]))
v=exposure.rescale_intensity(a,in_range=tuple(np.percentile(a,(0.5,99.5))),out_range=(0,1))
ov=segmentation.mark_boundaries(np.dstack([v]*3),out,color=(1,0,0))
ov=segmentation.mark_boundaries(ov,measure.label(st),color=(0,1,0))
io.imsave('ov.png',(ov*255).astype(np.uint8))
