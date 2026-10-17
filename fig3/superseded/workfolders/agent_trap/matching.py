import numpy as np


def match(gt, pr, thr=0.5):
    m = (gt > 0) & (pr > 0)
    pairs = {}
    for g, p in zip(gt[m], pr[m]):
        pairs[(g, p)] = pairs.get((g, p), 0) + 1
    ga = dict(zip(*np.unique(gt[gt > 0], return_counts=True)))
    pa = dict(zip(*np.unique(pr[pr > 0], return_counts=True)))
    ious = sorted(((n / (ga[g] + pa[p] - n), g, p) for (g, p), n in pairs.items()), reverse=True)
    ug, up, matched = set(), set(), []
    for iou, g, p in ious:
        if iou >= thr and g not in ug and p not in up:
            ug.add(g); up.add(p); matched.append((g, p, iou))
    return matched, set(ga) - ug, set(pa) - up
