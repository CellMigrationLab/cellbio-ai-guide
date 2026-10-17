"""Operator helper for Figure 3 protocol v2 (fig3/PROTOCOL_V2.md). Implements the protocol; does not change it.

Usage (repository root, PYTHONPATH=., V2_STAGE=preflight|main, SUBJECT_SCRATCHPAD=<operator scratchpad>):
  python fig3/v2/run_operator.py status                          complete / partial / next scenario (resuming)
  python fig3/v2/run_operator.py prepare SCENARIO_ID             subject folder + framed first message (subject_message.txt)
  python fig3/v2/run_operator.py start SCENARIO_ID               fresh headless subject session, first message
  python fig3/v2/run_operator.py answer SCENARIO_ID TEXT         reply to a follow-up question (answer sheet, verbatim)
  python fig3/v2/run_operator.py turn SCENARIO_ID N              row D: send the prescribed turn N (2 or 3)
  python fig3/v2/run_operator.py give_dev_files SCENARIO_ID      row B before code: add the field-104 image and annotation
  python fig3/v2/run_operator.py audit SCENARIO_ID               every tool call checked; conversation.md from the transcript
  python fig3/v2/run_operator.py meta SCENARIO_ID NOTES          meta.json from scenarios.csv, rows.csv and the transcript
  python fig3/v2/run_operator.py collect SCENARIO_ID             code_as_returned.py / agent_folder/ / direct_answers.json
  python fig3/v2/run_operator.py reject SCENARIO_ID REASON       move a failed attempt aside (never deleted)

Subjects are headless Claude Code sessions (`claude -p --restricted`, model claude-sonnet-5-5), each started in its own folder
SUBJECT_ROOT/vNNN (run order only, so the name reveals neither condition nor task) with a fresh session ID and only
the tools in the cli_tools column of rows.csv. A sub-agent cannot be used: it inherits the operator session's project
instructions (AGENTS.md) and working directory (the repository).
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import uuid
from pathlib import Path

from common.paths import REPO_ROOT

V2 = REPO_ROOT / "fig3" / "v2"
ASSETS = V2 / "assets"
STAGES = {  # stage: (runs folder, rejected-attempts folder, subject folders)
    "preflight": ("runs_preflight", "runs_preflight_rejected", Path("/home/user/sessions_v2_preflight")),
    "main": ("runs", "runs_rejected", Path("/home/user/sessions_v2")),
}
TRANSCRIPTS = Path("/root/.claude/projects")      # <folder slug>/<session id>.jsonl
SUBJECT_TMP = Path("/tmp/claude-0")               # <folder slug>/<session id>/scratchpad (the subject's own)
MODEL = "claude-sonnet-5-5"                       # full model ID (not an alias), for reproducibility
FREEZE = V2 / "FREEZE.json"
CLI_TIMEOUT_S = {"optimise": 6 * 3600}            # per subject turn; chat rows below
CHAT_TIMEOUT_S = 1800
MAX_ANSWERS = 3
CLOSING = "Thanks, that is all I need."
# variables of the operator session that a subject must not inherit (session identity, extra directories, messaging
# to the operator, synced skills/plugins, effort setting); everything else (proxy, credentials) is kept
STRIP_ENV = ("CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_USER_EMAIL", "CLAUDE_ADDITIONAL_DIRECTORIES",
             "CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD", "CLAUDE_CODE_SYNC_SESSION_REFS",
             "CLAUDE_CODE_MESSAGING_SOCKET", "CLAUDE_CODE_MESSAGING_TOKEN", "CLAUDE_CODE_SYNC_SKILLS",
             "CLAUDE_CODE_SYNC_PLUGINS", "DOCUMENTS_MCP_SCRATCH_ROOT", "CLAUDE_EFFORT", "PYTHONPATH")
# text that would show a subject looking for the study, its authors or this repository (any tool input)
FORBIDDEN_TERMS = ("cellbio-ai-guide", "cellmigrationlab", "jacquemet", "henriques", "mariscal",
                   "cell biologist's guide", "ai-assisted image analysis", "data/raw", "protocol_v2")


def stage() -> tuple[Path, Path, Path]:
    value = os.environ.get("V2_STAGE")
    if value not in STAGES:
        raise RuntimeError(f"set V2_STAGE to one of {sorted(STAGES)}")
    runs, rejected, root = STAGES[value]
    return V2 / runs, V2 / rejected, root


def scratchpad() -> Path:
    """The operator session's scratchpad (set SUBJECT_SCRATCHPAD to the path given in the session's system prompt).

    Subjects have their own scratchpad (archived by audit); the operator's must stay empty and untouched by subjects.
    No default: a wrong path would hide what subjects wrote."""
    value = os.environ.get("SUBJECT_SCRATCHPAD")
    if not value:
        raise RuntimeError("set SUBJECT_SCRATCHPAD to this session's scratchpad directory")
    return Path(value)


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


def run_dir_of(scenario_id: str) -> Path:
    return stage()[0] / scenario_id


def subject_dir(sc: dict) -> Path:
    return stage()[2] / f"v{int(sc['run_order']):03d}"


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
    folder, run_dir = subject_dir(sc), run_dir_of(scenario_id)
    if folder.exists() or run_dir.exists():
        raise FileExistsError(f"{folder} or {run_dir} exists (a scenario is prepared once; rerun = reject first)")
    scratch = scratchpad()
    if scratch.exists() and any(scratch.iterdir()):
        raise RuntimeError(f"{scratch} is not empty; run audit on the previous scenario first")
    folder.mkdir(parents=True)
    run_dir.mkdir(parents=True)
    sent = copy_assets(sc["folder_files"], folder)
    spec = row_spec(sc["row"])
    framing = spec["framing"].replace("{folder}", str(folder))
    message = framing + "\n\n" + (V2 / "prompts" / f"{sc['prompt']}.txt").read_text().strip()
    (run_dir / "subject_message.txt").write_text(message + "\n")
    (run_dir / "attachments_sent.json").write_text(json.dumps({"subject_folder": str(folder), "files": sent,
                                                               "cli_tools": spec["cli_tools"]}, indent=1))
    print(f"[tools: {spec['cli_tools']}, cwd: {folder}]\n{message}")


# ---------------------------------------------------------------- the subject session
def subject_env() -> dict:
    return {k: v for k, v in os.environ.items() if k not in STRIP_ENV}


def cli_command(tools: str, session: str, resume: bool, message: str) -> list[str]:
    return ["claude", "-p", "--restricted", "--strict-mcp-config", "--disable-slash-commands", "--model", MODEL,
            "--tools", tools, "--allowedTools", tools, "--permission-mode", "acceptEdits", "--output-format", "json",
            "--resume" if resume else "--session-id", session, message]


def turns(run_dir: Path) -> list[dict]:
    path = run_dir / "turns.json"
    return json.loads(path.read_text()) if path.is_file() else []


def send(scenario_id: str, message: str, kind: str) -> None:
    """One subject turn: kind = first | answer | turn (row D prescribed turn). Recorded in turns.json."""
    sc, run_dir = scenario(scenario_id), run_dir_of(scenario_id)
    folder, history = subject_dir(sc), turns(run_dir)
    if (kind == "first") != (not history):
        raise RuntimeError("start sends the first message once; later messages need a started session")
    session_file = run_dir / "session.json"
    if kind == "first":
        session = str(uuid.uuid4())
        version = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
        if FREEZE.is_file() and version != json.loads(FREEZE.read_text())["cli_version"]:
            print(f"WARNING: Claude Code CLI {version!r} differs from the frozen one; record a deviation for this run")
        session_file.write_text(json.dumps({"session_id": session, "cli_version": version, "model_requested": MODEL,
                                            "cli_tools": row_spec(sc["row"])["cli_tools"],
                                            "env_stripped": list(STRIP_ENV)}, indent=1))
    session = json.loads(session_file.read_text())["session_id"]
    cmd = cli_command(row_spec(sc["row"])["cli_tools"], session, kind != "first", message)
    timeout = CLI_TIMEOUT_S.get(sc["row"], CHAT_TIMEOUT_S)
    proc = subprocess.run(cmd, cwd=folder, env=subject_env(), capture_output=True, text=True, timeout=timeout)
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        result = {"is_error": True, "result": None, "raw_stdout": proc.stdout[-4000:]}
    keep = ("is_error", "subtype", "duration_ms", "num_turns", "total_cost_usd", "usage", "modelUsage",
            "permission_denials", "session_id")
    history.append({"kind": kind, "sent": message, "reply": result.get("result"), "exit_code": proc.returncode,
                    "stderr": proc.stderr[-4000:], **{k: result.get(k) for k in keep if k in result}})
    (run_dir / "turns.json").write_text(json.dumps(history, indent=1, ensure_ascii=False))
    if result.get("session_id") not in (None, session):
        raise RuntimeError(f"the CLI answered from session {result.get('session_id')}, expected {session}")
    print(f"[exit {proc.returncode}, error {result.get('is_error')}, denials {result.get('permission_denials')}]")
    print(result.get("result"))


def start(scenario_id: str) -> None:
    send(scenario_id, (run_dir_of(scenario_id) / "subject_message.txt").read_text().strip(), "first")


def answer(scenario_id: str, text: str) -> None:
    """Follow-up reply, verbatim from the answer sheet; at most 3, then only the closing line."""
    given = sum(t["kind"] == "answer" and t["sent"] != CLOSING for t in turns(run_dir_of(scenario_id)))
    if given >= MAX_ANSWERS and text != CLOSING:
        raise RuntimeError(f"{MAX_ANSWERS} replies given; only {CLOSING!r} may follow")
    if text != CLOSING and not from_answer_sheet(text):
        raise ValueError("not a combination of answer-sheet sentences, verbatim (answer_sheet.md)")
    send(scenario_id, text, "answer")


def from_answer_sheet(text: str) -> bool:
    """True if the text is one or more quoted answer-sheet sentences, verbatim, separated by spaces."""
    lines = sorted(set(re.findall(r'"([^"]+)"', (V2 / "answer_sheet.md").read_text())), key=len, reverse=True)
    rest = text.strip()
    while rest:
        hit = next((line for line in lines if rest.startswith(line)), None)
        if hit is None:
            return False
        rest = rest[len(hit):].strip()
    return True


def turn(scenario_id: str, n: str) -> None:
    sc = scenario(scenario_id)
    if sc["row"] != "direct" or n not in ("2", "3"):
        raise ValueError("prescribed turns 2 and 3 exist for row D only")
    done = [t for t in turns(run_dir_of(scenario_id)) if t["kind"] == "turn"]
    if len(done) != int(n) - 2:
        raise RuntimeError(f"turn {n} out of order ({len(done)} prescribed turns sent)")
    send(scenario_id, (V2 / "prompts" / f"direct_turn{n}_{sc['task']}.txt").read_text().strip(), "turn")


def code_given(history: list[dict]) -> bool:
    return any(python_blocks(t.get("reply") or "") for t in history)


def give_dev_files(scenario_id: str) -> None:
    """Answer-sheet line 'Image / annotation request', row B before any code: field-104 files into the folder."""
    sc = scenario(scenario_id)
    if sc["row"] != "code":
        raise ValueError("only row B receives the development files on request (row C labels arm has them already)")
    run_dir = run_dir_of(scenario_id)
    if code_given(turns(run_dir)):
        raise RuntimeError("the subject has already given code: the answer is \"I don't know.\"")
    folder, task = subject_dir(sc), sc["task"]
    sent = copy_assets(f"annotation.tif <- dev_{task}_annotation.tif; annotation.png <- dev_{task}_annotation.png",
                       folder)
    record = json.loads((run_dir / "attachments_sent.json").read_text())
    record["files"] += [f"{s} (on request)" for s in sent]
    (run_dir / "attachments_sent.json").write_text(json.dumps(record, indent=1))
    print("added:", sent)


# ---------------------------------------------------------------- audit and records
def session_id(run_dir: Path) -> str:
    return json.loads((run_dir / "session.json").read_text())["session_id"]


def transcript_path(session: str) -> Path:
    hits = list(TRANSCRIPTS.glob(f"*/{session}.jsonl"))
    if len(hits) != 1:
        raise FileNotFoundError(f"transcript for session {session}: {len(hits)} found")
    return hits[0]


def transcript(session: str) -> list[dict]:
    return [json.loads(line) for line in transcript_path(session).read_text().splitlines() if line.strip()]


def subject_tmp(session: str) -> Path:
    """The session's own temporary folder (scratchpad, background-task output): same folder slug as its transcript."""
    return SUBJECT_TMP / transcript_path(session).parent.name / session


