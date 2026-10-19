import sys,numpy as np,tifffile
sys.path.insert(0,'work')
from evalseg import evaluate
y0=int(sys.argv[3]); gt=tifffile.imread('annotation.tif'); pr=tifffile.imread(sys.argv[1])
g=gt[y0:].copy(); p=pr[y0:].copy()
# keep only objects whose centroid lies in region (labels cut at the region boundary are dropped from both)
from skimage.measure import regionprops
def keep(l):
    out=np.zeros_like(l)
    for r in regionprops(l):
        if r.centroid[0]>=40 and r.bbox[0]>0: out[l==r.label]=r.label
    return out
g=keep(g); p=keep(p)
for k,v in evaluate(g,p).items(): print(k,v)
