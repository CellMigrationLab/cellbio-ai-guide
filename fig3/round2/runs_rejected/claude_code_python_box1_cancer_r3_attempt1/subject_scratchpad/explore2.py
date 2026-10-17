import numpy as np, tifffile
from scipy import ndimage as ndi
from skimage import filters, morphology, measure, segmentation, feature, io, color
S='/tmp/claude-0/-home-user/8b3112e1-653c-5f4c-bdba-69ecd9f94f24/scratchpad/'
im=tifffile.imread('image.tif').astype(np.float32)
px=0.65
flat=im-ndi.gaussian_filter(im,40)
z=flat/np.sqrt(ndi.gaussian_filter(flat**2,40))
e=ndi.gaussian_filter(np.abs(z),2)
m=e>0.9
m=ndi.binary_fill_holes(m)
m=morphology.opening(m,morphology.disk(5))
m=morphology.remove_small_objects(m,int(np.pi*(5/px)**2))
d=ndi.gaussian_filter(ndi.distance_transform_edt(m),1.5)
pk=feature.peak_local_max(d,min_distance=int(7/px),labels=measure.label(m),exclude_border=False)
mk=np.zeros(m.shape,int); mk[tuple(pk.T)]=np.arange(1,len(pk)+1)
lab=segmentation.watershed(-d,mk,mask=m)
print(lab.max())
for r in measure.regionprops(lab):
    pass
areas=np.array([r.area*px**2 for r in measure.regionprops(lab)]); print(np.percentile(areas,[5,25,50,75,95]))
disp=np.clip((im-np.percentile(im,1))/(np.percentile(im,99.5)-np.percentile(im,1)),0,1)
b=segmentation.find_boundaries(lab,mode='outer')
rgb=np.dstack([disp]*3); rgb[b]=[1,0.2,0.2]
io.imsave(S+'ov.png',(rgb*255).astype(np.uint8))
