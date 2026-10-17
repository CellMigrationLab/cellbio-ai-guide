import numpy as np, tifffile
from scipy import ndimage as ndi
from skimage import filters, morphology, measure, segmentation, feature, io, exposure
S='/tmp/claude-0/-home-user/8b3112e1-653c-5f4c-bdba-69ecd9f94f24/scratchpad/'
im=tifffile.imread('image.tif').astype(np.float32)
bg=ndi.gaussian_filter(im,40)
flat=im-bg
sd=np.sqrt(ndi.gaussian_filter(flat**2,40))
z=flat/sd
# local texture energy at cell scale
e=ndi.gaussian_filter(np.abs(z),3)
print(np.percentile(e,[5,50,90,95,99]))
t=filters.threshold_otsu(e); print('otsu',t)
for name,a in [('e',e)]:
    v=exposure.rescale_intensity(a,out_range=(0,255)).astype(np.uint8); io.imsave(S+'e.png',v)