def strip_images(value):
    """Image payloads (base64) replaced by their SHA-256 and size; everything else unchanged."""
    if isinstance(value, dict):
        if value.get("type") == "base64" and isinstance(value.get("data"), str):
            raw = value["data"].encode()
            return {**value, "data": None, "sha256_of_base64": hashlib.sha256(raw).hexdigest(), "base64_chars": len(raw)}
        return {k: strip_images(v) for k, v in value.items()}
    if isinstance(value, list):
        return [strip_images(v) for v in value]
    return value


def store_transcript(source: Path, target: Path) -> None:
    """The session transcript kept with the run: every event, gzip-compressed, image payloads replaced by hashes."""
    events = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    with gzip.open(target, "wt", encoding="utf-8") as handle:
        for ev in events:
            handle.write(json.dumps(strip_images(ev), ensure_ascii=False) + "\n")


def outside(path_text: str, folder: Path) -> bool:
    p = Path(path_text)
    p = (folder / p) if not p.is_absolute() else p
    return not p.resolve().is_relative_to(folder.resolve())


# installed software and the shared model cache: outside the folder but part of the environment, not forbidden material
# (noted in audit.json, not flagged); everything else outside the folder is flagged
ENVIRONMENT_PATHS = ("/usr/", "/bin/", "/lib/", "/opt/", "/etc/", "/proc/", "/dev/null", "/root/.cellpose",
                     "/root/.cache/pip", "/root/.local/lib")


