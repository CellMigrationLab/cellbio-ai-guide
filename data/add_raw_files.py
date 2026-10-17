"""Add new raw files to data/raw under standard names, validated, and recorded in raw_name_map.csv and manifest.csv.

Usage:
  python data/add_raw_files.py --field 105 --source authors_unpublished \
      brightfield=/path/BF.tif dapi=/path/DAPI.tif pecam1=/path/PECAM.tif \
      cancer_cells_manual_labels=/path/cancer.tif endothelial_nuclei_manual_labels=/path/nuclei.tif \
      endothelial_junctions_annotator1=/path/junctions.tif
  python data/add_raw_files.py --prefix care_denoising --source authors_unpublished highsnr_reference=/path/GT.tif

Files are copied unchanged (bytes preserved) to data/raw/<field|prefix>_<role>.tif. All files of one call must share
the same 2D shape; label images must be integer-typed. Existing files are never overwritten.
"""
import argparse
import csv
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import tifffile

DATA = Path(__file__).resolve().parent
RAW = DATA / "raw"
NAME_MAP = DATA / "raw_name_map.csv"


def parse_pairs(pairs: list[str]) -> dict[str, Path]:
    """role=path arguments -> {role: Path}; raises on malformed pairs or missing files."""
    out = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Expected role=path, got {pair!r}")
        role, path = pair.split("=", 1)
        if not Path(path).is_file():
            raise FileNotFoundError(path)
        out[role] = Path(path)
    return out


def validate(files: dict[str, Path]) -> dict[str, str]:
    """Check that all images are 2D with one shared shape and that label images are integer; return descriptions."""
    shapes, info = {}, {}
    for role, path in files.items():
        image = np.squeeze(tifffile.imread(path))
        if image.ndim != 2:
            raise ValueError(f"{role}: expected a 2D image, got shape {image.shape}")
        if "labels" in role and not np.issubdtype(image.dtype, np.integer):
            if not np.array_equal(image, np.round(image)):
                raise ValueError(f"{role}: label image has non-integer values ({image.dtype})")
        shapes[role] = image.shape
        n = len(np.unique(image[image > 0])) if "labels" in role else None
        info[role] = f"{image.shape[1]} x {image.shape[0]} px, {image.dtype}" + (f", {n} objects" if n is not None else "")
    if len(set(shapes.values())) > 1:
        raise ValueError(f"Images differ in shape: {shapes}")
    return info


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--field", help="field number, e.g. 105 (files named field105_<role>.tif)")
    group.add_argument("--prefix", help="name prefix for non-field data, e.g. care_denoising")
    parser.add_argument("--source", required=True, help="source key from data/sources.csv")
    parser.add_argument("pairs", nargs="+", help="role=path")
    args = parser.parse_args()
    stem = f"field{args.field}" if args.field else args.prefix
    files = parse_pairs(args.pairs)
    info = validate(files)
    rows = []
    for role, path in files.items():
        target = RAW / f"{stem}_{role}{path.suffix.lower()}"
        if target.exists():
            raise FileExistsError(f"{target} exists; refusing to overwrite raw data")
        shutil.copy2(path, target)
        rows.append({"upload_name": path.name, "repo_name": target.name, "source_key": args.source, "content": info[role]})
        print(f"added {target.name}: {info[role]}")
    with NAME_MAP.open("a", newline="") as handle:
        csv.DictWriter(handle, fieldnames=["upload_name", "repo_name", "source_key", "content"]).writerows(rows)
    subprocess.run([sys.executable, str(DATA / "make_manifest.py")], check=True)


if __name__ == "__main__":
    main()
