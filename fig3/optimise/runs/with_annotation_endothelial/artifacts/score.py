import sys,numpy as np,tifffile
from scipy.optimize import linear_sum_assignment
from skimage.segmentation import clear_border
def prep(l):
    l=l.copy()
    for r in np.unique(np.concatenate([l[0],l[-1],l[:,0],l[:,-1]])):
        if r: l[l==r]=0
    return l
def f1(p,g,t=0.5):
    p=prep(p);g=prep(g)
    pi=np.unique(p)[1:];gi=np.unique(g)[1:]
    if not len(pi) or not len(gi): return 0,len(pi),len(gi)
    n=p.max()+1;m=g.max()+1
    c=np.bincount(p.ravel().astype(np.int64)*m+g.ravel(),minlength=n*m).reshape(n,m).astype(float)
    ap=c.sum(1);ag=c.sum(0)
    iou=c/(ap[:,None]+ag[None,:]-c+1e-9)
    iou=iou[np.ix_(pi,gi)]
    r,cc=linear_sum_assignment(-iou)
    tp=(iou[r,cc]>=t).sum()
    return 2*tp/(len(pi)+len(gi)),len(pi),len(gi)
if __name__=='__main__':
    print(f1(tifffile.imread(sys.argv[1]),tifffile.imread('annot_dev.tif')))