def shell_paths_outside(command: str, folder: Path) -> list[str]:
    """Absolute, home (~) and parent (..) paths in a shell command that resolve outside the folder."""
    hits = []
    for token in command.replace("'", " ").replace('"', " ").replace("=", " ").replace(":", " ").split():
        if token.startswith(("/", "..", "~")):
            token = token.rstrip(";,)|&")
            if token.startswith("~"):
                token = str(Path.home()) + token[1:]
            if token.startswith("/") and (len(Path(token).parts) < 2 or not Path("/", Path(token).parts[1]).exists()):
                continue      # a bare '/' or a top-level name that does not exist: code text (division, '+ "/x"')
            if outside(token, folder):
                hits.append(token)
    return hits


# the authors' public cancer-cell dataset and StarDist model (allowed; recorded per run, PROTOCOL_V2 section 13)
AUTHORS_PUBLIC = ("research.abo.fi", "10572122", "2024.09.30.615654", "stardistbfcancercell", "stardist_cancercells")


def temporary_path(path: str) -> bool:
    """A file in /tmp that is not another session's folder (the subject's own temporary files: recorded, not rerun)."""
    return path.startswith("/tmp/") and not path.startswith(str(SUBJECT_TMP) + "/")


def environment_path(path: str) -> bool:
    return path.startswith(ENVIRONMENT_PATHS)


