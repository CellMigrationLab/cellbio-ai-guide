import numpy as np, tifffile, pandas as pd
from scipy import ndimage as ndi
from skimage import measure, segmentation, morphology, io, exposure
from cellpose import models
PX=0.65
img=tifffile.imread('bf.tif').astype(np.float32)
bg=ndi.gaussian_filter(img,60); x=img-bg
x=(x-np.percentile(x,0.5))/(np.percentile(x,99.5)-np.percentile(x,0.5))
m=models.CellposeModel(gpu=False)
import os
if os.path.exists('raw_labels.npy'): lab=np.load('raw_labels.npy')
else:
    lab,_,_=m.eval(x,diameter=26,flow_threshold=0.4,cellprob_threshold=0.0); np.save('raw_labels.npy',lab)
# cleanup: fill holes, drop border-tiny and small debris, relabel
out=np.zeros_like(lab)
k=0
for r in measure.regionprops(lab):
    mask=ndi.binary_fill_holes(lab==r.label)
    a=mask.sum()
    if a<150 or a>1500 or r.solidity<0.85 or r.eccentricity>0.85: continue  # debris / endothelial polygons / irregular
    ring=mask&~ndi.binary_erosion(mask,iterations=3)
    # cancer cells have a dark/bright refractile rim: strong local contrast vs. flat endothelium
    if ring.sum()==0 or x[mask].std()<0.12: continue
    k+=1; out[mask&(out==0)]=k
out=out.astype(np.int32)
tifffile.imwrite('labels.tif',out)
rp=measure.regionprops(out)
df=pd.DataFrame({'label':[r.label for r in rp],'area_px':[r.area for r in rp],
 'area_um2':[r.area*PX**2 for r in rp],'touches_border':[int(r.bbox[0]==0 or r.bbox[1]==0 or r.bbox[2]==out.shape[0] or r.bbox[3]==out.shape[1]) for r in rp]})
df.to_csv('areas.csv',index=False)
print(len(df),df.area_um2.describe())
v=exposure.rescale_intensity(img,in_range=tuple(np.percentile(img,[0.5,99.5])),out_range=(0,1))
io.imsave('overlay.png',(segmentation.mark_boundaries(np.dstack([v]*3),out,color=(1,0,0))*255).astype(np.uint8))
