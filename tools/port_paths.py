"""Rewrite working-folder paths in a ported script to repository paths (used once while porting).

Edits made (and nothing else, so the logic of each script is unchanged):
  * `U = "/root/.claude/uploads/<session>/"`  ->  `from common.paths import RAW as U`
  * upload file names (e.g. "cccf774d-BF.tif")  ->  repository names from data/raw_name_map.csv
  * `sys.path.insert(..., "<scratch>/fig2")` lines removed; `from matching import` -> `from common.matching import`
Any other absolute path left in the file is reported, never silently kept.

Usage: python tools/port_paths.py FILE [FILE ...]   (edits in place, prints a report line per file)
"""
import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NAME_MAP = {row["upload_name"]: row["repo_name"] for row in csv.DictReader(open(REPO / "data" / "raw_name_map.csv"))}
UPLOAD_DIR_ASSIGN = re.compile(r'^(\s*)U\s*=\s*["\']/root/\.claude/uploads/[^"\']*["\']\s*$', re.M)
SCRATCH_SYSPATH = re.compile(r"^\s*sys\.path\.insert\(0,\s*['\"]/tmp/[^'\"]*['\"]\)\s*;?\s*$", re.M)
ABSOLUTE_PATH = re.compile(r"['\"](/(?:tmp|root|home)/[^'\"]*)['\"]")


def port(path: Path) -> list[str]:
    """Apply the edits to one file; return the absolute paths that remain (to be handled by hand)."""
    text = path.read_text()
    text = UPLOAD_DIR_ASSIGN.sub(r"\1from common.paths import RAW as U", text)
    text = SCRATCH_SYSPATH.sub("", text)
    text = re.sub(r"^(\s*)from matching import", r"\1from common.matching import", text, flags=re.M)
    for upload_name, repo_name in NAME_MAP.items():
        text = text.replace(upload_name, repo_name)
    path.write_text(text)
    return ABSOLUTE_PATH.findall(text)


def main(files: list[str]) -> None:
    """Port each file in place and report any absolute path left in it."""
    if not files:
        raise SystemExit(__doc__)
    for name in files:
        left = port(Path(name))
        print(f"{name}: {'OK' if not left else 'ABSOLUTE PATHS LEFT: ' + ', '.join(sorted(set(left)))}")


if __name__ == "__main__":
    main(sys.argv[1:])
