"""Sanity-check sheet (data/overview.png): for each question the figures address, the images and, separately, the
annotations used as reference, each drawn on its own (annotations are NOT overlaid on the images).

Image tiles: 8-bit preview (1st-99.7th percentile). Annotation tiles: each object in its own colour on black (label
images), the lines as drawn (junction annotations), or the boxes on black (DeepBacs). Object counts are read from the
annotation files themselves. Usage: PYTHONPATH=. python data/make_overview.py
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image, ImageDraw, ImageFont

from common.paths import RAW_DIR
from fig3.scoring.tasks import lines_to_cells

OUT = Path(__file__).resolve().parent / "overview.png"
THIRD = RAW_DIR / "third_party"
TILE, LABEL_H, ROW_HEAD, GAP = 300, 46, 40, 12
IMAGE_COLOUR, ANNOT_COLOUR, NONE_COLOUR = "#3b4a5c", "#1a7f37", "#9aa4b2"


@dataclass
class Tile:
    """One panel of the sheet: kind is 'image', 'annotation' or 'none'."""
    picture: Image.Image | None
    kind: str
    title: str
    detail: str = ""


@dataclass
class Question:
    """One row of the sheet: the question, the figures that use it, its images and its annotations."""
    title: str
    figures: str
    tiles: list[Tile] = field(default_factory=list)


def read(name: str) -> np.ndarray:
    return tifffile.imread(RAW_DIR / name)


def gray(image: np.ndarray) -> Image.Image:
    """8-bit preview of a 2D image (linear stretch, 1st-99.7th percentile); RGB images are passed through."""
    if image.ndim == 3:
        return Image.fromarray(image[..., :3].astype(np.uint8))
    image = np.asarray(image, float)
    lo, hi = np.percentile(image, (1, 99.7))
    if hi <= lo:
        raise ValueError("Image has no intensity range")
    return Image.fromarray((np.clip((image - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8))


def labels_picture(labels: np.ndarray, seed: int = 3) -> Image.Image:
    """Each object in its own random (fixed-seed) colour on black."""
    rng = np.random.default_rng(seed)
    lut = rng.integers(70, 256, size=(int(labels.max()) + 1, 3), dtype=np.uint8)
    lut[0] = 0
    return Image.fromarray(lut[labels])


def lines_picture(lines: np.ndarray) -> Image.Image:
    """Drawn junction lines, white on black, thickened for display."""
    from scipy.ndimage import binary_dilation
    return Image.fromarray((binary_dilation(lines > 0, iterations=1) * 255).astype(np.uint8))


def boxes_picture(xml: Path, size: tuple[int, int]) -> tuple[Image.Image, int, dict]:
    """Ground-truth boxes on black; returns (picture, number of boxes, count per class)."""
    picture, classes = Image.new("RGB", size, "black"), {}
    draw = ImageDraw.Draw(picture)
    palette = [(255, 90, 90), (90, 200, 255), (255, 210, 60), (150, 255, 120), (230, 120, 255), (255, 255, 255)]
    for obj in ET.parse(xml).getroot().iter("object"):
        name = obj.find("name").text
        classes.setdefault(name, 0)
        classes[name] += 1
        box = obj.find("bndbox")
        colour = palette[list(classes).index(name) % len(palette)]
        draw.rectangle([int(float(box.find(k).text)) for k in ("xmin", "ymin", "xmax", "ymax")], outline=colour, width=2)
    return picture, sum(classes.values()), classes


def n_objects(labels: np.ndarray) -> int:
    return int(len(np.unique(labels[labels > 0])))


def field_tiles(field: int) -> dict[str, list[Tile]]:
    """Image and annotation tiles of one annotated field, per question."""
    f = f"field{field}"
    bf, dapi, pecam = read(f"{f}_brightfield.tif"), read(f"{f}_dapi.tif"), read(f"{f}_pecam1.tif")
    cancer = read(f"{f}_cancer_cells_manual_labels.tif").astype(int)
    nuclei = read(f"{f}_endothelial_nuclei_manual_labels.tif").astype(int)
    lines1 = read(f"{f}_endothelial_junctions_annotator1.tif")
    lines2 = read(f"{f}_endothelial_junctions_annotator2.tif")
    tag = f"field {field}"
    return {
        "cancer": [Tile(gray(bf), "image", f"Brightfield, {tag}", "1022 x 1024 px, 0.65 um/px"),
                   Tile(labels_picture(cancer), "annotation", f"Manual cancer cells: {n_objects(cancer)}", tag)],
        "endo": [Tile(gray(bf), "image", f"Brightfield, {tag}", "image analysed"),
                 Tile(gray(pecam), "image", f"PECAM-1, {tag}", "image the outlines were drawn on"),
                 Tile(lines_picture(lines1), "annotation", f"Annotator 1: {n_objects(lines_to_cells(lines1 > 0))} cells",
                      f"{tag}, junction lines (reference)"),
                 Tile(lines_picture(lines2), "annotation", f"Annotator 2: {n_objects(lines_to_cells(lines2 > 0))} cells",
                      f"{tag}, junction lines (agreement)")],
        "nuclei": [Tile(gray(dapi), "image", f"DAPI, {tag}", ""),
                   Tile(labels_picture(nuclei), "annotation", f"Manual endothelial nuclei: {n_objects(nuclei)}", tag)],
        "pix2pix": [Tile(gray(read(f"{f}_pix2pix_predicted_dapi.tif")[1:1023]), "image", f"Predicted DAPI, {tag}", "pix2pix output"),
                    Tile(gray(read(f"{f}_pix2pix_predicted_pecam1.tif")[1:1023]), "image", f"Predicted PECAM-1, {tag}", "pix2pix output"),
                    Tile(gray(dapi), "annotation", f"Acquired DAPI, {tag}", "+ manual nuclei"),
                    Tile(gray(pecam), "annotation", f"Acquired PECAM-1, {tag}", "+ manual cells")],
    }


def questions() -> list[Question]:
    """The sheet's rows: annotated fields (104 = development/figures, 209 = test field) then the other examples."""
    a, b = field_tiles(104), field_tiles(209)
    det_png = THIRD / "deepbacs_ecoli_growth_stage/test_images/pos_8_frame_80_2.png"
    det_boxes, n_det, det_classes = boxes_picture(THIRD / "deepbacs_ecoli_growth_stage/test_annotations/pos_8_frame_80_2.xml",
                                                  Image.open(det_png).size)
    abx = THIRD / "deepbacs_antibiotic_phenotyping/stitched_images"
    abx_png = abx / "images/synthetic_image_23.png"
    abx_boxes, n_abx, abx_classes = boxes_picture(abx / "annotations/synthetic_image_23.xml", Image.open(abx_png).size)
    fmt = lambda d: ", ".join(f"{k} {v}" for k, v in d.items())  # noqa: E731
    return [
        Question("1. Cancer cells in brightfield (fields 104 and 209)", "Fig 1c, Fig 2a, Fig 3", a["cancer"] + b["cancer"]),
        Question("2. Endothelial cells in brightfield, annotated on PECAM-1 (fields 104 and 209)", "Fig 2a, Fig 3", a["endo"] + b["endo"]),
        Question("3. Endothelial nuclei in DAPI (fields 104 and 209)", "Fig 2d, Fig 3", a["nuclei"] + b["nuclei"]),
        Question("4. Artificial labelling: DAPI and PECAM-1 predicted from brightfield (fields 104 and 209)", "Fig 1a, Fig 2d",
                 a["pix2pix"] + b["pix2pix"]),
        Question("5. Denoising (CARE)", "Fig 1a, Fig 2c", [
            Tile(gray(read("care_denoising_acquired.tif")), "image", "Acquired (low SNR)", "0.6337 um/px"),
            Tile(gray(read("care_denoising_restored.tif")), "image", "CARE restored", "model output"),
            Tile(None, "none", "Ground truth: pending", "high-SNR acquisition to come")]),
        Question("6. Super-resolution (RCAN, BioSR endoplasmic reticulum)", "Fig 1a, Fig 2e", [
            Tile(gray(read("biosr_er_lowres_input.tif")), "image", "Low-resolution input", ""),
            Tile(gray(read("biosr_er_rcan_prediction.tif")), "image", "RCAN prediction", "model output"),
            Tile(gray(read("biosr_er_highres_reference.tif")), "annotation", "Reference: high-resolution acquisition", "no manual annotation")]),
        Question("7. Detection of bacteria (DeepBacs growth stage)", "Fig 1a", [
            Tile(Image.open(det_png).convert("RGB"), "image", "Test image pos_8_frame_80_2", "256 x 256 px"),
            Tile(det_boxes, "annotation", f"Ground-truth boxes: {n_det}", fmt(det_classes))]),
        Question("8. Classification of bacteria (DeepBacs antibiotics)", "Fig 1a", [
            Tile(Image.open(abx_png).convert("RGB"), "image", "Test image synthetic_image_23", ""),
            Tile(abx_boxes, "annotation", f"Ground-truth boxes: {n_abx}", fmt(abx_classes))]),
        Question("9. Illustrations only (nothing measured)", "Fig 1b, Fig 1c", [
            Tile(gray(read("hpmec_nuclei_max_projection.tif")), "image", "HPMEC nuclei (Fig 1b)", "no annotation"),
            Tile(gray(read("trackmate_capture_tracks.tif")), "image", "TrackMate capture (Fig 1c)", "no annotation")]),
    ]


