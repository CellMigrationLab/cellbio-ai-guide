"""Recover inline commands (shell heredocs run during the original work) that wrote a given output file.

Some source-data files were produced by one-off inline Python run from the shell and never saved as a script.
This tool searches the original session transcripts for every shell command that writes the target file name and
saves the LAST such command verbatim (the one whose output is in the repository), with its timestamp.

Usage: python tools/recover_inline.py OUT_DIR TRANSCRIPT.jsonl [TRANSCRIPT ...] -- TARGET [TARGET ...]
"""
import json
import re
import sys
from pathlib import Path

WRITE_HINT = re.compile(r"(\.save\(|imwrite\(|json\.dump\(|open\([^)]*['\"]w['\"]|savefig\(|>\s*\S)")


def commands(transcripts: list[str]):
    """Yield (timestamp, command text) for every shell tool call in the transcripts, in order."""
    for transcript in transcripts:
        for line in open(transcript):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") != "assistant":
                continue
            for part in (event.get("message") or {}).get("content") or []:
                if isinstance(part, dict) and part.get("type") == "tool_use" and part.get("name") == "Bash":
                    yield event.get("timestamp", ""), part.get("input", {}).get("command", "")


def main(argv: list[str]) -> None:
    if "--" not in argv or len(argv) < 5:
        raise SystemExit(__doc__)
    split = argv.index("--")
    out_dir, transcripts, targets = Path(argv[1]), argv[2:split], argv[split + 1:]
    out_dir.mkdir(parents=True, exist_ok=True)
    found = {t: None for t in targets}
    for stamp, cmd in commands(transcripts):
        for target in targets:
            if target in cmd and any(target in seg and WRITE_HINT.search(seg) for seg in cmd.splitlines()):
                found[target] = (stamp, cmd)
    for target, hit in found.items():
        if hit is None:
            print(f"{target}: NOT FOUND")
            continue
        stamp, cmd = hit
        name = re.sub(r"[^A-Za-z0-9_.-]", "_", target) + ".sh"
        (out_dir / name).write_text(f"# Recovered verbatim from the session transcript ({stamp}).\n"
                                    f"# Last shell command that wrote {target}. Paths are those of the original working folder.\n{cmd}\n")
        print(f"{target}: recovered ({stamp}) -> {name}")


if __name__ == "__main__":
    main(sys.argv)
