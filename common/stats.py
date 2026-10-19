"""Small statistics helpers that refuse undefined results instead of returning NaN."""
from __future__ import annotations

import numpy as np


def finite_values(values, *, name: str, n_min: int = 1) -> np.ndarray:
    """Return values as a 1D float array; raise if fewer than n_min values or any is not finite."""
    a = np.asarray(values, dtype=float)
    if a.ndim > 1:
        raise ValueError(f"{name}: expected a 1D sample, got shape {a.shape} (a 2D input used to be flattened silently)")
    a = a.ravel()
    if a.size < n_min:
        raise ValueError(f"{name}: need at least {n_min} values, got {a.size}")
    if not np.all(np.isfinite(a)):
        raise ValueError(f"{name}: contains NaN or infinite values")
    return a


def pearson_r(x, y, *, name: str) -> float:
    """Pearson correlation; raises for fewer than 3 pairs, unequal lengths or a constant variable."""
    a, b = finite_values(x, name=f"{name} (x)", n_min=3), finite_values(y, name=f"{name} (y)", n_min=3)
    if a.size != b.size:
        raise ValueError(f"{name}: x and y differ in length ({a.size} vs {b.size})")
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        raise ValueError(f"{name}: a variable is constant, correlation undefined")
    return float(np.corrcoef(a, b)[0, 1])
