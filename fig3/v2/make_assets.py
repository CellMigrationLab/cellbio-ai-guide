"""Create the files given to subject models in round 2 (all derived from data/raw, so they can be regenerated).

Design (fig3/PROTOCOL_V2.md, section 2): field 104 is the DEVELOPMENT image (a model may see it and its full manual
annotation); field 209 is the TEST image (only its image is ever given, to run a frozen script/pipeline on or, in the
direct-answer row, to answer about; its annotation is never given to a model).

Writes fig3/v2/assets/:
  dev_<task>_image.tif / .png         field 104 image (uint16 and pixel size as acquired; 8-bit preview, 1st-99.7th
                                      percentile)
  dev_<task>_annotation.tif / .png    field 104 manual annotation (label image; coloured preview)
  test_<task>_image.tif / .png        field 209 image (never its annotation)
  halfdev_<task>_image.tif / .png     rows B and C (revision of 19 Oct 2026, PROTOCOL_V2 section 2): ONE image of the same
                                      size as a field, a mosaic of the LEFT halves (x < 512) of field 104 and field 209
  halfdev_<task>_annotation.tif / .png  manual annotation of that mosaic (object ids offset so they stay unique)
  The RIGHT halves (x >= 512) of both fields are the held-out set of rows B and C: pipelines run on the whole
  fields (dev_/test_ images), scoring crops to the right halves (fig3.scoring.tasks.score_heldout).
Usage: PYTHONPATH=. python fig3/v2/make_assets.py
"""
import numpy as np
import tifffile
from PIL import Image

from common.paths import REPO_ROOT, raw_file
from fig3.scoring.tasks import HALF_X, TASKS, reference

OUT = REPO_ROOT / "fig3" / "v2" / "assets"
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
    with tifffile.TiffFile(raw_file(f"field{field}_{IMAGE_ROLE[task]}.tif")) as tif:
        image = tif.asarray()
        x_res, y_res = (tif.pages[0].tags[k].value for k in ("XResolution", "YResolution"))
        unit = tif.imagej_metadata["unit"]
    # the pixel size as acquired (ImageJ calibration, as in data/raw); other ImageJ fields, such as the channel label
    # with the source file name, are not copied
    tifffile.imwrite(OUT / f"{prefix}_{task}_image.tif", image, imagej=True, resolution=(x_res, y_res),
                     metadata={"unit": unit}, compression="zlib")
    preview(image.astype(float)).save(OUT / f"{prefix}_{task}_image.png")


def read_image(field: int, task: str):
    """Image of a field as acquired, with the ImageJ calibration (x_res, y_res, unit)."""
    with tifffile.TiffFile(raw_file(f"field{field}_{IMAGE_ROLE[task]}.tif")) as tif:
        image = tif.asarray()
        x_res, y_res = (tif.pages[0].tags[k].value for k in ("XResolution", "YResolution"))
        return image, (x_res, y_res), tif.imagej_metadata["unit"]


def write_halfdev(task: str) -> None:
    """Mosaic of the left halves of the development field (104) and the second field (209), image and annotation."""
    (im_a, res_a, unit_a), (im_b, res_b, unit_b) = read_image(DEV_FIELD, task), read_image(TEST_FIELD, task)
    if im_a.shape != im_b.shape or im_a.dtype != im_b.dtype or res_a != res_b or unit_a != unit_b:
        raise ValueError("fields 104 and 209 differ in shape, type or calibration; cannot make a mosaic")
    mosaic = np.concatenate([im_a[:, :HALF_X], im_b[:, :HALF_X]], axis=1)
    tifffile.imwrite(OUT / f"halfdev_{task}_image.tif", mosaic, imagej=True, resolution=res_a,
                     metadata={"unit": unit_a}, compression="zlib")
    preview(mosaic.astype(float)).save(OUT / f"halfdev_{task}_image.png")
    left_a, left_b = (reference(task, f)[:, :HALF_X].astype(np.int32) for f in (DEV_FIELD, TEST_FIELD))
    left_b = np.where(left_b > 0, left_b + int(left_a.max()), 0).astype(np.int32)
    annotation = np.concatenate([left_a, left_b], axis=1)
    tifffile.imwrite(OUT / f"halfdev_{task}_annotation.tif", annotation, compression="zlib")
    label_colours(annotation).save(OUT / f"halfdev_{task}_annotation.png")
    print(task, "half-dev objects (incl. objects cut at x = 512):", len(np.unique(annotation)) - 1)


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
        write_halfdev(task)
        print(task, "dev objects:", len(np.unique(annotation)) - 1,
              "| test objects (not shared):", len(np.unique(reference(task, TEST_FIELD))) - 1)


if __name__ == "__main__":
    main()
