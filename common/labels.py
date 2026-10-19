"""Strict reading of instance label images (0 = background, 1..n = objects).

Every score and measurement reads label images through `validate_labels` / `read_labels`, so an invalid image (a
probability map, fractional or negative values, NaN, a stack, the wrong shape) raises instead of being silently cast
to integers.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import tifffile


class InvalidLabels(ValueError):
    """A label image that cannot be interpreted as instance labels."""


def validate_labels(array: np.ndarray, *, name: str = "labels", expected_shape: tuple[int, int] | None = None,
                    squeeze: bool = False) -> np.ndarray:
    """Return `array` as an int64 label image after checking it; raise InvalidLabels otherwise.

    squeeze=True removes singleton axes first (e.g. a (1, Y, X) TIFF); any other extra dimension is an error.
    """
    a = np.asarray(array)
    if squeeze:
        a = np.squeeze(a)
    if a.ndim != 2:
        raise InvalidLabels(f"{name}: expected a 2D label image, got shape {a.shape}")
    if expected_shape is not None and a.shape != tuple(expected_shape):
        raise InvalidLabels(f"{name}: expected shape {tuple(expected_shape)}, got {a.shape}")
    if a.dtype == bool or not np.issubdtype(a.dtype, np.integer) and not np.issubdtype(a.dtype, np.floating):
        raise InvalidLabels(f"{name}: expected integer labels, got dtype {a.dtype}")
    if np.issubdtype(a.dtype, np.floating):
        if not np.all(np.isfinite(a)):
            raise InvalidLabels(f"{name}: contains NaN or infinite values")
        if not np.array_equal(a, np.round(a)):
            raise InvalidLabels(f"{name}: contains non-integer values (a probability map or a resampled image?)")
    if a.size and a.min() < 0:
        raise InvalidLabels(f"{name}: contains negative values")
    if a.size and a.max() > np.iinfo(np.int64).max:
        raise InvalidLabels(f"{name}: values too large for int64")
    return a.astype(np.int64)


def read_labels(path: str | Path, *, expected_shape: tuple[int, int] | None = None, squeeze: bool = False,
                rows: slice | None = None) -> np.ndarray:
    """Read a label TIFF and validate it (optionally after selecting `rows`, e.g. a registered row range)."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"label image not found: {path}")
    a = tifffile.imread(path)
    if rows is not None:
        a = a[rows]
    return validate_labels(a, name=path.name, expected_shape=expected_shape, squeeze=squeeze)
