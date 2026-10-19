"""Keep run records within the size limit of the git host: files larger than LIMIT_MB under fig3/v2/runs*/ (for example a
model an agent trained and saved in its folder) are moved to ARCHIVE (outside the repository) and listed, with size and
SHA-256, in LARGE_FILES.json next to where they were. Everything else in a run record is left as it is.
Usage: PYTHONPATH=. python fig3/v2/large_files.py      (run before committing)
"""
import hashlib
import json
import shutil
from pathlib import Path

from common.paths import REPO_ROOT

LIMIT_MB = 50
ARCHIVE = Path("/home/user/large_files_archive")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 24), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    for run in sorted((REPO_ROOT / "fig3" / "v2").glob("runs*/*")):
        big = [p for p in run.rglob("*") if p.is_file() and p.stat().st_size > LIMIT_MB * 1024 * 1024]
        if not big:
            continue
        manifest = run / "LARGE_FILES.json"
        listed = json.loads(manifest.read_text()) if manifest.exists() else []
        for p in big:
            rel = p.relative_to(REPO_ROOT)
            listed.append({"path": str(p.relative_to(run)), "size_bytes": p.stat().st_size, "sha256": sha256(p),
                           "moved_to": str(ARCHIVE / rel), "reason": f"larger than {LIMIT_MB} MB; not stored in git"})
            (ARCHIVE / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p), str(ARCHIVE / rel))
            print("moved", rel)
        manifest.write_text(json.dumps(listed, indent=1) + "\n")


if __name__ == "__main__":
    main()
