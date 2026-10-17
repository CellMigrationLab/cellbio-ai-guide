"""Collect every score for the three-task Figure 3 into fig_scores.json (missing runs -> null).
Tasks: nuclei (DAPI, easy), cancer (brightfield, medium), endo (brightfield, hard). F1 at IoU >= 0.5, whole field,
except row c, which is scored on the held-out right half (x >= 512) for both conditions so they are comparable."""
import json, os, sys, numpy as np, tifffile
sys.path.insert(0, '../bf'); sys.path.insert(0, '../v3')
sys.path.insert(0, '<work2>/fig2')
from matching import match
from skimage.segmentation import clear_border
U = '<uploads>/'
TASKS = ['nuclei', 'cancer', 'endo']


def f1_of(p):
    """F1, or -1 for a run whose script crashed / wrote no labels (plotted as x, counted as F1 0)."""
    try:
        d = json.load(open(p))
    except Exception:
        return None
    return -1 if d.get('error') else d.get('f1')


def runs(paths):
    return [f1_of(p) for p in paths]


def n_of(p):
    try:
        d = json.load(open(p))
    except Exception:
        return None
    return None if d.get('error') else d.get('n_pred')


def counts(paths):
    return [n_of(p) for p in paths]


# ---------------- held-out half scoring (row c)
from score_endo import gt as endo_gt
GT = {'cancer': tifffile.imread(U + 'e752a357-104_2.tif').astype(int), 'endo': endo_gt(),
      'nuclei': tifffile.imread(U + '1add3634-104_3.tif').astype(int)}
CANC = tifffile.imread(U + 'e752a357-104_2.tif') > 0


def f1_half(task, L):
    """F1 on the held-out half (x >= 512); conventions as the whole-field scorers."""
    g = GT[task][:, 512:].copy(); p = L[:, 512:].astype(int).copy() if L.shape[1] == 1024 else L.astype(int).copy()
    if task == 'endo':
        g = clear_border(g); p = clear_border(p)
    if task == 'nuclei':
        c = CANC[:, 512:]
        ids, cnt = np.unique(p[p > 0], return_counts=True)
        on = dict(zip(*np.unique(p[(p > 0) & c], return_counts=True)))
        p[np.isin(p, [i for i, n in zip(ids, cnt) if on.get(i, 0) > 0.3 * n])] = 0
    m, fn, fp = match(g, p, 0.5)
    HALF_N[task] = int(len(np.unique(g)) - 1)
    LAST_N[0] = int(len(np.unique(p)) - 1)
    return round(2 * len(m) / max(2 * len(m) + len(fn) + len(fp), 1), 3)


HALF_N, LAST_N = {}, [None]


def half_from(path, task):
    if not os.path.exists(path): return None
    return f1_half(task, np.squeeze(tifffile.imread(path)))


S = {'tasks': {}}
B2 = '../bf2/'
for t in TASKS:
    r = {}
    gen_py = {'nuclei': [f'gen_nuclei_r{k}/score.json' for k in (1, 2, 3)],
              'cancer': [B2 + 'codeG_cancer/score.json', 'gen_cancer_r2/score.json', 'gen_cancer_r3/score.json'],
              'endo': [B2 + 'codeG_endo/score.json', 'gen_endo_r2/score.json', 'gen_endo_r3/score.json']}[t]
    b1py = [f'py_box1_{t}_r{k}/score.json' for k in (1, 2, 3)]
    fg = [f'fj_gen_{t}_r{k}/score.json' for k in (1, 2, 3)]; fb = [f'fj_box1_{t}_r{k}/score.json' for k in (1, 2, 3)]
    r['py'] = {'before': runs(gen_py), 'after': runs(b1py), 'before_n': counts(gen_py), 'after_n': counts(b1py)}
    r['fj'] = {'before': runs(fg), 'after': runs(fb), 'before_n': counts(fg), 'after_n': counts(fb)}
    eye = {'nuclei': 'agent_nuclei/labels.tif', 'cancer': B2 + 'agent_cancer/labels.tif', 'endo': B2 + 'agent_endo/labels.tif'}[t]
    LAST_N[0] = None; b = half_from(eye, t); bn = LAST_N[0]
    LAST_N[0] = None; a = half_from(f'heldout/ref_{t}_labels.tif', t); an = LAST_N[0]
    r['agent'] = {'before': [b], 'after': [a], 'before_n': [bn], 'after_n': [an], 'dev_reported': None}
    if os.path.exists(f'ref_{t}/reported.json'):
        r['agent']['dev_reported'] = json.load(open(f'ref_{t}/reported.json')).get('f1')
    if t == 'nuclei':
        dn = json.load(open('draw/nuclei_scores.json')) if os.path.exists('draw/nuclei_scores.json') else {}
        r['draw'] = {'f1': [dn.get(f'draw_nuclei_r{k}', {}).get('f1') for k in (1, 2, 3)],
                     'drawn': [dn.get(f'draw_nuclei_r{k}', {}).get('n_drawn') for k in (1, 2, 3)],
                     'asked': dn.get('counts_asked_nuclei'), 'manual': [441, 565]}
    else:
        A = json.load(open(B2 + 'all_scores.json'))
        r['draw'] = {'f1': [A[f'draw_{t}_r{k}']['f1'] for k in (1, 2, 3)],
                     'drawn': [A[f'draw_{t}_r{k}']['n_drawn'] for k in (1, 2, 3)],
                     'asked': A['counts_asked'][t], 'manual': [124, 124] if t == 'cancer' else [382, 462]}
    r['default'] = {'nuclei': f1_of('default_nuclei/score.json'), 'cancer': 0.775, 'endo': 0.137}[t]
    S['tasks'][t] = r
S['manual'] = {'nuclei': 441, 'cancer': 124, 'endo': 382}
S['manual_half'] = HALF_N
json.dump(S, open('fig_scores.json', 'w'), indent=1)
for t in TASKS:
    print(t, {k: v for k, v in S['tasks'][t].items() if k != 'draw'})
