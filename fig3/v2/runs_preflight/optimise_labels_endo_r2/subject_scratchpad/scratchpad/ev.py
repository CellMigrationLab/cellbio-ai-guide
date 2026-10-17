import numpy as np, tifffile as t
from skimage.measure import regionprops
from skimage.morphology import convex_hull_image, binary_closing, disk
def f1(gt,pr,thr=0.5):
    # restrict to annotated region
    roi=convex_hull_image(gt>0)
    gl=np.unique(gt[gt>0]); 
    pr=pr*roi
    pl=[p for p in np.unique(pr[pr>0])]
    # IoU matrix via contingency
    g=gt[roi];p=pr[roi]
    gi=np.searchsorted(gl,g); 
    import scipy.sparse as sp
    pm={v:i for i,v in enumerate(pl)}
    mask=(g>0)&(p>0)
    inter=sp.coo_matrix((np.ones(mask.sum()),(gi[mask],np.array([pm[v] for v in p[mask]]))),shape=(len(gl),len(pl))).tocsr()
    ga=np.bincount(gi[g>0],minlength=len(gl)); pa=np.array([ (p==v).sum() for v in pl]) if pl else np.array([])
    tp=0
    for i in range(len(gl)):
        row=inter.getrow(i)
        for j,v in zip(row.indices,row.data):
            if v/(ga[i]+pa[j]-v)>thr: tp+=1
    fp=len(pl)-tp; fn=len(gl)-tp
    return dict(f1=2*tp/(2*tp+fp+fn),tp=tp,fp=fp,fn=fn,ngt=len(gl),npred=len(pl))
def stats(l,roi=None):
    r=regionprops(l); a=np.array([x.area for x in r])*0.65**2
    ar=np.array([x.axis_major_length/max(x.axis_minor_length,1e-6) for x in r])
    return np.median(a),np.median(ar)
