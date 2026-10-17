import sys,tifffile as t,numpy as np,skimage.io as io
from skimage.segmentation import find_boundaries
from skimage.measure import regionprops
S=sys.argv[3] if len(sys.argv)>3 else None
a=t.imread('image.tif').astype(float); lab=np.load(sys.argv[1])
b=np.clip(a/np.percentile(a,99.5),0,1)**0.6
rgb=np.dstack([b]*3)
rgb[find_boundaries(lab,mode='inner')]=[1,0,0]
io.imsave(sys.argv[2],(rgb*255).astype('uint8'))
