"""Operator helper for Figure 3 round 2 (Claude side): prepares subject folders, frames prompts, audits subject
transcripts and runs final code on the test field. It implements OPERATOR.md; it does not change the protocol.

Usage (from the repository root, PYTHONPATH=.):
  python fig3/round2/run_operator.py prepare <scenario_id>          # subject folder + framed message (subject_message.txt)
  python fig3/round2/run_operator.py audit <scenario_id> <agent_id> # tool-call audit + conversation.md from the transcript
  python fig3/round2/run_operator.py meta <scenario_id> <agent_id> [notes]    # meta.json from the transcript
  python fig3/round2/run_operator.py run <scenario_id>              # run code_run.py / code_run.ijm / pipeline on field 209

Subject folders live outside the repository under SUBJECT_ROOT and are named by run order only (s001, s002, ...), so the
folder name reveals neither the condition nor the task. Test runs happen in EXEC_ROOT.
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

from common.paths import REPO_ROOT

ROUND2 = REPO_ROOT / "fig3" / "round2"
ASSETS = ROUND2 / "assets"
RUNS = ROUND2 / "runs"
SUBJECT_ROOT = Path("/home/user/sessions")
EXEC_ROOT = Path("/home/user/r2exec")
TRANSCRIPTS = Path("/root/.claude/projects/-home-user")
FIJI = Path("/home/user/tools/Fiji/fiji-linux-x64")
TIMEOUT_S = 3600
SUBJECT_TOOLS_ALLOWED = {"advice": {"ToolSearch", "WebSearch", "WebFetch"},
                         "direct": {"ToolSearch", "WebSearch", "WebFetch", "Read"},
                         "code_python": {"ToolSearch", "WebSearch", "WebFetch", "Read"},
                         "code_fiji": {"ToolSearch", "WebSearch", "WebFetch", "Read"}}  # optimise: shell in its folder


def scenario(scenario_id: str) -> dict:
    with (ROUND2 / "scenarios.csv").open(newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["scenario_id"] == scenario_id]
    if len(rows) != 1:
        raise KeyError(f"{scenario_id}: {len(rows)} rows in scenarios.csv")
    return rows[0]


def subject_dir(sc: dict) -> Path:
    return SUBJECT_ROOT / f"s{int(sc['run_order']):03d}"


def framing(sc: dict, folder: Path) -> str:
    """OPERATOR.md section 6, filled from subject_tools."""
    parts = []
    tools = sc["subject_tools"]
    if "web" in tools:
        parts.append("Tools: web search is available (WebSearch and WebFetch; load them with ToolSearch if they are not listed).")
    if sc["row"] in ("code_python", "code_fiji"):
        parts.append(f"The user attached a file, which you can view: {folder / 'image.png'}.")
    elif sc["row"] == "direct":
        parts.append(f"The user attached a file, which you can view: {folder / 'image.png'}.")
    elif sc["row"] == "optimise":
        parts.append(f"You can run shell commands in the folder {folder} only.")
    return "You are an AI assistant chatting with a user. " + " ".join(parts) + " Reply to the user as you normally would."


def prepare(scenario_id: str) -> None:
    sc = scenario(scenario_id)
    folder, run_dir = subject_dir(sc), RUNS / scenario_id
    if folder.exists() or run_dir.exists():
        raise FileExistsError(f"{folder} or {run_dir} exists; a scenario is prepared once (rerun: new run folder)")
    folder.mkdir(parents=True)
    run_dir.mkdir(parents=True)
    task, row = sc["task"], sc["row"]
    sent = []
    if row in ("code_python", "code_fiji"):
        # image.tif is the user's file; the TIFF cannot be displayed to the subject, so the PNG preview is the
        # viewable attachment (OPERATOR.md section 3 fallback; recorded in deviations.md)
        shutil.copyfile(ASSETS / f"dev_{task}_image.tif", folder / "image.tif")
        shutil.copyfile(ASSETS / f"dev_{task}_image.png", folder / "image.png")
        sent = [f"image.tif <- dev_{task}_image.tif", f"image.png <- dev_{task}_image.png (viewable preview)"]
    elif row == "direct":
        shutil.copyfile(ASSETS / f"test_{task}_image.png", folder / "image.png")
        sent = [f"image.png <- test_{task}_image.png"]
    elif row == "optimise":
        shutil.copyfile(ASSETS / f"dev_{task}_image.tif", folder / "image.tif")
        sent = [f"image.tif <- dev_{task}_image.tif"]
        if sc["condition"] == "box1":
            shutil.copyfile(ASSETS / f"dev_{task}_annotation.tif", folder / "annotation.tif")
            sent.append(f"annotation.tif <- dev_{task}_annotation.tif")
    message = framing(sc, folder) + "\n\n" + (ROUND2 / sc["prompt_file"]).read_text().strip()
    (run_dir / "subject_message.txt").write_text(message + "\n")
    (run_dir / "attachments_sent.json").write_text(json.dumps({"subject_folder": str(folder), "files": sent}, indent=1))
    print(message)


def transcript(agent_id: str) -> list[dict]:
    hits = list(TRANSCRIPTS.glob(f"*/subagents/agent-{agent_id}.jsonl"))
    if len(hits) != 1:
        raise FileNotFoundError(f"transcript for agent {agent_id}: {len(hits)} found")
    return [json.loads(line) for line in hits[0].read_text().splitlines() if line.strip()]


def paths_in(tool_input: dict) -> list[str]:
    out = []
    for key in ("file_path", "path", "notebook_path"):
        if isinstance(tool_input.get(key), str):
            out.append(tool_input[key])
    return out


def audit(scenario_id: str, agent_id: str) -> None:
    """Every tool call of the subject, checked against the row's allowed tools and its folder."""
    sc = scenario(scenario_id)
    folder, run_dir = str(subject_dir(sc)), RUNS / scenario_id
    events = transcript(agent_id)
    calls, flags, lines = [], [], [f"# {scenario_id}\n"]
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
            elif kind == "tool_use" and block["name"] == "SubagentHandback":   # the subject's reply to the user
                lines.append(f"## assistant (reply)\n\n{block.get('input', {}).get('message', '')}\n")
            elif kind == "tool_use":
                name, inp = block["name"], block.get("input", {})
                calls.append({"tool": name, "input": inp})
                lines.append(f"## {role} (tool call: {name})\n\n```json\n{json.dumps(inp, indent=1)[:4000]}\n```\n")
                allowed = SUBJECT_TOOLS_ALLOWED.get(sc["row"])
                if allowed is not None and name not in allowed:
                    flags.append(f"tool {name} not offered for row {sc['row']}")
                for p in paths_in(inp):
                    if not p.startswith(folder):
                        flags.append(f"{name} outside the subject folder: {p}")
                if name == "Bash" and "cellbio" in json.dumps(inp):
                    flags.append(f"Bash command mentions the repository: {inp.get('command', '')[:200]}")
                if name == "Bash" and sc["row"] == "optimise" and folder not in json.dumps(inp) and "cd " not in inp.get("command", ""):
                    flags.append(f"Bash command without the subject folder (check): {inp.get('command', '')[:200]}")
            elif kind == "tool_result":
                text = block.get("content")
                text = text if isinstance(text, str) else json.dumps(text)[:2000]
                lines.append(f"## tool result\n\n```\n{text[:2000]}\n```\n")
    (run_dir / "conversation.md").write_text("\n".join(lines))
    (run_dir / "tool_calls.json").write_text(json.dumps(calls, indent=1))
    (run_dir / "audit.json").write_text(json.dumps({"agent_id": agent_id, "n_tool_calls": len(calls), "flags": flags},
                                                   indent=1))
    print(json.dumps({"n_tool_calls": len(calls), "flags": flags}, indent=1))


