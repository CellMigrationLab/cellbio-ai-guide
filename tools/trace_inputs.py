"""Run a Python script and record every existing file it opens for reading.

Used once, while porting the working folders into this repository, to list the exact inputs of each
figure builder and scoring script (so nothing is copied by guesswork and nothing is missed).

Usage:  python tools/trace_inputs.py OUTPUT.json SCRIPT.py [ARGS...]
The script runs in the current working directory, exactly as it would without tracing.
"""
import json
import os
import runpy
import sys
import sysconfig

EXCLUDED_PREFIXES = tuple(
    p for p in {sysconfig.get_paths()[k] for k in ("stdlib", "platstdlib", "purelib", "platlib")} | {sys.prefix}
)


def _is_data_file(path: str) -> bool:
    """True for regular files outside the Python installation and site-packages."""
    absolute = os.path.abspath(path)
    return os.path.isfile(absolute) and not absolute.startswith(EXCLUDED_PREFIXES) and "/site-packages/" not in absolute


def main(argv: list[str]) -> None:
    if len(argv) < 3:
        raise SystemExit(__doc__)
    output, script, args = argv[1], argv[2], argv[3:]
    opened: set[str] = set()
    script_abs = os.path.abspath(script)

    def hook(event: str, event_args: tuple) -> None:
        if event != "open" or not isinstance(event_args[0], (str, bytes, os.PathLike)):
            return
        path = os.fsdecode(event_args[0])
        mode = event_args[1] if len(event_args) > 1 and isinstance(event_args[1], str) else "r"
        if "r" in mode and "+" not in mode and _is_data_file(path) and os.path.abspath(path) != script_abs:
            opened.add(os.path.abspath(path))

    sys.addaudithook(hook)
    sys.argv = [script] + args
    sys.path.insert(0, os.path.dirname(script_abs))  # as `python SCRIPT.py` would
    try:
        runpy.run_path(script, run_name="__main__")
    finally:
        with open(output, "w") as handle:
            json.dump(sorted(opened), handle, indent=1)


if __name__ == "__main__":
    main(sys.argv)