def audit(scenario_id: str) -> None:
    sc = scenario(scenario_id)
    folder, run_dir = subject_dir(sc), run_dir_of(scenario_id)
    allowed = set(row_spec(sc["row"])["cli_tools"].split(","))
    session = session_id(run_dir)
    own_tmp = [str(subject_tmp(session))]
    operator_scratch = str(scratchpad())
    calls, flags, notes, lines = [], [], [], [f"# {scenario_id}\n"]
    tmp_files: set[str] = set()
    events = transcript(session)
    refused = {block.get("tool_use_id") for ev in events for block in ((ev.get("message") or {}).get("content") or [])
               if isinstance(block, dict) and block.get("type") == "tool_result"
               and "No such tool available" in json.dumps(block.get("content"))}
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
            elif kind == "tool_use":
                name, inp = block["name"], block.get("input", {})
                calls.append({"tool": name, "input": inp})
                lines.append(f"## assistant (tool call: {name})\n\n```json\n{json.dumps(inp, indent=1)[:4000]}\n```\n")
                if name not in allowed and block.get("id") in refused:
                    notes.append(f"tried {name}, not offered for row {sc['row']}; refused by the CLI (no access)")
                elif name not in allowed:
                    flags.append(f"tool {name} not offered for row {sc['row']}")
                text = json.dumps(inp, ensure_ascii=False).lower()
                if operator_scratch.lower() in text:
                    flags.append(f"{name} refers to the operator's scratchpad")
                if any(t in text for t in AUTHORS_PUBLIC):
                    notes.append(f"{name} refers to the authors' public dataset or model (allowed, recorded)")
                for term in FORBIDDEN_TERMS:
                    if term in text:
                        flags.append(f"{name} input contains {term!r}")
                for key in ("file_path", "path", "notebook_path"):
                    if isinstance(inp.get(key), str):
                        if any(inp[key].startswith(t) for t in own_tmp):
                            notes.append(f"{name} in the subject's own scratchpad (archived)")
                        elif temporary_path(inp[key]) and name != "Read":
                            notes.append(f"{name} of a temporary file in /tmp: {inp[key]} (recorded, not rerun)")
                            tmp_files.add(inp[key])
                        elif outside(inp[key], folder) and environment_path(inp[key]):
                            notes.append(f"{name} of an environment path: {inp[key]}")
                        elif outside(inp[key], folder):
                            flags.append(f"{name} outside the subject folder: {inp[key]}")
                if name == "Bash":
                    cmd = inp.get("command", "")
                    outside_paths = [p for p in shell_paths_outside(cmd, folder)
                                     if not any(p.startswith(t) for t in own_tmp)]
                    env_paths = [p for p in outside_paths if environment_path(p)]
                    tmp_paths = [p for p in outside_paths if temporary_path(p)]
                    bad = [p for p in outside_paths if p not in env_paths and p not in tmp_paths]
                    if env_paths:
                        notes.append(f"Bash refers to environment paths {sorted(set(env_paths))[:5]}")
                    if tmp_paths:
                        notes.append(f"temporary files in /tmp {sorted(set(tmp_paths))[:5]} (recorded, not rerun)")
                        tmp_files.update(tmp_paths)
                    if bad:
                        flags.append(f"Bash refers to paths outside the subject folder {bad[:5]}: {cmd[:200]}")
                    if any(t in cmd for t in own_tmp):
                        notes.append("Bash in the subject's own scratchpad (archived)")
            elif kind == "tool_result":
                text = block.get("content")
                if isinstance(text, list):     # images are kept as files in the subject folder, not as base64 here
                    text = [{"type": "image", "note": "image shown to the subject"} if b.get("type") == "image" else b
                            for b in text]
                text = text if isinstance(text, str) else json.dumps(text)
                lines.append(f"## tool result\n\n```\n{text[:3000]}\n```\n")
    target = run_dir / "subject_scratchpad.tar.gz"
    tmp = subject_tmp(session)                        # the session's own temporary folder, archived then removed
    if tmp.exists():
        if any(p.is_file() for p in tmp.rglob("*")):
            if target.exists():
                raise FileExistsError(f"{target} exists and the session folder has files again: check by hand")
            with tarfile.open(target, "w:gz") as tar:
                tar.add(tmp, arcname="subject_tmp")
        shutil.rmtree(tmp)
    archived = []
    if target.exists():
        with tarfile.open(target) as tar:
            archived = sorted(m.name for m in tar.getmembers() if m.isfile())
    kept = [f for f in sorted(tmp_files) if Path(f).is_file()]
    for f in kept:                                    # /tmp files the subject left behind
        (run_dir / "subject_tmp_files").mkdir(exist_ok=True)
        shutil.copy2(f, run_dir / "subject_tmp_files" / Path(f).name)
    scratch = scratchpad()
    if scratch.exists() and any(scratch.iterdir()):
        flags.append(f"operator scratchpad not empty after the run: {sorted(p.name for p in scratch.iterdir())}")
    result = {"session_id": session, "n_tool_calls": len(calls), "flags": flags,
              "notes": sorted(set(notes)), "scratchpad_archived": archived,
              "tmp_files_named": sorted(tmp_files), "tmp_files_archived": kept}
    store_transcript(transcript_path(session), run_dir / "transcript.jsonl.gz")
    (run_dir / "conversation.md").write_text("\n".join(lines))
    (run_dir / "tool_calls.json").write_text(json.dumps(calls, indent=1))
    (run_dir / "audit.json").write_text(json.dumps(result, indent=1))
    print(json.dumps({k: result[k] for k in ("n_tool_calls", "flags", "notes", "scratchpad_archived")}, indent=1))


