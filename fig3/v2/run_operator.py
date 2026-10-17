"""Operator helper for Figure 3 protocol v2 (fig3/PROTOCOL_V2.md). Implements the protocol; does not change it.

Usage (repository root, PYTHONPATH=.):
  python fig3/v2/run_operator.py prepare SCENARIO_ID             subject folder + framed first message (subject_message.txt)
  python fig3/v2/run_operator.py give_dev_files SCENARIO_ID      row B before code: add the field-104 image and annotation
  python fig3/v2/run_operator.py audit SCENARIO_ID AGENT_ID      every tool call checked; conversation.md from the transcript
  python fig3/v2/run_operator.py meta SCENARIO_ID AGENT_ID NOTES meta.json from scenarios.csv, rows.csv and the transcript
  python fig3/v2/run_operator.py reject SCENARIO_ID REASON       move a failed attempt aside (never deleted)
Subject folders: SUBJECT_ROOT/vNNN (run order only, so the name reveals neither condition nor task).
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

from common.paths import REPO_ROOT

V2 = REPO_ROOT / "fig3" / "v2"
ASSETS, RUNS = V2 / "assets", V2 / "runs"
SUBJECT_ROOT = Path("/home/user/sessions_v2")
TRANSCRIPTS = Path("/root/.claude/projects/-home-user")
# The harness tells every sub-agent to use this scratchpad; it is emptied before each subject and anything a subject
# leaves there is archived with its run.
SCRATCH = Path("/tmp/claude-0/-home-user/8b3112e1-653c-5f4c-bdba-69ecd9f94f24/scratchpad")
MODEL_ALIASES = {"sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5", "haiku": "claude-haiku-5-5"}
TOOLS = {  # tools a subject may use, by the 'tools' column of rows.csv; paths are checked separately
    "web": {"ToolSearch", "WebSearch", "WebFetch"},
    "web; view attachment": {"ToolSearch", "WebSearch", "WebFetch", "Read"},
    "view attachment": {"Read"},
    "web; shell in its folder": {"ToolSearch", "WebSearch", "WebFetch", "Read", "Bash", "Write", "Edit", "Glob", "Grep",
                                 "TodoWrite"},
}
REPLY_TOOL = "SubagentHandback"   # the harness's way of delivering the subject's reply


def table(name: str) -> list[dict]:
    with (V2 / name).open(newline="") as handle:
        return list(csv.DictReader(handle))


def scenario(scenario_id: str) -> dict:
    rows = [r for r in table("scenarios.csv") if r["scenario_id"] == scenario_id]
    if len(rows) != 1:
        raise KeyError(f"{scenario_id}: {len(rows)} rows in scenarios.csv")
    return rows[0]


def row_spec(row: str) -> dict:
    return next(r for r in table("rows.csv") if r["row"] == row)


def subject_dir(sc: dict) -> Path:
    return SUBJECT_ROOT / f"v{int(sc['run_order']):03d}"


def copy_assets(spec: str, folder: Path) -> list[str]:
    """'target <- asset; ...' from scenarios.csv; returns what was copied."""
    sent = []
    for item in filter(None, (s.strip() for s in spec.split(";"))):
        target, asset = (x.strip() for x in item.split("<-"))
        if "test_" in asset and "annotation" in asset:
            raise ValueError("the test-field annotation is never given to a subject")
        shutil.copyfile(ASSETS / asset, folder / target)
        sent.append(item)
    return sent


def prepare(scenario_id: str) -> None:
    sc = scenario(scenario_id)
    folder, run_dir = subject_dir(sc), RUNS / scenario_id
    if folder.exists() or run_dir.exists():
        raise FileExistsError(f"{folder} or {run_dir} exists (a scenario is prepared once; rerun = reject first)")
    if SCRATCH.exists() and any(SCRATCH.iterdir()):
        raise RuntimeError(f"{SCRATCH} is not empty; run audit on the previous scenario first")
    folder.mkdir(parents=True)
    run_dir.mkdir(parents=True)
    sent = copy_assets(sc["folder_files"], folder)
    framing = row_spec(sc["row"])["framing"].replace("{folder}", str(folder))
    message = framing + "\n\n" + (V2 / "prompts" / f"{sc['prompt']}.txt").read_text().strip()
    (run_dir / "subject_message.txt").write_text(message + "\n")
    (run_dir / "attachments_sent.json").write_text(json.dumps({"subject_folder": str(folder), "files": sent,
                                                               "subject_agent": row_spec(sc["row"])["subject_agent"]},
                                                              indent=1))
    print(f"[agent: {row_spec(sc['row'])['subject_agent']}, cwd: {folder}]\n{message}")


def give_dev_files(scenario_id: str) -> None:
    """Answer-sheet line 'Image / annotation request', row B before any code: field-104 files into the folder."""
    sc = scenario(scenario_id)
    if sc["row"] != "code":
        raise ValueError("only row B receives the development files on request (row C labels arm has them already)")
    folder, task = subject_dir(sc), sc["task"]
    sent = copy_assets(f"annotation.tif <- dev_{task}_annotation.tif; annotation.png <- dev_{task}_annotation.png",
                       folder)
    record = json.loads((RUNS / scenario_id / "attachments_sent.json").read_text())
    record["files"] += [f"{s} (on request)" for s in sent]
    (RUNS / scenario_id / "attachments_sent.json").write_text(json.dumps(record, indent=1))
    print("added:", sent)


def transcript(agent_id: str) -> tuple[list[dict], dict]:
    hits = list(TRANSCRIPTS.glob(f"*/subagents/agent-{agent_id}.jsonl"))
    if len(hits) != 1:
        raise FileNotFoundError(f"transcript for agent {agent_id}: {len(hits)} found")
    meta = json.loads(Path(str(hits[0]).replace(".jsonl", ".meta.json")).read_text())
    return [json.loads(line) for line in hits[0].read_text().splitlines() if line.strip()], meta


def outside(path_text: str, folder: Path) -> bool:
    p = Path(path_text)
    p = (folder / p) if not p.is_absolute() else p
    return not p.resolve().is_relative_to(folder.resolve())


def shell_paths_outside(command: str, folder: Path) -> list[str]:
    """Absolute paths and parent references in a shell command that resolve outside the folder."""
    hits = []
    for token in command.replace("'", " ").replace('"', " ").replace("=", " ").split():
        if token.startswith("/") or token.startswith(".."):
            token = token.rstrip(";,)|&")
            if token.startswith(("/usr/", "/bin/", "/dev/null", "/proc/self")) or token in ("/", "/usr", "/bin"):
                continue
            if outside(token, folder):
                hits.append(token)
    return hits


def audit(scenario_id: str, agent_id: str) -> None:
    sc = scenario(scenario_id)
    folder, run_dir = subject_dir(sc), RUNS / scenario_id
    allowed = TOOLS[row_spec(sc["row"])["tools"]]
    events, _ = transcript(agent_id)
    calls, flags, notes, lines = [], [], [], [f"# {scenario_id}\n"]
    for ev in events:
        msg = ev.get("message") or {}
        role, content = msg.get("role"), msg.get("content")
        if isinstance(content, str):
            lines.append(f"## {role}\n\n{content}\n")
            continue
        for block in content or []:
            kind = block.get("type")
            if kind == "text":
                lines.append(f"## {role}\n\n{block['text']}\n")
            elif kind == "tool_use" and block["name"] == REPLY_TOOL:
                lines.append(f"## assistant (reply)\n\n{block.get('input', {}).get('message', '')}\n")
            elif kind == "tool_use":
                name, inp = block["name"], block.get("input", {})
                calls.append({"tool": name, "input": inp})
                lines.append(f"## assistant (tool call: {name})\n\n```json\n{json.dumps(inp, indent=1)[:4000]}\n```\n")
                if name not in allowed:
                    flags.append(f"tool {name} not offered for row {sc['row']}")
                for key in ("file_path", "path", "notebook_path"):
                    if isinstance(inp.get(key), str):
                        if inp[key].startswith(str(SCRATCH)):
                            notes.append(f"{name} in the harness scratchpad (archived)")
                        elif outside(inp[key], folder):
                            flags.append(f"{name} outside the subject folder: {inp[key]}")
                if name == "Bash":
                    cmd = inp.get("command", "")
                    bad = [p for p in shell_paths_outside(cmd, folder) if not p.startswith(str(SCRATCH))]
                    if bad:
                        flags.append(f"Bash refers to paths outside the subject folder {bad[:5]}: {cmd[:200]}")
                    if str(SCRATCH) in cmd:
                        notes.append("Bash in the harness scratchpad (archived)")
            elif kind == "tool_result":
                text = block.get("content")
                text = text if isinstance(text, str) else json.dumps(text)
                lines.append(f"## tool result\n\n```\n{text[:3000]}\n```\n")
    archived = []
    if SCRATCH.exists() and any(SCRATCH.iterdir()):
        target = run_dir / "subject_scratchpad"
        target.mkdir(exist_ok=True)
        for item in SCRATCH.iterdir():
            shutil.move(str(item), target / item.name)
            archived.append(item.name)
    result = {"agent_id": agent_id, "n_tool_calls": len(calls), "flags": flags,
              "scratchpad_notes": sorted(set(notes)), "scratchpad_archived": archived}
    (run_dir / "conversation.md").write_text("\n".join(lines))
    (run_dir / "tool_calls.json").write_text(json.dumps(calls, indent=1))
    (run_dir / "audit.json").write_text(json.dumps(result, indent=1))
    print(json.dumps({k: result[k] for k in ("n_tool_calls", "flags", "scratchpad_archived")}, indent=1))


def write_meta(scenario_id: str, agent_id: str, notes: str = "") -> None:
    sc = scenario(scenario_id)
    run_dir = RUNS / scenario_id
    events, agent_meta = transcript(agent_id)
    sent = [ev["message"]["content"] for ev in events
            if (ev.get("message") or {}).get("role") == "user" and isinstance(ev["message"].get("content"), str)
            and "<system-reminder>" not in ev["message"]["content"]]
    calls = json.loads((run_dir / "tool_calls.json").read_text())
    stamps = [ev["timestamp"] for ev in events if ev.get("timestamp")]
    meta = {"scenario_id": scenario_id, "row": sc["row"], "condition": sc["condition"], "task": sc["task"],
            "field": sc["field"], "replicate": int(sc["replicate"]),
            "interface": f"Claude Code sub-agent ({agent_meta.get('agentType')}), fresh per scenario",
            "model": MODEL_ALIASES.get(agent_meta.get("model"), agent_meta.get("model")), "agent_id": agent_id,
            "datetime_start": min(stamps), "datetime_end": max(stamps),
            "tools_offered": row_spec(sc["row"])["tools"],
            "web_used": [c["input"].get("query") or c["input"].get("url") for c in calls
                         if c["tool"] in ("WebSearch", "WebFetch")],
            "code_executed_by_subject": any(c["tool"] == "Bash" for c in calls),
            "attachments_sent": json.loads((run_dir / "attachments_sent.json").read_text())["files"],
            "messages_sent": sent, "follow_ups": max(0, len(sent) - 1), "notes": notes}
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print({k: meta[k] for k in ("model", "follow_ups", "code_executed_by_subject", "web_used")})


def reject(scenario_id: str, reason: str) -> None:
    sc = scenario(scenario_id)
    attic = V2 / "runs_rejected"
    n = 1 + len(list(attic.glob(f"{scenario_id}_attempt*")))
    target = attic / f"{scenario_id}_attempt{n}"
    target.parent.mkdir(exist_ok=True)
    shutil.move(str(RUNS / scenario_id), target)
    if subject_dir(sc).exists():
        shutil.move(str(subject_dir(sc)), target / "subject_folder")
    (target / "REJECTED.md").write_text(f"Attempt {n} of {scenario_id} rejected: {reason}\n")
    print("moved to", target)


if __name__ == "__main__":
    commands = {"prepare": prepare, "give_dev_files": give_dev_files, "audit": audit, "meta": write_meta,
                "reject": reject}
    if len(sys.argv) < 3 or sys.argv[1] not in commands:
        raise SystemExit(__doc__)
    commands[sys.argv[1]](*sys.argv[2:])
