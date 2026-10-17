"""Sanity-check sheet: every image in data/raw with its manual annotation drawn on top (data/overview.png).

Each tile shows one image (8-bit preview, 1st-99.7th percentile) and, where one exists, the annotation as outlines
or boxes, with the number of annotated objects counted from the annotation file itself.
Usage: PYTHONPATH=. python data/make_overview.py
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image, ImageDraw, ImageFont
from skimage.segmentation import find_boundaries

from common.paths import RAW_DIR
from fig3.scoring.tasks import lines_to_cells

TILE = 420
OUT = Path(__file__).resolve().parent / "overview.png"
THIRD = RAW_DIR / "third_party"


def gray(image: np.ndarray) -> np.ndarray:
    """8-bit preview of a 2D image (linear stretch, 1st-99.7th percentile)."""
    image = np.asarray(image, float)
    lo, hi = np.percentile(image, (1, 99.7))
    if hi <= lo:
        raise ValueError("Image has no intensity range")
    return (np.clip((image - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)


def overlay(image: np.ndarray, labels: np.ndarray | None, colour: tuple) -> Image.Image:
    """RGB tile: grey image with the label outlines in one colour."""
    rgb = np.stack([gray(image)] * 3, axis=-1) if image.ndim == 2 else image[..., :3].astype(np.uint8)
    if labels is not None:
        rgb[find_boundaries(labels, mode="inner")] = colour
    return Image.fromarray(rgb)


def boxes_tile(png: Path, xml: Path, colour: tuple) -> tuple[Image.Image, int]:
    """RGB tile of a DeepBacs image with its ground-truth boxes; returns (tile, number of boxes)."""
    image = Image.open(png).convert("RGB")
    draw, n = ImageDraw.Draw(image), 0
    for obj in ET.parse(xml).getroot().iter("object"):
        b = obj.find("bndbox")
        draw.rectangle([int(float(b.find(k).text)) for k in ("xmin", "ymin", "xmax", "ymax")], outline=colour, width=1)
        n += 1
    return image, n


def count(labels: np.ndarray) -> int:
    return int(len(np.unique(labels[labels > 0])))


def tiles() -> list[tuple[Image.Image, str, str]]:
    """(tile, title, figures using it) for every image."""
    r = lambda name: tifffile.imread(RAW_DIR / name)  # noqa: E731 - short local reader
    bf, dapi, pecam = r("field104_brightfield.tif"), r("field104_dapi.tif"), r("field104_pecam1.tif")
    cancer = r("field104_cancer_cells_manual_labels.tif").astype(int)
    nuclei = r("field104_endothelial_nuclei_manual_labels.tif").astype(int)
    endo1 = lines_to_cells(r("field104_endothelial_junctions_annotator1.tif") > 0)
    endo2 = lines_to_cells(r("field104_endothelial_junctions_annotator2.tif") > 0)
    stardist = r("field104_cancer_cells_stardist_custom_labels.tif").astype(int)
    out = [
        (overlay(bf, cancer, (255, 0, 200)), f"Brightfield + MANUAL cancer cells (n={count(cancer)})", "Fig 1c, 2a, 3"),
        (overlay(bf, endo1, (0, 220, 255)), f"Brightfield + MANUAL endothelial cells, annotator 1 (n={count(endo1)})", "Fig 2a, 3"),
        (overlay(pecam, endo2, (255, 200, 0)), f"PECAM-1 + MANUAL endothelial cells, annotator 2 (n={count(endo2)})", "Fig 2a/d (agreement)"),
        (overlay(dapi, nuclei, (0, 255, 0)), f"DAPI + MANUAL endothelial nuclei (n={count(nuclei)})", "Fig 2d, 3"),
        (overlay(bf, stardist, (255, 140, 0)), f"Brightfield + custom StarDist (model, n={count(stardist)})", "Fig 1c, 2a (candidate)"),
        (overlay(r("field104_pix2pix_predicted_pecam1.tif")[1:1023], endo1, (0, 220, 255)), "pix2pix PECAM-1 (predicted) + MANUAL annotator 1", "Fig 1a, 2d"),
        (overlay(r("field104_pix2pix_predicted_dapi.tif")[1:1023], nuclei, (0, 255, 0)), "pix2pix DAPI (predicted) + MANUAL nuclei", "Fig 1a, 2d"),
        (overlay(r("care_denoising_acquired.tif"), None, (0, 0, 0)), "CARE: acquired (no manual annotation)", "Fig 1a, 2c"),
        (overlay(r("care_denoising_restored.tif"), None, (0, 0, 0)), "CARE: restored (no manual annotation)", "Fig 1a, 2c"),
        (overlay(r("biosr_er_lowres_input.tif"), None, (0, 0, 0)), "BioSR ER: low-res input", "Fig 1a, 2e"),
        (overlay(r("biosr_er_rcan_prediction.tif"), None, (0, 0, 0)), "BioSR ER: RCAN prediction", "Fig 1a, 2e"),
        (overlay(r("biosr_er_highres_reference.tif"), None, (0, 0, 0)), "BioSR ER: high-res acquisition (reference)", "Fig 2e"),
        (overlay(r("hpmec_nuclei_max_projection.tif"), None, (0, 0, 0)), "HPMEC nuclei (no annotation; illustration)", "Fig 1b"),
        (Image.fromarray(r("trackmate_capture_tracks.tif")[..., :3]), "TrackMate capture (no annotation)", "Fig 1c"),
    ]
    det, n_det = boxes_tile(THIRD / "deepbacs_ecoli_growth_stage/test_images/pos_8_frame_80_2.png",
                            THIRD / "deepbacs_ecoli_growth_stage/test_annotations/pos_8_frame_80_2.xml", (255, 60, 60))
    out.append((det, f"DeepBacs detection + GROUND-TRUTH boxes (n={n_det})", "Fig 1a"))
    abx = THIRD / "deepbacs_antibiotic_phenotyping/stitched_images"
    cls, n_cls = boxes_tile(abx / "images/synthetic_image_23.png", abx / "annotations/synthetic_image_23.xml", (255, 60, 60))
    out.append((cls, f"DeepBacs classification + GROUND-TRUTH boxes (n={n_cls})", "Fig 1a"))
    return out


def main() -> None:
    items = tiles()
    cols, head = 4, 54
    sheet = Image.new("RGB", (cols * TILE, ((len(items) + cols - 1) // cols) * (TILE + head)), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=14)
    for k, (tile, title, used) in enumerate(items):
        x, y = (k % cols) * TILE, (k // cols) * (TILE + head)
        tile = tile.copy()
        tile.thumbnail((TILE - 10, TILE - 10))
        sheet.paste(tile, (x + 5, y + head))
        draw.text((x + 6, y + 6), title, fill="black", font=font)
        draw.text((x + 6, y + 28), f"used in: {used}", fill="#555555", font=font)
        print(f"{title} | {used}")
    sheet.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