def authors_public_use(run_dir: Path, calls: list[dict], history: list[dict]) -> dict:
    """Did the subject find (tool inputs, replies) or use (code to be run) the authors' public dataset or model?"""
    hit = lambda text: any(t in text.lower() for t in AUTHORS_PUBLIC)   # noqa: E731
    code = [run_dir / "code_as_returned.py", *sorted((run_dir / "agent_folder").glob("*.py"))]
    return {"found": hit(json.dumps([c["input"] for c in calls])) or any(hit(t.get("reply") or "") for t in history),
            "in_code_run": any(hit(f.read_text(errors="replace")) for f in code if f.is_file())}


def write_meta(scenario_id: str, notes: str = "") -> None:
    sc = scenario(scenario_id)
    run_dir = run_dir_of(scenario_id)
    session = json.loads((run_dir / "session.json").read_text())
    events, history = transcript(session["session_id"]), turns(run_dir)
    models = sorted({(ev.get("message") or {}).get("model") for ev in events
                     if (ev.get("message") or {}).get("role") == "assistant"} - {None, "<synthetic>"})
    calls = json.loads((run_dir / "tool_calls.json").read_text())
    stamps = [ev["timestamp"] for ev in events if ev.get("timestamp")]
    meta = {"scenario_id": scenario_id, "stage": os.environ["V2_STAGE"], "row": sc["row"],
            "condition": sc["condition"], "task": sc["task"], "field": sc["field"], "replicate": int(sc["replicate"]),
            "interface": f"Claude Code headless session (claude -p --restricted, {session['cli_version']}), "
                         "fresh per scenario, started in its own folder",
            "model": models, "model_requested": session.get("model_requested", session.get("model_alias")),
            "session_id": session["session_id"],
            "models_billed": sorted({m for t in history for m in (t.get("modelUsage") or {})}),
            "datetime_start": min(stamps), "datetime_end": max(stamps),
            "tools_offered": row_spec(sc["row"])["tools"], "cli_tools": session["cli_tools"],
            "web_used": [c["input"].get("query") or c["input"].get("url") for c in calls
                         if c["tool"] in ("WebSearch", "WebFetch")],
            "code_executed_by_subject": any(c["tool"] == "Bash" for c in calls),
            "attachments_sent": json.loads((run_dir / "attachments_sent.json").read_text())["files"],
            "messages_sent": [t["sent"] for t in history],
            "answers_given": [t["sent"] for t in history if t["kind"] == "answer"],
            "follow_ups": sum(t["kind"] == "answer" for t in history),
            "authors_public_material": authors_public_use(run_dir, calls, history),
            "cost_usd": round(sum(t.get("total_cost_usd") or 0 for t in history), 4), "notes": notes}
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print({k: meta[k] for k in ("model", "follow_ups", "code_executed_by_subject", "web_used")})


