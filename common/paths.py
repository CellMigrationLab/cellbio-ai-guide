"""Repository paths. Scripts import these instead of hard-coding locations."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

# Legacy scripts concatenate file names onto a directory string ending in "/" (U + "name.tif").
RAW = str(RAW_DIR) + "/"


def raw_file(name: str) -> Path:
    """Path of a raw data file; raises if it is missing so a wrong name never fails silently later."""
    path = RAW_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Raw data file not found: {path}. See data/README.md and data/manifest.csv.")
    return path
