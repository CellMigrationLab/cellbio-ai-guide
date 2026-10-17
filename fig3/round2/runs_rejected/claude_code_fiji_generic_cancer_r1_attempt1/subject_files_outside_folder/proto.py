import numpy as np, tifffile
from scipy import ndimage as ndi
from skimage import filters, morphology, measure, segmentation, io, color
im=tifffile.imread('/home/user/sessions/s002/image.tif').astype(float)
bg=ndi.gaussian_filter(im,30); f=im-bg
sd=np.sqrt(np.maximum(ndi.uniform_filter(f**2,7)-ndi.uniform_filter(f,7)**2,0))
sd=ndi.gaussian_filter(sd,1)
t=filters.threshold_otsu(sd); print('otsu',t, np.percentile(sd,[50,90,99]))
dark=f< -2.0*f.std()*0.6
for name,m in [('sd',sd>t)]:
    pass
import sys
k=float(sys.argv[1]) if len(sys.argv)>1 else 1.0
m=sd>t*k
m=morphology.binary_closing(m,morphology.disk(3))
m=ndi.binary_fill_holes(m)
m=morphology.binary_opening(m,morphology.disk(5))
m=morphology.remove_small_objects(m,200)
d=ndi.distance_transform_edt(m); d=ndi.gaussian_filter(d,2)
pk=measure.label(morphology.h_maxima(d,0.7))
lab=segmentation.watershed(-d,pk,mask=m)
out=[]
for r in measure.regionprops(lab):
    if r.area<250 or r.area>2500 or r.solidity<0.6: lab[lab==r.label]=0
lab,_,_=segmentation.relabel_sequential(lab)
print(lab.max(), np.median([r.area for r in measure.regionprops(lab)]))
ov=segmentation.mark_boundaries(np.clip((im-im.min())/(np.percentile(im,99.8)-im.min()),0,1),lab,color=(1,0,0))
io.imsave('ov.png',(ov*255).astype(np.uint8))
