"""Compare predicted labels with annotation: detection F1 (IoU>=0.5), count, area and aspect ratio agreement."""
import sys, numpy as np, tifffile
from skimage.measure import regionprops
PX=0.65
def match(gt,pr):
    gi,pi=np.unique(gt[gt>0]),np.unique(pr[pr>0])
    pairs=np.stack([gt.ravel(),pr.ravel()],1); pairs=pairs[(pairs>0).all(1)]
    u,c=np.unique(pairs,axis=0,return_counts=True)
    ga={i:(gt==i).sum() for i in gi} if False else dict(zip(*np.unique(gt,return_counts=True)))
    pa=dict(zip(*np.unique(pr,return_counts=True)))
    m={}
    for (g,p),n in zip(u,c):
        iou=n/(ga[g]+pa[p]-n)
        if iou>=0.5: m[g]=(p,iou)
    return m,len(gi),len(pi)
def stats(l):
    return {r.label:(r.area*PX**2, r.axis_major_length/max(r.axis_minor_length,1e-9)) for r in regionprops(l)}
def evaluate(gt,pr):
    m,ng,npred=match(gt,pr); tp=len(m)
    if tp==0: return dict(n_gt=ng,n_pred=npred,tp=0,F1_iou50=0.0,mean_iou_matched=0.0,median_area_pred=float('nan'))
    f1=2*tp/(ng+npred); sg,sp=stats(gt),stats(pr)
    a=np.array([[sg[g][0],sp[p][0]] for g,(p,_) in m.items()]); r=np.array([[sg[g][1],sp[p][1]] for g,(p,_) in m.items()])
    allg=np.array(list(sg.values())); allp=np.array(list(sp.values()))
    return dict(n_gt=ng,n_pred=npred,tp=tp,F1_iou50=round(f1,3),precision=round(tp/npred,3),recall=round(tp/ng,3),
      count_ratio=round(npred/ng,3),mean_iou_matched=round(np.mean([v[1] for v in m.values()]),3),
      median_area_gt=round(np.median(allg[:,0]),0),median_area_pred=round(np.median(allp[:,0]),0),
      median_AR_gt=round(np.median(allg[:,1]),2),median_AR_pred=round(np.median(allp[:,1]),2),
      matched_area_rel_err_median=round(np.median(np.abs(a[:,1]-a[:,0])/a[:,0]),3),
      matched_AR_abs_err_median=round(np.median(np.abs(r[:,1]-r[:,0])),3),
      matched_area_corr=round(np.corrcoef(a.T)[0,1],3),matched_AR_corr=round(np.corrcoef(r.T)[0,1],3))
if __name__=="__main__":
    for k,v in evaluate(tifffile.imread(sys.argv[1]),tifffile.imread(sys.argv[2])).items(): print(k,v)
