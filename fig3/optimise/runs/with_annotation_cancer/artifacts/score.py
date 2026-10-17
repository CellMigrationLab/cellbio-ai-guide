import numpy as np, tifffile, sys
from scipy.optimize import linear_sum_assignment
def f1(pred, gt, thr=0.5):
    p=np.unique(pred[pred>0]); g=np.unique(gt[gt>0])
    if len(p)==0: return 0,0,0,0
    pi={v:i for i,v in enumerate(p)}; gi={v:i for i,v in enumerate(g)}
    n=np.zeros((len(p)+1,len(g)+1))
    m=(pred>0)&(gt>0)
    pp=np.searchsorted(p,pred[m]); gg=np.searchsorted(g,gt[m])
    np.add.at(n,(pp,gg),1)
    ap=np.bincount(np.searchsorted(p,pred[pred>0]),minlength=len(p)); ag=np.bincount(np.searchsorted(g,gt[gt>0]),minlength=len(g))
    n=n[:-1,:-1]; iou=n/(ap[:,None]+ag[None,:]-n)
    r,c=linear_sum_assignment(-iou); tp=int((iou[r,c]>=thr).sum())
    fp=len(p)-tp; fn=len(g)-tp
    return 2*tp/(2*tp+fp+fn),tp,fp,fn
if __name__=='__main__':
    print(f1(tifffile.imread(sys.argv[1]),tifffile.imread('annot_dev.tif')))
