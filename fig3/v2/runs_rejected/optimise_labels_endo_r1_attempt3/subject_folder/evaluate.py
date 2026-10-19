"""Compare predicted labels with annotation: python evaluate.py labels.tif annotation.tif"""
import sys, numpy as np, tifffile
from skimage import measure
def iou_matrix(gt, pr):
    n_g, n_p = gt.max()+1, pr.max()+1
    inter = np.bincount(gt.ravel().astype(np.int64)*n_p+pr.ravel(), minlength=n_g*n_p).reshape(n_g,n_p)
    ag, ap = inter.sum(1,keepdims=True), inter.sum(0,keepdims=True)
    return inter/(ag+ap-inter+1e-9)
def evaluate(gt, pr, verbose=True):
    iou = iou_matrix(gt, pr)[1:,1:]
    res = {"n_gt": iou.shape[0], "n_pred": iou.shape[1]}
    for t in (0.5, 0.75):
        tp = ((iou>=t)).sum(); res[f"F1@{t}"] = 2*tp/(iou.shape[0]+iou.shape[1])
    # matched-pair shape errors
    gi, pi = np.where(iou>=0.5)
    rg = {r.label:r for r in measure.regionprops(gt)}; rp={r.label:r for r in measure.regionprops(pr)}
    ga=np.array([rg[i+1].area for i in gi]); pa=np.array([rp[j+1].area for j in pi])
    gr=np.array([rg[i+1].major_axis_length/rg[i+1].minor_axis_length for i in gi])
    pr_=np.array([rp[j+1].major_axis_length/rp[j+1].minor_axis_length for j in pi])
    res["area_med_rel_err"] = float(np.median((pa-ga)/ga)); res["area_MAPE"]=float(np.mean(abs(pa-ga)/ga))
    res["aspect_MAE"] = float(np.mean(abs(pr_-gr)))
    res["count_ratio"] = iou.shape[1]/iou.shape[0]
    return res
if __name__=="__main__":
    print(evaluate(tifffile.imread(sys.argv[2]), tifffile.imread(sys.argv[1])))
