"""Segment endothelial cells (whole-cell outlines, including the part under cancer cells)
in a 2D image made of N fields side by side; measure area and aspect ratio.
Input: image.tif (2D, uint16, 12-bit, 0.65 um/px)
Output: labels.tif, measurements.csv (label, area_um2, aspect_ratio), diagnostics.csv, intermediates/"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np, pandas as pd, tifffile
from scipy import ndimage as ndi
from skimage import io, measure, morphology, segmentation


@dataclass(frozen=True)
class Params:
    pixel_size_um: float = 0.65
    max_value_12bit: int = 4095
    n_fields: int = 2                        # fields side by side along X, segmented independently
    cell_diameter_um: float = 37.5           # middle of 25-50 um
    cellpose_model: str = "cpsam"
    flow_threshold: float = 0.4              # Cellpose default
    cellprob_threshold: float = 0.0          # Cellpose default
    cancer_contrast_k: float = 6.0           # STARTING VALUE: tune on the overlay
    cancer_smooth_sigma_px: float = 1.0
    cancer_close_radius_px: int = 2
    cancer_dilate_px: int = 3                # covers the halo outside the threshold
    cancer_min_area_um2: float = 50.0
    inpaint_sigma_px: float = 15.0           # background interpolation under cancer cells
    hidden_fill_distance_um: float = 10.0    # max reach when assigning leftover cancer pixels
    min_cell_area_um2: float = 150.0         # smaller = debris
    remove_border_objects: bool = True

    @property
    def cell_diameter_px(self) -> float:
        return self.cell_diameter_um / self.pixel_size_um

    def um2_to_px(self, a: float) -> int:
        return int(round(a / self.pixel_size_um**2))


def load_image(path: Path, p: Params) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found in {Path.cwd()}")
    im = tifffile.imread(path)
    if im.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X), got shape {im.shape}")
    if im.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {im.dtype}")
    if im.max() > p.max_value_12bit:
        raise ValueError(f"Max {im.max()} exceeds 12-bit range; data differ from assumptions")
    if im.max() == im.min():
        raise ValueError("Image is constant")
    return im


def field_slices(width: int, n_fields: int) -> list[slice]:
    if width % n_fields:
        raise ValueError(f"Width {width} not divisible by n_fields={n_fields}")
    w = width // n_fields
    return [slice(i * w, (i + 1) * w) for i in range(n_fields)]


def remove_small_components(mask: np.ndarray, min_px: int) -> np.ndarray:
    lab, n = ndi.label(mask)
    sizes = np.bincount(lab.ravel(), minlength=n + 1)
    keep = sizes >= min_px
    keep[0] = False
    return keep[lab]


def detect_cancer_cells(im: np.ndarray, p: Params) -> np.ndarray:
    """Heuristic (not an established method): pixels far from the field median (robust z-score)
    = bright/dark phase halo; close, fill holes, drop small blobs (debris), dilate."""
    s = ndi.gaussian_filter(im.astype(np.float32), p.cancer_smooth_sigma_px)
    med = np.median(s)
    sigma = 1.4826 * np.median(np.abs(s - med))
    if sigma == 0:
        raise ValueError("Zero robust sigma; cannot threshold")
    extreme = np.abs(s - med) > p.cancer_contrast_k * sigma
    closed = ndi.binary_closing(extreme, structure=morphology.disk(p.cancer_close_radius_px))
    filled = ndi.binary_fill_holes(closed)
    big = remove_small_components(filled, p.um2_to_px(p.cancer_min_area_um2))
    return ndi.binary_dilation(big, structure=morphology.disk(p.cancer_dilate_px))


def inpaint_background(im: np.ndarray, mask: np.ndarray, p: Params) -> np.ndarray:
    """Replace masked pixels by a normalised Gaussian average of unmasked pixels."""
    f = im.astype(np.float32)
    keep = (~mask).astype(np.float32)
    num = ndi.gaussian_filter(f * keep, p.inpaint_sigma_px)
    den = ndi.gaussian_filter(keep, p.inpaint_sigma_px)
    if (den[mask] < 1e-3).any():
        raise ValueError("Cancer-cell region too large for inpaint_sigma_px; increase it or check the mask")
    out = f.copy()
    out[mask] = num[mask] / den[mask]
    return out


def segment_cellpose(im: np.ndarray, p: Params) -> np.ndarray:
    """Cellpose normalises (1st-99th percentile) and rescales by 30/diameter internally."""
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model=p.cellpose_model)
    masks, _, _ = model.eval(im, diameter=p.cell_diameter_px, flow_threshold=p.flow_threshold,
                             cellprob_threshold=p.cellprob_threshold, normalize=True)
    if masks.shape != im.shape:
        raise RuntimeError(f"Cellpose output {masks.shape} != input {im.shape}")
    return masks.astype(np.int32)


def fill_hidden_pixels(labels: np.ndarray, cancer: np.ndarray, p: Params):
    """Give unlabelled pixels inside the cancer mask to the nearest cell (<= hidden_fill_distance_um).
    Returns (labels, boolean map of pixels assigned this way). This is an extrapolation."""
    reach = p.hidden_fill_distance_um / p.pixel_size_um
    expanded = segmentation.expand_labels(labels, distance=reach)
    assigned = (labels == 0) & cancer & (expanded > 0)
    return np.where(assigned, expanded, labels), assigned


def remove_small(labels: np.ndarray, p: Params) -> np.ndarray:
    small = np.flatnonzero(np.bincount(labels.ravel()) < p.um2_to_px(p.min_cell_area_um2))
    out = labels.copy()
    out[np.isin(out, small[small != 0])] = 0
    return out


def process_field(im: np.ndarray, p: Params):
    cancer = detect_cancer_cells(im, p)
    raw = segment_cellpose(inpaint_background(im, cancer, p), p)
    filled, assigned = fill_hidden_pixels(raw, cancer, p)
    cleaned = remove_small(filled, p)
    if p.remove_border_objects:
        cleaned = segmentation.clear_border(cleaned)   # field edges incl. the seam
    return raw, cancer, assigned, cleaned


def remove_border_objects_per_field(labels: np.ndarray, n_fields: int) -> np.ndarray:
    out = np.zeros_like(labels)
    for sl in field_slices(labels.shape[1], n_fields):
        out[:, sl] = segmentation.clear_border(labels[:, sl])
    return out


def relabel_consecutive(labels):
    return segmentation.relabel_sequential(labels)[0].astype(np.int32)


def measure_cells(labels, pixel_size_um: float) -> pd.DataFrame:
    """area in um^2; aspect ratio = major/minor axis of the moment-equivalent ellipse (>= 1)."""
    rows = []
    for r in measure.regionprops(labels):
        if r.axis_minor_length <= 0:
            raise ValueError(f"Label {r.label} is degenerate (zero minor axis)")
        rows.append({"label": r.label, "area_um2": r.area * pixel_size_um**2,
                     "aspect_ratio": r.axis_major_length / r.axis_minor_length})
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio"])


def diagnostics(labels, cancer, assigned) -> pd.DataFrame:
    n = labels.max() + 1
    area = np.bincount(labels.ravel(), minlength=n)
    under = np.bincount(labels.ravel(), weights=cancer.ravel(), minlength=n)
    extrap = np.bincount(labels.ravel(), weights=assigned.ravel(), minlength=n)
    idx = np.arange(1, n)
    return pd.DataFrame({"label": idx, "fraction_under_cancer": under[1:] / area[1:],
                         "fraction_extrapolated": extrap[1:] / area[1:]})


def make_overlay(im, labels, cancer):
    lo, hi = np.percentile(im, (1, 99))
    rgb = np.dstack([np.clip((im.astype(np.float32) - lo) / (hi - lo), 0, 1)] * 3)
    rgb[segmentation.find_boundaries(cancer, mode="inner")] = (0, 1, 1)    # cancer mask: cyan
    rgb[segmentation.find_boundaries(labels, mode="inner")] = (1, 0, 0)    # cells: red
    return (rgb * 255).astype(np.uint8)


def run(image_path=Path("image.tif"), out_dir=Path(".")):
    p = Params()
    inter = out_dir / "intermediates"
    inter.mkdir(exist_ok=True)
    im = load_image(image_path, p)
    raw, cancer, assigned, final = (np.zeros(im.shape, t) for t in (np.int32, bool, bool, np.int32))
    offset = 0
    for sl in field_slices(im.shape[1], p.n_fields):
        r, c, a, f = process_field(im[:, sl], p)
        raw[:, sl] = np.where(r > 0, r + offset, 0)
        final[:, sl] = np.where(f > 0, f + offset, 0)
        cancer[:, sl], assigned[:, sl] = c, a
        offset += int(r.max())
        print(f"Field {sl.start}-{sl.stop}: Cellpose objects {r.max()}, kept {len(np.unique(f)) - 1}")
    final = relabel_consecutive(final)
    table = measure_cells(final, p.pixel_size_um)
    tifffile.imwrite(out_dir / "labels.tif", final)
    table.to_csv(out_dir / "measurements.csv", index=False)
    diagnostics(final, cancer, assigned).to_csv(out_dir / "diagnostics.csv", index=False)
    tifffile.imwrite(inter / "cellpose_raw_labels.tif", raw)
    tifffile.imwrite(inter / "cancer_mask.tif", (cancer * 255).astype(np.uint8))
    io.imsave(inter / "overlay.png", make_overlay(im, final, cancer), check_contrast=False)
    print(f"Endothelial cells: {len(table)}; median area {table.area_um2.median():.0f} um2; "
          f"median AR {table.aspect_ratio.median():.2f}")


if __name__ == "__main__":
    run()
