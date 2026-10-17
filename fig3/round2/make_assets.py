"""Create the files given to subject models in round 2 (all derived from data/raw, so they can be regenerated).

Design (fig3/STRATEGY.md, section 2): field 104 is the DEVELOPMENT image (a model may see it and its full manual
annotation); field 209 is the TEST image (only its image is ever given, to run a frozen script/pipeline on or, in the
direct-answer row, to answer about; its annotation is never given to a model).

Writes fig3/round2/assets/:
  dev_<task>_image.tif / .png         field 104 image (uint16 as acquired; 8-bit preview, 1st-99.7th percentile)
  dev_<task>_annotation.tif / .png    field 104 manual annotation (label image; coloured preview)
  test_<task>_image.tif / .png        field 209 image (never its annotation)
Usage: PYTHONPATH=. python fig3/round2/make_assets.py
"""
import numpy as np
import tifffile
from PIL import Image

from common.paths import REPO_ROOT, raw_file
from fig3.scoring.tasks import TASKS, reference

OUT = REPO_ROOT / "fig3" / "round2" / "assets"
DEV_FIELD, TEST_FIELD = 104, 209
IMAGE_ROLE = {"nuclei": "dapi", "cancer": "brightfield", "endo": "brightfield"}
PREVIEW_PERCENTILES = (1.0, 99.7)


def preview(image: np.ndarray) -> Image.Image:
    """8-bit display preview (linear stretch between PREVIEW_PERCENTILES)."""
    lo, hi = np.percentile(image, PREVIEW_PERCENTILES)
    if hi <= lo:
        raise ValueError("Image has no intensity range")
    return Image.fromarray(np.round(np.clip((image - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8))


def label_colours(labels: np.ndarray, seed: int = 3) -> Image.Image:
    """RGB rendering of a label image with random, fixed-seed colours (background black)."""
    rng = np.random.default_rng(seed)
    lut = rng.integers(60, 256, size=(int(labels.max()) + 1, 3), dtype=np.uint8)
    lut[0] = 0
    return Image.fromarray(lut[labels])


def write_image(prefix: str, field: int, task: str) -> None:
    """Write a field's image for a task as TIFF (unchanged values) and PNG preview."""
    image = tifffile.imread(raw_file(f"field{field}_{IMAGE_ROLE[task]}.tif"))
    tifffile.imwrite(OUT / f"{prefix}_{task}_image.tif", image, compression="zlib")
    preview(image.astype(float)).save(OUT / f"{prefix}_{task}_image.png")


def main() -> None:
    """Write development and test assets for the three tasks."""
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*"):
        old.unlink()  # assets are fully regenerated; nothing else lives here
    for task in TASKS:
        write_image("dev", DEV_FIELD, task)
        write_image("test", TEST_FIELD, task)
        annotation = reference(task, DEV_FIELD).astype(np.int32)
        tifffile.imwrite(OUT / f"dev_{task}_annotation.tif", annotation, compression="zlib")
        label_colours(annotation).save(OUT / f"dev_{task}_annotation.png")
        print(task, "dev objects:", len(np.unique(annotation)) - 1,
              "| test objects (not shared):", len(np.unique(reference(task, TEST_FIELD))) - 1)


if __name__ == "__main__":
    main()