def python_blocks(text: str) -> list[str]:
    return re.findall(r"```\s*(?:python|py)\s*\n(.*?)```", text or "", flags=re.S)


def analysis_block(replies: list[str]) -> tuple[int, int, str, str]:
    """The script to run (fixed rule): the last Python block, in the latest reply that has one, naming both outputs
    (labels.tif and measurements.csv), i.e. the latest complete script; partial edits sent later are not applied.
    Else the last block naming labels.tif; else the last block of the last reply with code."""
    rules = (("complete script: names labels.tif and measurements.csv",
              lambda b: "labels.tif" in b and "measurements.csv" in b),
             ("names labels.tif", lambda b: "labels.tif" in b), ("last block", lambda b: True))
    for rule, test in rules:
        for r in range(len(replies) - 1, -1, -1):
            blocks = python_blocks(replies[r])
            hits = [i for i, b in enumerate(blocks) if test(b)]
            if hits:
                return r, hits[-1], blocks[hits[-1]], rule
    raise ValueError("no Python block")


def pip_packages(text: str) -> list[str]:
    """Package requirements named in 'pip install ...' instructions (options such as -U dropped), in order, once."""
    out: list[str] = []
    for line in re.findall(r"pip3?\s+install\s+([^\n`]+)", text or ""):
        for token in line.split():
            token = token.strip("\"',;")
            if token and not token.startswith("-") and token not in out and re.match(r"^[A-Za-z0-9]", token):
                out.append(token)
    return out


