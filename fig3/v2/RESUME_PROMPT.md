> **Kept for reference.** The main run was completed on 19 Oct 2026 (72 runs). This prompt describes the original protocol; rows B and C
> were revised afterwards (`fig3/PROTOCOL_V2.md` revision note, `fig3/deviations.md`), so do not use it unchanged to run new scenarios.

# Resuming the Figure 3 main run (protocol v2) in a new session

Use this if the operator session stopped (credits, time-out, container lost). Everything that counts is in git on
`main`: each scenario is committed and pushed as soon as it is complete. Start a new Claude Code session in the
repository `CellMigrationLab/cellbio-ai-guide` and paste the text below.

```text
You are the operator of Figure 3 (protocol v2) for "The cell biologist's guide to AI-assisted image analysis",
resuming an interrupted main run. Repository: CellMigrationLab/cellbio-ai-guide; work on main (push to main is
authorised); commit and push after every scenario.

Read first: AGENTS.md, fig3/PROTOCOL_V2.md (frozen), fig3/v2/README.md, fig3/v2/answer_sheet.md, fig3/deviations.md
(all of it, including the protocol v2 sections), fig3/v2/FREEZE.json.

1. Environment (stop and tell me if anything fails):
   - pip install -r environment/requirements-models.txt --extra-index-url https://download.pytorch.org/whl/cpu
   - Cellpose weights: ~/.cellpose/models/cpsam_v2 must have the SHA-256 recorded at the top of
     fig3/v2/environment_freeze.txt. The download is often cut by the proxy: use
     curl -L -C - -o ~/.cellpose/models/cpsam_v2 https://huggingface.co/mouseland/cellpose-sam/resolve/main/cpsam_v2
     (repeat until the size and SHA-256 match), then check `from cellpose import models; models.CellposeModel(gpu=False)`.
   - `pip freeze` must equal fig3/v2/environment_freeze.txt (ignore its first comment line); do not install anything
     else into this environment. If it differs, tell me before running anything.
   - `make check` passes; it includes fig3/tests/test_v2_freeze.py (nothing that defines the protocol has changed).
   - `claude --version` equals cli_version in FREEZE.json; if not, tell me (a different CLI is a recorded deviation).
   - export V2_STAGE=main PYTHONPATH=. SUBJECT_SCRATCHPAD=<this session's scratchpad directory, from your system prompt>
2. Where we are: `python fig3/v2/run_operator.py status` (complete / partial / next).
3. Partial scenarios (a run folder without its final file): if the subject's conversation is complete (turns.json
   ends with the subject's last reply; transcript.jsonl and audit.json are in the run folder; for row C also
   agent_folder/), finish the remaining steps (collect, runner, score). Otherwise the attempt was interrupted:
   `run_operator.py reject <id> "interrupted: <what happened> (PROTOCOL_V2 section 9, API or session interruption)"`,
   then run it again from prepare. Never edit or delete a stored run.
4. Continue the scenarios in scenarios.csv order, one subject at a time, exactly as fig3/v2/README.md says
   (prepare, start, answers from the answer sheet only and only to explicit questions, turns for row D, audit, meta,
   collect, runner, score). Row C runs in the background; do not start another subject or any helper agent while a
   subject runs. After each scenario: git add, commit ("fig3/v2 main run: <run_order> <scenario_id>") and push to main.
5. Rules that must never be broken:
   - Subjects are headless sessions started only by run_operator.py start (never a sub-agent: a sub-agent sees
     AGENTS.md). The subject never sees this repository, the protocol, the answer sheet, condition names or other runs.
   - Answer follow-up questions only from the answer sheet, verbatim, at most 3 replies; row B gets the field-104
     image and annotation only if asked before any code (run_operator.py give_dev_files); never a field-209 annotation.
   - Rerun only for the reasons in PROTOCOL_V2 section 9 (row C: reads decide, section 3); archive every attempt with
     run_operator.py reject, the reason written before the new attempt.
   - Code is run only by fig3/v2/runner.py; scores only against the authors' manual annotations; if a reference looks
     wrong, stop and ask.
   - Row A: draft the item table per reply (items.csv: current / outdated / does_not_exist / not_possible, with the
     source of each) for the authors to review; do not choose the example to show. Do this only when no subject runs.
   - Any departure from the frozen protocol goes into fig3/deviations.md with the affected runs; ask before changing
     PROTOCOL_V2.md or any frozen file.
Report progress in short messages; ask all questions together when you need decisions.
```
