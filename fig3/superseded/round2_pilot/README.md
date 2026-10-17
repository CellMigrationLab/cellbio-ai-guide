# Round-2 pilot (17 Oct 2026; superseded by `fig3/PROTOCOL_V2.md`, not used in any figure)

The round-2 design (162 scenarios, Claude and ChatGPT, prompts in `prompts/`, operator rules in `OPERATOR.md`,
answers in `answer_sheet.md`, hashes in `protocol_freeze.csv`) was started and stopped after three accepted Claude
scenarios. It was replaced by protocol v2 after the authors' redesign and two ChatGPT audits (pull request 2 in this
repository). Everything run is kept here for audit:

- `runs/`: the accepted pilot scenarios (advice generic nuclei r3; Fiji generic cancer r1, macro syntax error;
  Python Box 1 cancer r3, attempt 2, interrupted by a rate limit after the annotation was sent, not scored);
- `runs_rejected/`: rejected attempts with the reason in `REJECTED.md`;
- `run_operator.py`, `make_scenarios.py`: the operator helper and scenario generator as used.

Lessons carried into protocol v2: Claude sub-agents always have a shell (code rows need an agent without one); the
harness scratchpad is shared; torchvision must match the CPU build of torch; Fiji needs a virtual display; answer-sheet
lines must not mention attachments that were not sent; a failed script must never be scored as successful.

## Operator notes from the pilot
Operator conventions applied to every Claude scenario, decided before or at the first scenario and not changed after:
- Subjects are fresh Claude Code sub-agents (general-purpose, `sonnet` = claude-sonnet-5-5), started from a neutral
  working directory `/home/user/sessions/sNNN` (named by run order only). The harness adds its own reminder that the
  reply is delivered with `SubagentHandback`; it is visible in every `conversation.md`.
- Isolation is checked, not enforced: a hook confining sub-agents to their folder was blocked by the session's
  permission policy, so `run_operator.py audit` lists every tool call of the subject and flags any tool or path outside
  the row's allowance. A flagged access to the repository or another scenario means the scenario is rerun.
- Code rows: Claude cannot display a TIFF, so the subject's folder holds `image.tif` (the user's file) and the PNG
  preview `image.png`, and the framing names `image.png` as the viewable attachment (OPERATOR.md section 3 fallback).
- Advice rows send no image. A request to send the image or a crop is not covered for this row by the answer sheet, so
  it is answered "I don't know". The image-size line is quoted verbatim even though it mentions the PNG preview
  (first seen in `claude_advice_generic_nuclei_r3`).
- A conversation is closed without a further message when the subject's only remaining request is one already answered.
- Code rows may run code (authors' decision, 17 Oct 2026, after the first attempt of `claude_code_fiji_generic_cancer_r1`,
  whose subject ran a Python prototype unprompted and wrote files in the operator's scratchpad; that attempt is kept in
  `round2/runs_rejected/`). From then on the code-row framing adds the frozen section-6 sentence "You can run shell
  commands in the folder <path> only.", every such run is recorded as `app_executed_code`, and the final code is still
  run unchanged (paths only) on field 209. This matches the ChatGPT code tool allowed in OPERATOR.md 3.4. Advice and
  direct rows offer no shell; a subject that runs code there is rerun.
- The operator's scratchpad (visible to sub-agents through the harness) was emptied after that attempt; it held
  round-1 working files. No subject read them (audit of attempt 1).
- The harness tells every sub-agent to keep temporary files in the operator's scratchpad, and subjects do so even when
  told to stay in their folder. The scratchpad is emptied before each subject, and what a subject leaves there is
  moved to `subject_scratchpad/` in its run folder. Scratchpad use is recorded in `audit.json`, not treated as a rerun
  (it holds nothing but the subject's own files); any other path outside the folder still means a rerun.
- Fiji macros run as in round 1, `xvfb-run -a <Fiji> -batch macro.ijm` (virtual display, no `--headless`), because
  `--headless` fails on macros that open windows.
- Environment fault found by the subject of `claude_code_python_box1_cancer_r3` (attempt 1): torchvision did not match
  the CPU build of torch, so Cellpose could not be imported. Fixed (torchvision 0.29.1+cpu, now pinned in
  `environment/requirements-models.txt`) and the scenario rerun; attempt 1 is in `round2/runs_rejected/`. Scenarios 1
  and 2 did not depend on it (advice; a Fiji macro).
