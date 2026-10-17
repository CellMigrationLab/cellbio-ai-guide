# Figure 3: deviations from protocol and other things an auditor should know

## Prompts and harness
- All runs used Claude Code sub-agents (not the claude.ai app). Each prompt starts with our wrapper text (role, which
  file may be viewed, whether code can be run, which tools may be used) and ends with an output-format instruction
  (`labels.tif`, one code block). Both are visible in every `prompt.md`.
- Box 1 prompts included a setup line not in Box 1 ("My setup: Python … Cellpose 4.2.1.1 (CPU only)" / "a current Fiji
  installation") so that the code could run in our environment.
- Web tools (WebSearch/WebFetch) were allowed where stated but had to be loaded by the model before use; many runs did
  not load them, one concluded it had no web access. "Did not check the documentation" is therefore partly a harness effect.
- Box 1 v1 (stricter wording) runs were superseded by Box 1 v2 runs (`superseded/runs/python_box1_v1wording_*`).

## Running the code
- Fiji macros: the `input = …` and `output = …` lines were replaced by absolute paths so that the macros could run
  headless (`harness/collect.py`); nothing else was edited.
- Python scripts were run unchanged in a folder containing the image (`harness/queue_runner.sh`).
- Two Fiji macros failed and wrote no output, counted as F1 0 (× in the figure): `fiji_generic_cancer_r3` calls a
  non-existent command ("Set Scaling…"); `fiji_box1_nuclei_r2` calls `ceil()`, which the ImageJ macro language does not have.
- Draw runs: the model's polygons were rasterised (`direct_answers/code/rasterise_poly.py`). `draw_nuclei_r2` returned
  centres plus a hexagon rule instead of polygons; it was rasterised from its own rule. Endothelial "outlines" were a
  placeholder grid, as one reply states.

## Agents (row c)
- The nuclei agent with annotation wrote its working files outside its folder; they were copied back
  (`optimise/runs/with_annotation_nuclei/artifacts/written_outside_sandbox/`).
- The cancer agent (rerun) wrote intermediate files to `/tmp`.
- The endothelial agent (rerun) copied `pipeline.py` and `log.txt` outside its folder and deleted the copies (it said so).
- The first attempts of the cancer and endothelial agents with annotation were interrupted by a session restart and
  rerun from clean folders (`superseded/runs/optimise_with_annotation_*_interrupted`).
- By-eye agents were scored on the held-out half so that both conditions are compared on the same cells.
- Agents' reported development scores came from their own scoring code; re-scored with ours in `optimise/dev_rescored.json`.

## Answers to follow-up questions (pilots only)
- In the Box 1 v3 pilots we answered the models' questions from a fixed answer sheet (`pilots/answer_sheet_pilot.md`).
  One answer was wrong ("label the visible part of endothelial cells under cancer cells"; the annotation runs under
  them); the advice run that spotted the inconsistency received the correction, the code pilot did not.

## Scoring conventions
- Nuclei, round 1 (draft figure): predicted objects lying > 30 % on annotated cancer cells were ignored before
  matching (cancer-cell nuclei are not annotated). This also discarded correct predictions of the 17 annotated
  endothelial nuclei under cancer cells (best achievable F1 0.98). Found by the tests on 17 Oct 2026.
- Nuclei, from round 2: predictions are matched to the full manual annotation (441 nuclei) first; only unmatched
  objects lying > 30 % on cancer cells are ignored. Round-1 nuclei scores under this rule (for comparison): Python
  Box 1 0.94 → 0.96, Cellpose default 0.94 → 0.96, other runs change by < 0.01.
- Endothelial cells: objects touching the image border are removed from reference and prediction; reference cells come
  from annotator 1's junction lines (`lines_to_cells`, slivers < 150 px removed).
- Code that crashed or wrote no label image: F1 0, drawn as ×.

## Round 2 (Claude side; operator: Claude Code, 17 Oct 2026 onwards)
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
