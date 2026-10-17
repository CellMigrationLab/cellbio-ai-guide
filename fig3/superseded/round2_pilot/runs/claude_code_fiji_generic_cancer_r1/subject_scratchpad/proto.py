import tifffile,numpy as np
from scipy import ndimage as ndi
from skimage import measure,morphology,segmentation,io,color
a=tifffile.imread('/home/user/sessions/s002/image.tif').astype(np.float32)
bg=ndi.gaussian_filter(a,50); f=a-bg
g=ndi.gaussian_filter(f,1)
m=ndi.uniform_filter(g,7); v=ndi.uniform_filter(g*g,7)-m*m
sd=np.sqrt(np.maximum(v,0))
print(np.percentile(sd,[50,90,95,99]))
from skimage.filters import threshold_otsu
t=threshold_otsu(sd);print('otsu',t)
for T in [t, 1.5*np.median(sd)+0]:
    pass
mask=sd>t
mask=morphology.binary_closing(mask,morphology.disk(2))
mask=ndi.binary_fill_holes(mask)
mask=morphology.binary_opening(mask,morphology.disk(4))
dist=ndi.distance_transform_edt(mask)
dist=ndi.gaussian_filter(dist,1.5)
pk=morphology.h_maxima(dist,1.0)
mk=measure.label(pk)
lab=segmentation.watershed(-dist,mk,mask=mask)
out=np.zeros_like(lab)
n=0
for r in measure.regionprops(lab):
    if r.area<250: continue
    n+=1; out[lab==r.label]=n
print(n,[int(r.area) for r in measure.regionprops(out)][:40])
tifffile.imwrite('proto_lab.tif',out.astype(np.uint16))
im=(a-a.min())/(a.max()-a.min())
b=segmentation.find_boundaries(out)
rgb=np.dstack([im]*3);rgb[b]=[1,0,0]
io.imsave('ov.png',(rgb*255).astype(np.uint8))
