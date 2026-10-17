"""Shared conversion of manual annotations (one implementation for all figures)."""
import numpy as np
from skimage.measure import label
from skimage.segmentation import clear_border, expand_labels

SLIVER_PX = 150  # regions smaller than this (px) between drawn lines are not cells


def lines_to_cells(lines: np.ndarray) -> np.ndarray:
    """Convert drawn junction lines (True on lines) to a label image of complete cells.

    Regions enclosed by the lines (4-connected) are labelled, grown by 2 px to close the line gap, cells touching the
    image border are removed (they are incomplete) and slivers smaller than SLIVER_PX are discarded.
    """
    if lines.dtype != bool:
        raise TypeError(f"lines must be a boolean mask (True on lines), got {lines.dtype}")
    lab = expand_labels(label(~lines, connectivity=1), 2)
    lab = clear_border(lab)
    sizes = np.bincount(lab.ravel())
    lab[np.isin(lab, np.where(sizes < SLIVER_PX)[0])] = 0
    return lab