def draw_tile(sheet: Image.Image, x: int, y: int, tile: Tile, fonts: tuple) -> None:
    """Draw one tile: coloured kind bar, title, detail, then the picture (or an empty box)."""
    draw = ImageDraw.Draw(sheet)
    colour = {"image": IMAGE_COLOUR, "annotation": ANNOT_COLOUR, "none": NONE_COLOUR}[tile.kind]
    draw.rectangle([x, y, x + TILE, y + 18], fill=colour)
    draw.text((x + 6, y + 2), {"image": "IMAGE", "annotation": "ANNOTATION / REFERENCE", "none": "ANNOTATION"}[tile.kind],
              fill="white", font=fonts[1])
    draw.text((x + 4, y + 21), tile.title, fill="black", font=fonts[1])
    draw.text((x + 4, y + 35), tile.detail, fill="#555555", font=fonts[2])
    top = y + LABEL_H + 4
    if tile.picture is None:
        draw.rectangle([x, top, x + TILE, top + TILE], outline=NONE_COLOUR, width=2)
        return
    picture = tile.picture.convert("RGB")
    picture.thumbnail((TILE, TILE))
    sheet.paste(picture, (x + (TILE - picture.width) // 2, top))
    draw.rectangle([x, top, x + TILE, top + TILE], outline=colour, width=2)


def main() -> None:
    rows = questions()
    cols = max(len(q.tiles) for q in rows)
    row_h = ROW_HEAD + LABEL_H + 4 + TILE + GAP
    sheet = Image.new("RGB", (GAP + cols * (TILE + GAP), len(rows) * row_h + GAP), "white")
    draw = ImageDraw.Draw(sheet)
    fonts = (ImageFont.load_default(size=19), ImageFont.load_default(size=13), ImageFont.load_default(size=12))
    for r, question in enumerate(rows):
        y = GAP + r * row_h
        draw.line([GAP, y - GAP // 2, sheet.width - GAP, y - GAP // 2], fill="#d0d7de", width=1)
        draw.text((GAP, y + 6), question.title, fill="black", font=fonts[0])
        draw.text((GAP + 900, y + 9), f"used in {question.figures}", fill="#555555", font=fonts[1])
        for c, tile in enumerate(question.tiles):
            draw_tile(sheet, GAP + c * (TILE + GAP), y + ROW_HEAD, tile, fonts)
        print(f"{question.title} | {question.figures} | " + " ; ".join(f"{t.kind}: {t.title}" for t in question.tiles))
    sheet.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
