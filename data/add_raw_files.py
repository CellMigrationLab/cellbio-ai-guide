"""Add new raw files to data/raw under standard names, validated, and recorded in raw_name_map.csv and manifest.csv.

Usage:
  python data/add_raw_files.py --field 105 --source authors_unpublished \
      brightfield=/path/BF.tif dapi=/path/DAPI.tif pecam1=/path/PECAM.tif \
      cancer_cells_manual_labels=/path/cancer.tif endothelial_nuclei_manual_labels=/path/nuclei.tif \
      endothelial_junctions_annotator1=/path/junctions.tif
  python data/add_raw_files.py --prefix care_denoising --source authors_unpublished highsnr_reference=/path/GT.tif

Files are copied unchanged (bytes preserved) to data/raw/<field|prefix>_<role>.tif. All files of one call must share
the same 2D shape; label images must be integer-valued. Existing files are never overwritten. The source key(s) must
exist in sources.csv; roles and prefixes may contain only lower-case letters, digits and underscores. Every check runs
before any file is copied, and a failure during copying removes the files already copied in this call.
"""
import argparse
import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import tifffile

DATA = Path(__file__).resolve().parent
RAW = DATA / "raw"
NAME_MAP = DATA / "raw_name_map.csv"
SOURCES = DATA / "sources.csv"
NAME_PART = re.compile(r"^[a-z0-9_]+$")


def parse_pairs(pairs: list[str]) -> dict[str, Path]:
    """role=path arguments -> {role: Path}; raises on malformed pairs or missing files."""
    out = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Expected role=path, got {pair!r}")
        role, path = pair.split("=", 1)
        if not NAME_PART.match(role):
            raise ValueError(f"Role {role!r}: use lower-case letters, digits and underscores only")
        if role in out:
            raise ValueError(f"Role {role!r} given twice")
        if not Path(path).is_file():
            raise FileNotFoundError(path)
        out[role] = Path(path)
    return out


def check_source(source: str) -> None:
    """Every key of a ';'-separated source must be a source_key in sources.csv."""
    with SOURCES.open(newline="") as handle:
        known = {row["source_key"] for row in csv.DictReader(handle)}
    unknown = [key for key in source.split(";") if key not in known]
    if unknown:
        raise ValueError(f"Unknown source key(s) {unknown}; add them to {SOURCES.name} first")


def copy_all(copies: list[tuple[Path, Path]]) -> None:
    """Copy every source to its target; if one copy fails, remove those already made, then re-raise."""
    done = []
    try:
        for source, target in copies:
            shutil.copy2(source, target)
            done.append(target)
    except BaseException:
        for target in done:
            target.unlink(missing_ok=True)
        raise


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
    if not NAME_PART.match(stem):
        raise ValueError(f"Name prefix {stem!r}: use lower-case letters, digits and underscores only")
    check_source(args.source)
    files = parse_pairs(args.pairs)
    info = validate(files)
    targets = {role: RAW / f"{stem}_{role}{path.suffix.lower()}" for role, path in files.items()}
    existing = [t.name for t in targets.values() if t.exists()]
    if existing:
        raise FileExistsError(f"{existing} exist in data/raw; refusing to overwrite raw data")
    copy_all([(files[role], target) for role, target in targets.items()])
    rows = []
    for role, path in files.items():
        rows.append({"upload_name": path.name, "repo_name": targets[role].name, "source_key": args.source,
                     "content": info[role]})
        print(f"added {targets[role].name}: {info[role]}")
    with NAME_MAP.open("a", newline="") as handle:
        csv.DictWriter(handle, fieldnames=["upload_name", "repo_name", "source_key", "content"]).writerows(rows)
    subprocess.run([sys.executable, str(DATA / "make_manifest.py")], check=True)


if __name__ == "__main__":
    main()
