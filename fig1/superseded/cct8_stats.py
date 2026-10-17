"""Superplot data, p-value heatmap and PCA for the CCT8 CDM shape dataset (Fig. 5D-E of doi:10.1242/jcs.265278).

Data: MorphoCoverage data/lab/cct8_cdm_morphology/objects.csv.gz (derived, values unchanged, from Zenodo 20704995, CC BY 4.0).
Test reproduces the source paper: randomization test on Cohen's d (cells as unit), 10,000 iterations,
Bonferroni over the 3 pairwise comparisons.
"""
import json
import numpy as np
import pandas as pd

o = pd.read_csv("/home/user/morphocoverage/data/lab/cct8_cdm_morphology/objects.csv.gz")
FEATS = ["Area", "Perim.", "Major", "Minor", "Feret", "MinFeret", "AR", "Circ.", "Round", "Solidity"]
CONDS = ["siCTRL", "siCCT8#5", "siCCT8#8"]
rng = np.random.default_rng(0)


def cohen_d(a, b):
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    return (a.mean() - b.mean()) / sp


def rand_p(a, b, n=10000):
    d0 = abs(cohen_d(a, b))
    pool = np.concatenate([a, b])
    na = len(a)
    cnt = 0
    for _ in range(n):
        rng.shuffle(pool)
        if abs(cohen_d(pool[:na], pool[na:])) >= d0:
            cnt += 1
    return (cnt + 1) / (n + 1)


pairs = [("siCTRL", "siCCT8#5"), ("siCTRL", "siCCT8#8"), ("siCCT8#5", "siCCT8#8")]
res = {}
for f in FEATS:
    for a, b in pairs:
        x = o.loc[o.condition == a, f].to_numpy(float)
        y = o.loc[o.condition == b, f].to_numpy(float)
        p = rand_p(x, y)
        res[f"{f}|{a}|{b}"] = {"d": float(cohen_d(x, y)), "p": p, "p_bonf": min(1.0, p * 3)}
for f in ["Area", "AR"]:
    print(f, {k.split("|", 1)[1]: (round(v["d"], 4), round(v["p_bonf"], 4)) for k, v in res.items() if k.startswith(f + "|")})

# superplot data for AR: every cell + repeat means
sp = {"feature": "AR", "cells": [], "means": []}
for c in CONDS:
    for r in (1, 2, 3):
        v = o.loc[(o.condition == c) & (o.biological_repeat == r), "AR"].to_numpy(float)
        sp["cells"] += [[c, r, float(x)] for x in v]
        sp["means"].append([c, r, float(v.mean())])
# PCA on standardised features (all cells)
X = o[FEATS].to_numpy(float)
Z = (X - X.mean(0)) / X.std(0, ddof=1)
U, S, Vt = np.linalg.svd(Z, full_matrices=False)
pcs = Z @ Vt[:2].T
var = (S ** 2 / (S ** 2).sum())[:2]
pca = {"var": var.tolist(), "pts": [[c, float(p1), float(p2)] for c, (p1, p2) in zip(o.condition, pcs)]}
json.dump({"stats": res, "superplot": sp, "pca": pca, "features": FEATS, "conditions": CONDS},
          open("data7/cct8_plots.json", "w"))
print("PCA variance explained", np.round(var, 3))
