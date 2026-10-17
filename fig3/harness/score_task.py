"""score_task.py <dir> <nuclei|cancer|endo> : score <dir>/labels.tif and write <dir>/score.json"""
import sys, json, os, numpy as np, tifffile
sys.path.insert(0, '../bf'); sys.path.insert(0, '../v3')
d, task = sys.argv[1], sys.argv[2]
p = f'{d}/labels.tif'
if not os.path.exists(p):
    s = {'f1': 0.0, 'error': 'no labels.tif written'}
else:
    L = np.squeeze(tifffile.imread(p))
    if task == 'cancer':
        from score_cancer import score
    elif task == 'endo':
        from score_endo import score
    else:
        from score_nuclei import score
    try:
        s = score(L)
    except Exception as e:
        s = {'f1': 0.0, 'error': repr(e)}
json.dump(s, open(f'{d}/score.json', 'w')); print(d, s)
