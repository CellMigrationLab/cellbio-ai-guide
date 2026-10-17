# Recovered verbatim from the session transcript (2026-10-16T16:46:22Z).
# Added a whole-field pixel correlation ("r_pixel") to data/al_intensity.json. It was shown in the figure for
# four minutes and then removed, so it is NOT used by the final Figure 2; al_intensity.py alone does not write it.
cd <work2>/fig2; python3 - <<'PY'
import json, numpy as np, tifffile
U="<uploads>/"
d=json.load(open("data/al_intensity.json"))
for key,a,p in [("DAPI","2453a2f8-GT_DAPI.tif","fb5637b9-pi2pix_DAPI.tif"),("PECAM-1","79740787-GT_PECAM.tif","8ad24279-pix2pix_PECAM.tif")]:
    A=tifffile.imread(U+a).astype(float); P=tifffile.imread(U+p)[1:1023].astype(float)
    r=float(np.corrcoef(A.ravel(),P.ravel())[0,1]); d[key]["r_pixel"]=round(r,3); print(key, r)
json.dump(d,open("data/al_intensity.json","w"))
PY