MODEL_ALIASES = {"sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5", "haiku": "claude-haiku-5-5"}


def write_meta(scenario_id: str, agent_id: str, notes: str = "") -> None:
    """meta.json (OPERATOR.md section 5) filled from scenarios.csv and the subject transcript, not by hand."""
    sc = scenario(scenario_id)
    run_dir = RUNS / scenario_id
    events = transcript(agent_id)
    agent_meta = json.loads(next(TRANSCRIPTS.glob(f"*/subagents/agent-{agent_id}.meta.json")).read_text())
    user_texts = []
    for ev in events:
        msg = ev.get("message") or {}
        if msg.get("role") == "user" and isinstance(msg.get("content"), str) and "<system-reminder>" not in msg["content"]:
            user_texts.append(msg["content"])
    calls = json.loads((run_dir / "tool_calls.json").read_text())
    web_used = [c["input"].get("query") or c["input"].get("url") for c in calls if c["tool"] in ("WebSearch", "WebFetch")]
    stamps = [ev["timestamp"] for ev in events if ev.get("timestamp")]
    meta = {"scenario_id": scenario_id, "assistant": sc["assistant"], "row": sc["row"], "condition": sc["condition"],
            "task": sc["task"], "replicate": int(sc["replicate"]),
            "interface": "Claude Code sub-agent (general-purpose), fresh per scenario, framing OPERATOR.md section 6",
            "model": MODEL_ALIASES.get(agent_meta.get("model"), agent_meta.get("model")), "agent_id": agent_id,
            "datetime_start": min(stamps), "datetime_end": max(stamps),
            "web_available": "web" in sc["subject_tools"], "web_used": web_used, "app_executed_code": False,
            "attachments_sent": json.loads((run_dir / "attachments_sent.json").read_text())["files"],
            "messages_sent": user_texts, "follow_ups": max(0, len(user_texts) - 1),
            "packages_installed": [], "notes": notes}
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print({k: meta[k] for k in ("model", "follow_ups", "web_used", "datetime_start")})