def first_json_object(text: str) -> dict | None:
    """The JSON object in a fenced block, else the outermost {...} in the text; None if it does not parse."""
    fenced = re.findall(r"```(?:json)?\s*\n(\{.*?\})\s*```", text or "", flags=re.S)
    candidates = fenced or ([text[text.index("{"):text.rindex("}") + 1]] if text and "{" in text else [])
    for c in candidates:
        try:
            value = json.loads(c)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def collect(scenario_id: str) -> None:
    """Row B: the analysis script of the last reply that has code (analysis_block) -> code_as_returned.py (as
    returned; the choice in code_selection.json), and the
    packages its replies ask to install -> packages.txt (row C needs neither: the agent installs what it uses).
    Row C: the subject folder -> agent_folder/. Row D: direct_answers.json (turn-2 numbers left for the operator to
    read from the reply and fill in; turn-3 JSON parsed as given)."""
    sc = scenario(scenario_id)
    run_dir, history = run_dir_of(scenario_id), turns(run_dir_of(scenario_id))
    if sc["row"] == "code":
        replies = [t["reply"] for t in history if python_blocks(t.get("reply") or "")]
        if not replies:
            print("no Python code block in any reply: nothing to run (recorded as no_code)")
            (run_dir / "no_code.txt").write_text("No Python code block in any reply.\n")
            return
        reply_no, index, block, rule = analysis_block(replies)
        (run_dir / "code_as_returned.py").write_text(block)
        later = [n + 1 for n in range(reply_no + 1, len(replies))]
        (run_dir / "code_selection.json").write_text(json.dumps(
            {"replies_with_code": len(replies), "reply_used": reply_no + 1, "block_used": index + 1, "rule": rule,
             "later_replies_with_code_not_used": later}, indent=1))
        print(f"code_as_returned.py: reply {reply_no + 1} of {len(replies)} with code, block {index + 1} ({rule});"
              f" later code not used: {later}")
        packages = pip_packages(" ".join(t.get("reply") or "" for t in history))
        (run_dir / "packages.txt").write_text("# from the replies' pip install lines, as given\n"
                                              + "".join(f"{p}\n" for p in packages))
        print("packages.txt:", packages)
    elif sc["row"] == "optimise":
        shutil.copytree(subject_dir(sc), run_dir / "agent_folder", dirs_exist_ok=False)
        print(sorted(p.name for p in (run_dir / "agent_folder").iterdir()))
    elif sc["row"] == "direct":
        replies = [t["reply"] for t in history if t["kind"] in ("first", "turn")]
        if len(replies) != 3:
            raise RuntimeError(f"{len(replies)} of 3 prescribed turns answered")
        ans = {"field": int(sc["field"]), "turn1_text": replies[0], "turn2_text": replies[1],
               "turn2_median_area_um2": None, "turn2_median_aspect_ratio": None,
               "turn3_json": first_json_object(replies[2])}
        (run_dir / "direct_answers.json").write_text(json.dumps(ans, indent=1, ensure_ascii=False))
        print("turn 2 (fill turn2_median_area_um2 / _aspect_ratio from this text):\n", replies[1])
        print("turn 3 JSON parsed:", ans["turn3_json"] is not None)
    else:
        print("row A: nothing to collect (item check)")


