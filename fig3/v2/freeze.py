"""Freeze of Figure 3 protocol v2 (PROTOCOL_V2 section 11): SHA-256 of every file that defines the protocol, plus the
subject model ID and the Claude Code CLI version. fig3/tests/test_v2_freeze.py fails if any file changes.

Usage: PYTHONPATH=. python fig3/v2/freeze.py      (writes fig3/v2/FREEZE.json; run once, at the freeze)
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone

from common.paths import REPO_ROOT
from fig3.v2.run_operator import MODEL

V2 = REPO_ROOT / "fig3" / "v2"
FROZEN = (  # protocol, prompts and tables, answer sheet, operator, runner, scorer and the code they rely on, assets,
            # environment (repository-relative; patterns are expanded in sorted order)
    "fig3/PROTOCOL_V2.md", "fig3/v2/prompts/*.txt", "fig3/v2/rows.csv", "fig3/v2/scenarios.csv",
    "fig3/v2/answer_sheet.md", "fig3/v2/run_operator.py", "fig3/v2/runner.py", "fig3/v2/score.py",
    "fig3/v2/make_protocol.py", "fig3/v2/make_assets.py", "fig3/v2/freeze.py", "fig3/v2/assets/*",
    "fig3/v2/environment_freeze.txt", "fig3/scoring/tasks.py", "common/labels.py", "common/matching.py",
    "common/annotations.py", "common/metadata.py", "common/stats.py", "common/paths.py", "box1/box1_final.md",
)


def frozen_files() -> list[str]:
    out = []
    for pattern in FROZEN:
        hits = sorted(REPO_ROOT.glob(pattern))
        if not hits:
            raise FileNotFoundError(f"nothing matches {pattern}")
        out += [str(p.relative_to(REPO_ROOT)) for p in hits if p.is_file()]
    return out


def sha256(path: str) -> str:
    return hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()


def main() -> None:
    if (V2 / "FREEZE.json").exists():
        raise SystemExit("FREEZE.json exists: the protocol is frozen (changes go to deviations.md)")
    version = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    record = {"frozen_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "subject_model": MODEL, "cli_version": version, "python": sys.version.split()[0],
              "files": {f: sha256(f) for f in frozen_files()}}
    (V2 / "FREEZE.json").write_text(json.dumps(record, indent=1) + "\n")
    print(len(record["files"]), "files frozen;", MODEL, version)


if __name__ == "__main__":
    main()
