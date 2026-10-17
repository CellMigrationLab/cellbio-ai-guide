"""Create the files given to subject models in round 2 (all derived from data/raw, so they can be regenerated).

Writes fig3/round2/assets/:
  <task>_image.tif / _image.png      whole field as acquired (uint16) and an 8-bit preview (1st-99.7th percentile)
  <task>_image_left.tif               development half (x < 512), for the optimise row
  <task>_annotation_left.tif / .png   reference labels of the development half only (the right half is never shared)
Usage: PYTHONPATH=. python fig3/round2/make_assets.py
"""
import numpy as np
import tifffile
from PIL import Image
from skimage.segmentation import clear_border

from common.paths import REPO_ROOT, raw_file
from fig3.scoring.tasks import HALF_X, TASKS, reference

OUT = REPO_ROOT / "fig3" / "round2" / "assets"
IMAGE = {"nuclei": "field104_dapi.tif", "cancer": "field104_brightfield.tif", "endo": "field104_brightfield.tif"}
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


def main() -> None:
    """Write all assets for the three tasks."""
    OUT.mkdir(parents=True, exist_ok=True)
    for task in TASKS:
        image = tifffile.imread(raw_file(IMAGE[task]))
        tifffile.imwrite(OUT / f"{task}_image.tif", image, compression="zlib")
        preview(image.astype(float)).save(OUT / f"{task}_image.png")
        tifffile.imwrite(OUT / f"{task}_image_left.tif", image[:, :HALF_X], compression="zlib")
        left = reference(task)[:, :HALF_X].astype(np.int32)
        if task == "endo":
            left = clear_border(left)
        tifffile.imwrite(OUT / f"{task}_annotation_left.tif", left, compression="zlib")
        label_colours(left).save(OUT / f"{task}_annotation_left.png")
        print(task, image.shape, "left-half objects:", len(np.unique(left)) - 1)


if __name__ == "__main__":
    main()
