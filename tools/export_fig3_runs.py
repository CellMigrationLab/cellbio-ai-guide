"""Export every Figure 3 LLM run into fig3/<section>/runs/<run_id>/ (used once while porting).

For each row of fig3/runs_index.csv it writes, with local paths scrubbed (see SCRUB):
  conversation.md  every user turn and every assistant text, in order, verbatim; tool calls listed by name + argument
  prompt.md        the first user message (the exact prompt, including our wrapper text)
  meta.json        agent id, model(s), start/end time, tool calls made, web searches/fetches, files read
and copies the run's working-folder artefacts (code as run, logs, outputs, scores). Label/intermediate TIFFs are
re-saved with lossless zlib compression (pixel values verified identical); copies of the raw input images are skipped
(they are in data/raw/).

Usage: python tools/export_fig3_runs.py SUBAGENT_DIR WORK_ROOT
"""
import csv
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np
import tifffile

REPO = Path(__file__).resolve().parent.parent
FIG3 = REPO / "fig3"
SESSION = "8b3112e1-653c-5f4c-bdba-69ecd9f94f24"
SCRUB = [  # (local prefix, placeholder) - longest first
    (f"/tmp/claude-0/-home-user-AIC-Turku-database/{SESSION}/scratchpad/", "<work2>/"),
    (f"/tmp/claude-0/-home-user/{SESSION}/scratchpad/fig3/", "<fig3-work>/"),
    (f"/tmp/claude-0/-home-user/{SESSION}/scratchpad/", "<work>/"),
    (f"/tmp/claude-0/-home-user/{SESSION}/tasks/", "<tasks>/"),
    (f"/root/.claude/uploads/{SESSION}/", "<uploads>/"),
    (f"/root/.claude/projects/-home-user/{SESSION}", "<transcript>"),
]
SKIP_NAMES = {"bf.tif", "dapi.tif", "bf_preview.png", "dapi_preview.png", "__pycache__", "bf_dev.tif", "annot_dev.tif",
              "dapi_dev.tif", "cancer_mask_dev.tif"}
TEXT_SUFFIXES = {".md", ".txt", ".py", ".ijm", ".log", ".json", ".csv", ".sh"}


def scrub(text: str) -> str:
    for local, placeholder in SCRUB:
        text = text.replace(local, placeholder)
    return text


def read_transcript(path: Path) -> tuple[list[str], dict]:
    """Return (conversation blocks, metadata) from a subagent transcript."""
    blocks, meta, seen = [], {"models": [], "tool_calls": {}, "web": [], "files_read": []}, set()
    for line in path.open():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("uuid") in seen:
            continue
        seen.add(event.get("uuid"))
        message = event.get("message") or {}
        content, stamp = message.get("content"), event.get("timestamp", "")
        if event.get("type") == "user":
            texts = [content] if isinstance(content, str) else [c.get("text", "") for c in content or []
                                                                if isinstance(c, dict) and c.get("type") == "text"]
            for text in texts:
                if not text.strip():
                    continue
                if text.lstrip().startswith("<system-reminder>"):  # injected by the agent harness, not by us
                    blocks.append(f"## HARNESS NOTE ({stamp})\n\n{text}")
                    continue
                meta.setdefault("start", stamp)
                blocks.append(f"## USER ({stamp})\n\n{text}")
        elif event.get("type") == "assistant":
            meta["end"] = stamp
            if message.get("model") and message["model"] not in meta["models"]:
                meta["models"].append(message["model"])
            for part in content or []:
                if part.get("type") == "text" and part["text"].strip():
                    blocks.append(f"## ASSISTANT ({stamp})\n\n{part['text']}")
                elif part.get("type") == "tool_use":
                    name, args = part.get("name", ""), part.get("input", {})
                    meta["tool_calls"][name] = meta["tool_calls"].get(name, 0) + 1
                    if "andback" in name:
                        blocks.append("## ASSISTANT (final report)\n\n" + "\n".join(str(v) for v in args.values()))
                        continue
                    arg = args.get("query") or args.get("url") or args.get("file_path") or args.get("command", "")[:300]
                    if name in ("WebSearch", "WebFetch"):
                        meta["web"].append(arg)
                    if name == "Read":
                        meta["files_read"].append(arg)
                    blocks.append(f"*[tool call: {name}: {arg}]*")
    return blocks, meta


def copy_artifacts(src: Path, dst: Path) -> list[str]:
    """Copy a run's working folder (minus raw-input copies); compress TIFFs losslessly; scrub text files."""
    copied = []
    for item in sorted(src.rglob("*")):
        rel = item.relative_to(src)
        if item.is_dir() or any(part in SKIP_NAMES for part in rel.parts):
            continue
        target = dst / "artifacts" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if item.suffix.lower() in (".tif", ".tiff"):
            data = tifffile.imread(item)
            tifffile.imwrite(target, data, compression="zlib")
            if not np.array_equal(tifffile.imread(target), data):
                raise RuntimeError(f"Lossless re-save changed pixel values: {item}")
        elif item.suffix.lower() in TEXT_SUFFIXES:
            target.write_text(scrub(item.read_text(errors="replace")))
        else:
            shutil.copy2(item, target)
        copied.append(str(rel))
    return copied


def main(subagent_dir: str, work_root: str) -> None:
    rows = list(csv.DictReader(open(FIG3 / "runs_index.csv")))
    for row in rows:
        transcript = Path(subagent_dir) / f"agent-{row['agent_id']}.jsonl"
        if not transcript.is_file():
            raise FileNotFoundError(f"Transcript missing for {row['run_id']}: {transcript}")
        out = FIG3 / row["section"] / "runs" / row["run_id"]
        out.mkdir(parents=True, exist_ok=True)
        blocks, meta = read_transcript(transcript)
        (out / "conversation.md").write_text(scrub(f"# {row['run_id']}\n\n" + "\n\n".join(blocks)) + "\n")
        first_user = next((b for b in blocks if b.startswith("## USER")), "")
        (out / "prompt.md").write_text(scrub(first_user.split("\n\n", 1)[-1]) + "\n")
        meta.update({k: row[k] for k in ("agent_id", "description", "section", "status", "note")})
        meta["workdir"] = row["workdir"]
        if row["workdir"]:
            src = Path(work_root) / row["workdir"]
            if not src.is_dir():
                raise FileNotFoundError(f"Working folder missing for {row['run_id']}: {src}")
            if row["section"] != "direct_answers":  # draw folders are shared by runs; exported separately
                meta["artifacts"] = copy_artifacts(src, out)
        (out / "meta.json").write_text(scrub(json.dumps(meta, indent=1)))
        print(f"{row['section']:15s} {row['run_id']:45s} turns={sum(b.startswith('## USER') for b in blocks)}"
              f" web={len(meta['web'])} artifacts={len(meta.get('artifacts', []))}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
