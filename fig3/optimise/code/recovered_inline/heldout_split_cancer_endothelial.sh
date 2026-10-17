# Recovered verbatim from the session transcript (2026-10-17T05:56:38.298Z).
# Development (x < 512) / held-out (x >= 512) split for cancer and endothelial cells. Paths are those of the original working folder.
cd <work>/fig3 && mkdir -p bf3 && cd bf3 && for t in cancer endo; do for r in 1 2 3; do mkdir -p box1_${t}_r$r; cp ../bf/agent/bf.tif box1_${t}_r$r/; cp ../bf/codeG/bf_preview.png box1_${t}_r$r/; done; for r in 2 3; do mkdir -p gen_${t}_r$r; cp ../bf/agent/bf.tif ../bf/codeG/bf_preview.png gen_${t}_r$r/; done; done && python3 - <<'E'
# development / held-out split for the agent-with-reference experiment: left half (x < 512) dev, right half held out
import sys, numpy as np, tifffile, os
sys.path.insert(0, '../bf')
from score_endo import gt
from skimage.segmentation import clear_border
from skimage.measure import label
bf = tifffile.imread('../bf/agent/bf.tif')
GC = tifffile.imread('<uploads>/e752a357-104_2.tif')
GE = gt()
os.makedirs('ref_cancer', exist_ok=True); os.makedirs('ref_endo', exist_ok=True); os.makedirs('heldout', exist_ok=True)
for t, G in [('cancer', GC), ('endo', GE)]:
    tifffile.imwrite(f'ref_{t}/bf_dev.tif', bf[:, :512])
    d = G[:, :512].astype(np.int32)
    if t == 'endo': d = clear_border(d)
    tifffile.imwrite(f'ref_{t}/annot_dev.tif', d)
    h = G[:, 512:].astype(np.int32)
    if t == 'endo': h = clear_border(h)
    tifffile.imwrite(f'heldout/gt_{t}_heldout.tif', h)
    tifffile.imwrite(f'heldout/gt_{t}_dev.tif', d)
    print(t, 'dev objects', len(np.unique(d)) - 1, 'held-out objects', len(np.unique(h)) - 1)
tifffile.imwrite('heldout/bf_heldout.tif', bf[:, 512:])
E
chmod 444 ref_*/annot_dev.tif ref_*/bf_dev.tif; ls
