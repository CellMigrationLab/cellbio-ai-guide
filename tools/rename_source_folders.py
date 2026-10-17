"""Rename the source-data folders of Figs 1-3 to descriptive names and update the scripts that read them (used once; already applied, do not run again).

Record-only files (code/recovered_inline/, superseded/) keep their original paths; the README of each figure lists the
mapping. Usage: python tools/rename_source_folders.py
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RENAMES = {  # figure folder -> {old source_data subfolder: new name}
    "fig1": {"data": "panel_b", "data4": "panel_c_step3", "data5": "panel_a", "data8": "panel_c_steps2_4",
             "data9": "panel_c_step5", "full_field": "full_field_labels"},
    "fig2": {"data": "panels", "data4": "from_fig1_panel_c", "data5": "from_fig1_panel_a"},
    "fig3/figure": {"bf3": "round1"},
}
EXTRA_FILES = ["tools/check_all.py", "fig3/scoring/build_scores.py", "fig2/README.md", "fig1/README.md", "fig3/README.md",
               "AGENTS.md", "data/README.md"]


def rewrite(path: Path, mapping: dict, prefix: str = "") -> bool:
    """Replace quoted path prefixes old/ -> new/ (optionally after a folder prefix); return True if the file changed."""
    text = path.read_text()
    new = text
    for old, name in sorted(mapping.items(), key=lambda kv: -len(kv[0])):  # longest first: "data4" before "data"
        new = re.sub(rf"(?<![A-Za-z0-9_]){re.escape(prefix + old)}/", f"{prefix}{name}/", new)
    if new != text:
        path.write_text(new)
    return new != text


def main() -> None:
    for fig, mapping in RENAMES.items():
        src = REPO / fig / "source_data"
        for old, name in mapping.items():
            if not (src / old).is_dir():
                raise FileNotFoundError(src / old)
            (src / old).rename(src / name)
        code_files = [p for p in (REPO / fig / "code").rglob("*.py") if "recovered_inline" not in p.parts]
        changed = [p for p in code_files if rewrite(p, mapping)]
        print(fig, "scripts updated:", [str(p.relative_to(REPO)) for p in changed])
    cross = {"fig1/source_data/" + k: "fig1/source_data/" + v for k, v in RENAMES["fig1"].items()}
    cross |= {"fig2/source_data/" + k: "fig2/source_data/" + v for k, v in RENAMES["fig2"].items()}
    cross |= {"figure/source_data/bf3": "figure/source_data/round1", "source_data\" / \"bf3\"": "source_data\" / \"round1\""}
    files = EXTRA_FILES + [str(p.relative_to(REPO)) for p in (REPO / "fig2" / "code").rglob("*.py") if "recovered_inline" not in p.parts]
    for name in files:
        path = REPO / name
        text = path.read_text()
        new = text
        for old, rep in sorted(cross.items(), key=lambda kv: -len(kv[0])):  # longest first
            new = new.replace(old, rep)
        if new != text:
            path.write_text(new)
            print("updated", name)


if __name__ == "__main__":
    main()