def run(scenario_id: str) -> None:
    """Run the final code (code_run.py / code_run.ijm, or the agent's pipeline) on a copy of the test image."""
    sc = scenario(scenario_id)
    run_dir, exec_dir = RUNS / scenario_id, EXEC_ROOT / scenario_id
    if exec_dir.exists():
        raise FileExistsError(f"{exec_dir} exists")
    exec_dir.mkdir(parents=True)
    shutil.copyfile(ASSETS / f"test_{sc['task']}_image.tif", exec_dir / "image.tif")
    if sc["row"] == "code_fiji":
        shutil.copyfile(run_dir / "code_run.ijm", exec_dir / "code_run.ijm")
        cmd = ["xvfb-run", "-a", str(FIJI), "--headless", "-batch", "code_run.ijm"]
    elif sc["row"] == "code_python":
        shutil.copyfile(run_dir / "code_run.py", exec_dir / "code_run.py")
        cmd = [sys.executable, "code_run.py"]
    elif sc["row"] == "optimise":
        # run inside a copy of the agent's folder (its pipeline may read files it saved there); the test image and the
        # output sit one level up. Generic runs: pipeline_run.py = pipeline.py with only paths changed (EDITS.md).
        shutil.copytree(run_dir / "agent_folder", exec_dir / "agent_folder")
        script = run_dir / "pipeline_run.py" if (run_dir / "pipeline_run.py").exists() else run_dir / "agent_folder" / "pipeline.py"
        shutil.copyfile(script, exec_dir / "agent_folder" / "pipeline_run.py")
        cmd = [sys.executable, "pipeline_run.py", str(exec_dir / "image.tif"), str(exec_dir / "labels.tif")]
        exec_dir = exec_dir / "agent_folder"
    else:
        raise ValueError(f"row {sc['row']} has no code to run")
    try:
        proc = subprocess.run(cmd, cwd=exec_dir, capture_output=True, text=True, timeout=TIMEOUT_S)
        log = f"$ {' '.join(cmd)}\nexit {proc.returncode}\n--- stdout\n{proc.stdout}\n--- stderr\n{proc.stderr}"
    except subprocess.TimeoutExpired:
        log = f"$ {' '.join(cmd)}\nTIMEOUT after {TIMEOUT_S} s"
    (run_dir / "run.log").write_text(log)
    out = EXEC_ROOT / scenario_id / "labels.tif"
    if out.exists():
        shutil.copyfile(out, run_dir / "labels.tif")
    print(log[-1500:])


if __name__ == "__main__":
    commands = {"prepare": prepare, "audit": audit, "meta": write_meta, "run": run}
    if len(sys.argv) < 3 or sys.argv[1] not in commands:
        raise SystemExit(__doc__)
    commands[sys.argv[1]](*sys.argv[2:])
