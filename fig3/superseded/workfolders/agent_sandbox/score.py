"""Score a nuclei label image against the manual reference of the development image.
Usage: python3 score.py labels.tif   -> prints object F1 (IoU >= 0.5, one-to-one matching)."""
import sys
import tifffile
from matching import match
ref = tifffile.imread("nuclei_reference_dev.tif").astype(int)
pr = tifffile.imread(sys.argv[1]).astype(int)
m, fn, fp = match(ref, pr, 0.5)
tp = len(m)
print(f"F1 = {2*tp/(2*tp+len(fn)+len(fp)):.3f}  (TP {tp}, FN {len(fn)}, FP {len(fp)})")
