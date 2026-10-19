import sys,numpy as np,tifffile
sys.path.insert(0,'work')
from skimage import filters, feature, segmentation, morphology, measure
import scipy.ndimage as ndi
from evalseg import evaluate
a=tifffile.imread('image.tif').astype(np.float32); gt=tifffile.imread('annotation.tif')
def run(sig_hp=2.0,sig_seed=10,md=18,comp=0.0,sig_edge=2.0,thr=4.0,w_edge=1.0):
    bg=filters.gaussian(a,30); d=a-bg
    sd=np.sqrt(filters.gaussian(d**2,60)); n=d/sd
    # cancer / debris: strong excursions
    strong=filters.gaussian(np.abs(n),1.5)>thr
    strong=morphology.remove_small_objects(strong,20)
    strong=morphology.binary_dilation(strong,morphology.disk(5))
    hp=filters.gaussian(n,sig_hp)-filters.gaussian(n,sig_hp*3)
    en=np.where(strong,0,hp**2)
    w=(~strong).astype(np.float32)
    energy=filters.gaussian(en,sig_seed)/np.maximum(filters.gaussian(w,sig_seed),0.05)
    pk=feature.peak_local_max(energy,min_distance=md,exclude_border=False)
    mk=np.zeros(a.shape,np.int32); mk[tuple(pk.T)]=np.arange(1,len(pk)+1)
    edge=filters.gaussian(np.where(strong,0,np.abs(hp)),sig_edge)
    lab=segmentation.watershed(w_edge*edge/edge.std(),mk,compactness=comp)
    return lab,mk,strong
if __name__=="__main__":
    for sig_seed in (8,12):
      for md in (15,22):
        for comp in (0,0.01,0.1):
            lab,mk,_=run(sig_seed=sig_seed,md=md,comp=comp); e=evaluate(gt,lab)
            print(sig_seed,md,comp,e['n_pred'],e['F1_iou50'],e['mean_iou_matched'],e['median_area_pred'],flush=True)
