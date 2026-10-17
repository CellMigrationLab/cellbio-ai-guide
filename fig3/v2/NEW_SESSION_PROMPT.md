# Prompt for a new session (operator of Figure 3, protocol v2)

Paste the text below into a new Claude Code session started **in the repository `CellMigrationLab/cellbio-ai-guide`**
(so that `.claude/agents/subject-chat.md` is loaded). Optional environment setup script (cloud environment settings),
so the tools need not be reinstalled each time:

```bash
pip install -r environment/requirements-models.txt --extra-index-url https://download.pytorch.org/whl/cpu
python -c "from cellpose import models; models.CellposeModel(gpu=False)"   # downloads the cpsam weights once
```

---

```text
You are the operator of Figure 3 (protocol v2) for "The cell biologist's guide to AI-assisted image analysis".
Repository: CellMigrationLab/cellbio-ai-guide (push to main is authorised; commit after every 10 scenarios).

Read first, in this order: AGENTS.md, fig3/PROTOCOL_V2.md (the only plan), fig3/v2/README.md, fig3/v2/answer_sheet.md,
and fig3/deviations.md (including the lessons from the round-2 pilot).

1. Environment check (stop and tell me if anything fails):
   - `make check` and `make full` pass;
   - torch 2.14.1+cpu, torchvision 0.29.1+cpu and Cellpose 4.2.1.1 import, and `from cellpose import models` works
     (if not: pip install -r environment/requirements-models.txt --extra-index-url https://download.pytorch.org/whl/cpu);
   - the sub-agent type `subject-chat` (Read, WebSearch, WebFetch only; no shell) is available. If it is not, stop
     and tell me: rows A, B and D must not be run with an agent that has a shell.
   - Record `pip freeze` in fig3/v2/environment_freeze.txt.
   - Export SUBJECT_SCRATCHPAD=<your session's scratchpad directory, from your system prompt> for every
     run_operator.py call (prepare and audit use it to check and archive what subjects write there).

2. Preflight: one scenario per row x task (12 runs), following fig3/v2/README.md step by step, in
   fig3/v2/runs_preflight/ (not used in the figure). Fix harness problems only (operator, runner, scorer, framing),
   never the prompts' content without asking me. Show me a short report: what worked, what failed, what you changed.

3. After I approve: freeze protocol v2 (SHA-256 of prompts, rows.csv, scenarios.csv, answer sheet, run_operator.py,
   runner.py, score.py, make_protocol.py, PROTOCOL_V2.md, the agent definition and environment_freeze.txt, plus a
   test that fails if any changes), then run the 72 scenarios in scenarios.csv order.

Rules that must never be broken:
- The subject never sees this repository, the protocol, the answer sheet, the condition names or other runs. It gets
  only the framed first message from run_operator.py prepare and the files listed for its scenario. Start each
  subject from its own subject folder, with the sub-agent type named in rows.csv, fresh for every scenario.
- Answer follow-up questions only from the answer sheet, verbatim, at most 3 replies. Row B: the field-104 image and
  annotation only if asked before any code was given (run_operator.py give_dev_files). Never give a field-209
  annotation.
- Empty the harness scratchpad before each subject (prepare refuses otherwise); audit every run; follow the rerun
  policy in PROTOCOL_V2.md section 9 exactly; archive every attempt (run_operator.py reject).
- Code is run only by fig3/v2/runner.py, unchanged except input/output paths (diff in EDITS.md).
- Always score against the authors' manual annotations; if anything about a reference looks wrong, stop and ask.
- Row A: make the item table (current / outdated / does not exist / not possible, with the source of each) for me to
  review; do not choose the example to show.
- Record every deviation in fig3/deviations.md. Ask me before changing anything in PROTOCOL_V2.md.
Report progress in short messages; ask all your questions together when you need decisions.
```
