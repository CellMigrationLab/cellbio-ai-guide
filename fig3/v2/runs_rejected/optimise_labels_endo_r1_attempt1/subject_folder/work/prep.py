"""Shared preprocessing for experiments (mirrors what pipeline.py will do)."""
import numpy as np, tifffile
from skimage import filters, transform
SCALE=0.6
def flatten(a):
    a=a.astype(np.float32); bg=filters.gaussian(a,40); d=a-bg
    sd=np.sqrt(filters.gaussian(d**2,40)); return (d/sd).astype(np.float32)
def down(n): return transform.rescale(n,SCALE,order=1,anti_aliasing=True).astype(np.float32)
def down_lbl(l): return transform.resize(l,(round(l.shape[0]*SCALE),round(l.shape[1]*SCALE)),order=0,preserve_range=True,anti_aliasing=False).astype(np.int32)
