import numpy as np, tifffile, sys
from scipy import ndimage as ndi
from skimage import filters, morphology, segmentation, measure, feature
def run(img, sig=3, thr_mode='otsu', min_area=150, dist_sm=2, md=9):
    x=img.astype(float)
    x=(x-np.median(x))/ (np.percentile(x,99)-np.percentile(x,1))
    # local texture / contrast
    m=ndi.uniform_filter(x,5); s=np.sqrt(np.maximum(ndi.uniform_filter(x*x,5)-m*m,0))
    s=ndi.gaussian_filter(s,sig)
    t=filters.threshold_otsu(s) if thr_mode=='otsu' else thr_mode
    mask=s>t
    mask=ndi.binary_fill_holes(morphology.binary_opening(mask,morphology.disk(3)))
    mask=morphology.remove_small_objects(mask,min_area)
    d=ndi.gaussian_filter(ndi.distance_transform_edt(mask),dist_sm)
    pk=feature.peak_local_max(d,min_distance=md,labels=measure.label(mask),exclude_border=False)
    mk=np.zeros(mask.shape,int); mk[tuple(pk.T)]=np.arange(1,len(pk)+1)
    lab=segmentation.watershed(-d,mk,mask=mask)
    return lab
if __name__=='__main__':
    lab=run(tifffile.imread(sys.argv[1])); tifffile.imwrite(sys.argv[2],lab.astype(np.int32))
