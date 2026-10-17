"""Pix2pix outputs (predicted images and their segmentations) are 1024 x 1024 px with one padded row at the top; the
acquired images are 1022 x 1024. Rows 1-1022 of a pix2pix file register with the acquired field (checked visually for
fields 104 and 209)."""
from __future__ import annotations

import numpy as np
import tifffile

from common.paths import raw_file

PIX2PIX_SHAPE = (1024, 1024)
ACQUIRED_SHAPE = (1022, 1024)


def read_pix2pix(name: str) -> np.ndarray:
    """Read a pix2pix file from data/raw and return the rows that register with the acquired image."""
    image = tifffile.imread(raw_file(name))
    if image.shape != PIX2PIX_SHAPE:
        raise ValueError(f"{name}: expected {PIX2PIX_SHAPE}, got {image.shape}; the one-row offset may not apply")
    return image[1:1 + ACQUIRED_SHAPE[0]]
