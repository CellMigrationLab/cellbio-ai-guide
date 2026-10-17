import numpy as np,tifffile
from scipy.optimize import linear_sum_assignment
def border(l):
    s=set(np.unique(np.concatenate([l[0],l[-1],l[:,0],l[:,-1]])))-{0};return s
def f1(pred,gt,thr=0.5):
    bp,bg=border(pred),border(gt)
    P=[i for i in np.unique(pred) if i and i not in bp];G=[i for i in np.unique(gt) if i and i not in bg]
    if not P or not G: return 0,0,len(P),len(G)
    gi={g:k for k,g in enumerate(G)};pi={p:k for k,p in enumerate(P)}
    M=np.zeros((len(P),len(G)))
    ap=np.bincount(pred.ravel());ag=np.bincount(gt.ravel())
    m=(pred>0)&(gt>0)
    pr,gr=pred[m],gt[m]
    pairs,c=np.unique(np.stack([pr,gr]),axis=1,return_counts=True)
    for (p,g),n in zip(pairs.T,c):
        if p in pi and g in gi: M[pi[p],gi[g]]=n/(ap[p]+ag[g]-n)
    r,cc=linear_sum_assignment(-M);tp=(M[r,cc]>=thr).sum()
    return 2*tp/(len(P)+len(G)),tp,len(P),len(G)
