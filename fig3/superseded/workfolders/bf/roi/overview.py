import numpy as np, tifffile
from skimage import segmentation, exposure
from PIL import Image, ImageDraw
D='<work2>/'
bf=tifffile.imread('agent/bf.tif').astype(float)
gt=tifffile.imread('<uploads>/e752a357-104_2.tif')
cp=tifffile.imread(D+'fig1/data4/BF_cellpose_sam_labels.tif')
g=tifffile.imread('codeG/labels.tif')
v=exposure.rescale_intensity(bf,in_range=tuple(np.percentile(bf,[0.5,99.5])),out_range=(0,1))
rgb=np.dstack([v]*3)
rgb[segmentation.find_boundaries(gt)]=(0,0.8,1)
rgb[segmentation.find_boundaries(cp)]=(1,0.2,0.8)
im=Image.fromarray((rgb*255).astype(np.uint8)); d=ImageDraw.Draw(im)
for k in range(0,1024,100):
    d.line([(k,0),(k,1023)],fill=(255,255,0)); d.line([(0,k),(1023,k)],fill=(255,255,0)); d.text((k+2,2),str(k),fill=(255,255,0)); d.text((2,k+2),str(k),fill=(255,255,0))
im.save('roi/overview.png')
