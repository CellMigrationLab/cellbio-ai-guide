"""Write or verify data/manifest.csv: one row per file under data/raw with its SHA-256, size and source.

Usage:  python data/make_manifest.py            write the manifest
        python data/make_manifest.py --verify   check every file against the manifest (exit 1 on any mismatch)
"""
import csv
import hashlib
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent
RAW = DATA / "raw"
MANIFEST = DATA / "manifest.csv"
THIRD_PARTY_SOURCES = {"deepbacs_ecoli_growth_stage": "deepbacs_growth_stage;deepbacs2022",
                       "deepbacs_antibiotic_phenotyping": "deepbacs_antibiotic;deepbacs2022"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def source_of(rel: Path, names: dict) -> str:
    if rel.parts[0] == "third_party":
        return THIRD_PARTY_SOURCES[rel.parts[1]]
    if rel.name not in names:
        raise KeyError(f"{rel} has no entry in data/raw_name_map.csv")
    return names[rel.name]


def main(verify: bool) -> None:
    names = {r["repo_name"]: r["source_key"] for r in csv.DictReader(open(DATA / "raw_name_map.csv"))}
    files = sorted(p for p in RAW.rglob("*") if p.is_file())
    if verify:
        rows = {r["path"]: r for r in csv.DictReader(open(MANIFEST))}
        bad = [str(p.relative_to(DATA)) for p in files if rows.get(str(p.relative_to(DATA)), {}).get("sha256") != sha256(p)]
        missing = [k for k in rows if not (DATA / k).is_file()]
        for item in bad + missing:
            print("MISMATCH or MISSING:", item)
        print(f"{len(files)} files checked, {len(bad) + len(missing)} problems")
        raise SystemExit(1 if bad or missing else 0)
    with MANIFEST.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["path", "bytes", "sha256", "source_key"])
        for path in files:
            rel = path.relative_to(RAW)
            writer.writerow([str(path.relative_to(DATA)), path.stat().st_size, sha256(path), source_of(rel, names)])
    print(f"wrote {MANIFEST} ({len(files)} files)")


if __name__ == "__main__":
    main("--verify" in sys.argv[1:])
