# Recovered verbatim from the session transcript (2026-10-17T06:29:50.616Z).
# Last shell command that wrote heldout/dapi_heldout.tif. Paths are those of the original working folder.
B=<fig3-work>/bf3; U=<uploads>; rm -rf /tmp/fijitest; cd $B && python3 - <<'E'
import os, shutil, numpy as np, tifffile
from PIL import Image
U='<uploads>/'
dapi = tifffile.imread(U+'2453a2f8-GT_DAPI.tif')
lo, hi = np.percentile(dapi, [0.5, 99.5])
Image.fromarray((np.clip((dapi-lo)/(hi-lo),0,1)*255).astype(np.uint8)).save('dapi_preview.png')
tifffile.imwrite('dapi.tif', dapi)
src = {'nuclei': ('dapi.tif', 'dapi_preview.png'), 'cancer': ('../bf/agent/bf.tif', '../bf/codeG/bf_preview.png'), 'endo': ('../bf/agent/bf.tif', '../bf/codeG/bf_preview.png')}
names = []
for t in ['nuclei', 'cancer', 'endo']:
    for r in (1, 2, 3):
        for pre in ['py_box1', 'fj_gen', 'fj_box1'] + (['gen'] if t == 'nuclei' else []):
            names.append((f'{pre}_{t}_r{r}', t))
for n, t in names:
    os.makedirs(n, exist_ok=True)
    img, prev = src[t]
    shutil.copy(img, f'{n}/{"dapi.tif" if t=="nuclei" else "bf.tif"}')
    shutil.copy(prev, f'{n}/{"dapi_preview.png" if t=="nuclei" else "bf_preview.png"}')
print(len(names), 'folders')
# development / held-out split for nuclei + by-eye agent folder + draw/count
os.makedirs('ref_nuclei', exist_ok=True); os.makedirs('agent_nuclei', exist_ok=True); os.makedirs('dc_nuclei', exist_ok=True)
R = tifffile.imread(U+'1add3634-104_3.tif').astype(np.int32)
tifffile.imwrite('ref_nuclei/dapi_dev.tif', dapi[:, :512]); tifffile.imwrite('ref_nuclei/annot_dev.tif', R[:, :512])
tifffile.imwrite('heldout/dapi_heldout.tif', dapi[:, 512:])
shutil.copy('dapi.tif', 'agent_nuclei/dapi.tif'); shutil.copy('dapi_preview.png', 'dc_nuclei/dapi_full.png')
print('dev nuclei', len(np.unique(R[:, :512])) - 1, 'held-out', len(np.unique(R[:, 512:])) - 1)
E
chmod 444 ref_nuclei/*.tif agent_nuclei/dapi.tif; ls | head -80 | tr '\n' ' '
