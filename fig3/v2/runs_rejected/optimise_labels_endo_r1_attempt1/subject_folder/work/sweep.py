import sys,numpy as np,tifffile
sys.path.insert(0,'work')
from cellpose import dynamics
from prep import *
from evalseg import evaluate
from skimage.measure import regionprops
gt=tifffile.imread('annotation.tif'); f=np.load('work/fa_flows.npz')
def keep(l):
    out=np.zeros_like(l)
    for r in regionprops(l):
        if r.bbox[0]>0: out[l==r.label]=r.label
    return out
g=keep(gt[540:])
for cp,ft in [(0,0.4),(-1,0.4),(-2,0.4),(0,1.0),(-1,1.0),(-2,1.5),(1,0.4)]:
    m=dynamics.compute_masks(f['dP'],f['cp'],niter=200,cellprob_threshold=cp,flow_threshold=ft,min_size=30)
    m=transform.resize(m,gt.shape,order=0,preserve_range=True,anti_aliasing=False).astype(np.int32)
    e=evaluate(g,keep(m[540:])); print(cp,ft,e['n_pred'],e['F1_iou50'],e['median_area_pred'],e['median_AR_pred'],flush=True)
