"""Rasterise LLM polygons (replies/draw_<target>_r<k>.txt) to label images and score them."""
import sys, re, json, numpy as np, tifffile
from skimage.draw import polygon
sys.path.insert(0, '../../bf'); sys.path.insert(0, '..')
from score_cancer import score as sc
from score_endo import score as se
for name in sys.argv[1:]:
    t = open(f'../replies/{name}.txt').read()
    d = json.loads(re.search(r'\{"count".*\]\s*\}', t, re.S).group(0))
    L = np.zeros((1022, 1024), np.int32)
    for i, c in enumerate(d['cells'], 1):
        p = np.array(c['points'], float)
        rr, cc = polygon(p[:, 1], p[:, 0], L.shape)
        L[rr, cc] = i
    tifffile.imwrite(f'{name}_labels.tif', L)
    s = (sc if 'cancer' in name else se)(L); s['n_drawn'] = len(d['cells']); s['count_stated'] = d['count']
    json.dump(s, open(f'{name}_score.json', 'w')); print(name, s)