def reject(scenario_id: str, reason: str) -> None:
    sc = scenario(scenario_id)
    runs, attic, _ = stage()
    n = 1 + len(list(attic.glob(f"{scenario_id}_attempt*")))
    target = attic / f"{scenario_id}_attempt{n}"
    target.parent.mkdir(exist_ok=True)
    shutil.move(str(runs / scenario_id), target)
    if subject_dir(sc).exists():
        shutil.move(str(subject_dir(sc)), target / "subject_folder")
    (target / "REJECTED.md").write_text(f"Attempt {n} of {scenario_id} rejected: {reason}\n")
    print("moved to", target)


def is_complete(sc: dict, run_dir: Path) -> bool:
    """A scenario is complete when its last step is done: meta.json (row A; the item table follows) or score.json."""
    return (run_dir / ("meta.json" if sc["row"] == "advice" else "score.json")).is_file()


def status(*_: str) -> None:
    """Completed, partial and next scenarios of the current stage (for resuming after an interruption)."""
    runs, attic, _ = stage()
    done, partial, todo = [], [], []
    for sc in table("scenarios.csv"):
        run_dir = runs / sc["scenario_id"]
        (done if is_complete(sc, run_dir) else partial if run_dir.exists() else todo).append(sc)
    print(f"stage {os.environ['V2_STAGE']}: {len(done)} complete, {len(partial)} partial, {len(todo)} not started; "
          f"{len(list(attic.glob('*_attempt*')))} rejected attempts")
    for sc in partial:
        files = sorted(p.name for p in (runs / sc["scenario_id"]).iterdir())
        print(f"PARTIAL {sc['run_order']} {sc['scenario_id']}: {files}")
    if todo:
        print(f"NEXT {todo[0]['run_order']} {todo[0]['scenario_id']}")
    version = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    if FREEZE.is_file():
        frozen = json.loads(FREEZE.read_text())["cli_version"]
        print(f"CLI {version!r}" + ("" if version == frozen else f" DIFFERS from frozen {frozen!r}: record a deviation"))


if __name__ == "__main__":
    commands = {"status": status, "prepare": prepare, "start": start, "answer": answer, "turn": turn, "give_dev_files": give_dev_files,
                "audit": audit, "meta": write_meta, "collect": collect, "reject": reject}
    if len(sys.argv) < 2 or sys.argv[1] not in commands or (sys.argv[1] != "status" and len(sys.argv) < 3):
        raise SystemExit(__doc__)
    commands[sys.argv[1]](*sys.argv[2:])
