# Figure 3: deviations from protocol and other things an auditor should know

Round 1 (the current draft). Deviations under protocol v2 will be recorded in a section of their own.

Lessons from the round-2 pilot (3 scenarios, 17 Oct 2026; removed, see git history), built into the v2 harness: Claude
sub-agents always have a shell (rows without code use the `subject-chat` agent); the harness scratchpad is shared
(emptied before each subject); torchvision must match the CPU build of torch; answer-sheet lines must not mention
files that were not sent; a script that fails must never be scored as successful.

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
  headless; nothing else was edited.
- Python scripts were run unchanged in a folder containing the image.
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
- In the Box 1 v3 pilots we answered the models' questions from a fixed answer sheet (the pilots were later removed; git history).
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

## Protocol v2 (operator: Claude Code, from 17 Oct 2026)
Changes made before the preflight, decided by the authors on 17 Oct 2026 (PROTOCOL_V2 sections 3 and 13 updated):
- **Subjects are headless Claude Code sessions, not sub-agents.** A probe of the `subject-chat` sub-agent (a harness
  check, not a scenario) showed that a sub-agent receives the operator session's project instructions (the whole
  AGENTS.md: the purpose of Figure 3, the four rows and the condition names) and its working directory (the
  repository). Each subject is now a fresh `claude -p --restricted --strict-mcp-config --disable-slash-commands`
  session, model `sonnet`, new session ID, started in its own folder, with only its row's tools (`cli_tools` in
  `rows.csv`); follow-up turns resume the same session. A probe of this set-up reported no project instructions, no
  git repository, its own scratchpad and only the tools given. The sub-agent definition (`.claude/agents/subject-chat.md`)
  was removed. The command line and the environment variables not passed on are in `run_operator.py` and in each
  run's `session.json`.
- **Round-2 pilot**: its sub-agent subjects very likely had the same AGENTS.md in their context. The pilot is not used
  in the figure.
- **Account context**: each subject's context still contains the account's email address (one of the authors) and
  commit-attribution lines; both come from the account, not the repository, and cannot be removed from the operator
  session. Accepted by the authors. The audit flags any tool input that names the study, its authors or this
  repository; such a run is rerun (subject access to forbidden material).
- **Row D** is given the Read tool only, so the web cannot be used (section 3 says "no web").
- **Row C** keeps a shell; the CLI cannot confine it to the folder (a shell could list `/home/user`). Isolation is the
  framing sentence plus the audit, as the protocol states.
- **Effort**: the operator session's effort setting is not passed on; subjects run at the CLI default. The CLI may use
  a small model internally (e.g. for session titles or web-search summaries); models billed are recorded in `meta.json`
  (`models_billed`), the model that wrote the replies in `model`.
- Protocol section 3, row A's tools read "web search, view attachment"; row A has no attachment (section 5, `rows.csv`),
  so the table now reads "web search".
- **Environment**: the Cellpose `cpsam_v2` weights download was truncated twice by the network proxy; the file was
  downloaded again with resume and checked against the SHA-256 published by Hugging Face (recorded at the top of
  `v2/environment_freeze.txt`).

### Preflight (12 runs, `v2/runs_preflight/`, not used in the figure): harness fixes
Found in the preflight and fixed before the freeze (operator, runner, scorer, assets; no prompt changed):
- **Assets**: `make_assets.py` wrote the subject TIFFs without the pixel size (the raw files carry an ImageJ calibration,
  0.649614 µm/px, unit micron), although the answer sheet says "0.65 µm per pixel, from the metadata". A script that
  read the pixel size from the file stopped. The TIFFs now keep the calibration (pixel values unchanged; other ImageJ
  fields, such as a channel label naming the source file and cell line, are not copied). The first attempt of
  `code_simple_endo_r3` was rejected for this (harness fault) and rerun.
- **Script to run (row B)**: replies may hold several code blocks (e.g. the analysis and an evaluation script) and
  later replies may hold only partial edits. Fixed rule: the latest Python block that names both outputs
  (`labels.tif` and `measurements.csv`), searching the replies from the last; partial edits are not applied (that
  would be editing beyond paths). The choice is recorded in `code_selection.json`.
- **Packages (row B)**: `packages.txt` is written from the replies' `pip install` lines, as given.
- **Runtime manifest (row C)**: the prompt fixes no format, so the runner copies every string in
  `runtime_manifest.json` that names a file in the agent folder (development image and annotation refused, as before).
- **Audit**: `~` paths are resolved; code fragments in heredocs (a bare `/`, `+ "/x.npy"`) are no longer read as
  paths; installed software and the shared Cellpose model cache (`/usr`, `/opt`, `~/.cellpose`, ...) are noted, not
  flagged; a call to a tool the session does not have, refused by the CLI, is noted ("no access"), not flagged; the
  session's own temporary folder is archived to `subject_scratchpad/`.
- **Row D count**: the count is the first number of the reply (list markers skipped); a range counts only if that
  first number starts it (before, a range anywhere in the reply was taken). A turn-2 range is recorded as its midpoint,
  with the text kept in `turn2_read_by_operator`.
- **Answers**: `run_operator.py answer` refuses text that is not a sequence of answer-sheet sentences, verbatim.
- **Images shown to the subject**: the CLI re-encodes the attached PNG as JPEG at full size (1024 × 1022) before the
  model sees it; coordinates are unchanged.

### Authors' decisions after the preflight (17 Oct 2026; PROTOCOL_V2 sections 3, 5, 6 and 13 updated before the freeze)
- **Row C, reads decide**: reading or listing anything outside the folder that could carry information is a
  violation (rerun); the subject's own temporary files in `/tmp` are recorded in `audit.json`
  (`tmp_files_named`), archived to `subject_tmp_files/` if still present, and not rerun. Preflight
  `optimise_labels_endo_r2` wrote and deleted test outputs in `/tmp`.
- **Row B**: the latest complete script is run; later partial edits are not applied (`code_selection.json`).
  Preflight `code_box1_nuclei_r3`.
- **Follow-ups**: only explicit questions are answered; conditional offers get no reply. In the preflight the offer in
  `advice_simple_endo_r2` was answered and the one in `direct_three_turns_endo_f209_r3` was not (the inconsistency that
  led to the rule).
- **Authors' public dataset and model** (Zenodo 10572122; research.abo.fi; bioRxiv 10.1101/2024.09.30.615654): allowed;
  `meta.json` records whether the subject found it (`authors_public_material.found`) and whether the code that was run
  uses it (`in_code_run`); such row B or C runs are marked in the figure. Found by preflight `advice_box1_cancer_r1`
  through task-based searches.
- **Model ID pinned** (before the freeze, authors' request for reproducibility): subjects are started with the full
  model ID `claude-sonnet-5-5` instead of the alias `sonnet` (the alias resolved to the same model in all preflight
  runs, recorded in each `meta.json`). The Claude Code CLI version is recorded in `FREEZE.json` and in each run's
  `session.json`; a run with a different CLI version is recorded here.
- **Commits**: after every scenario (authors' request), so that an interrupted session can resume from the last pushed
  state (`v2/RESUME_PROMPT.md`).
- **Storage of run records** (before the freeze, to keep 72 runs within a git repository): the session transcript is kept
  with each run as `transcript.jsonl.gz` (every event; base64 image payloads replaced by their SHA-256 and length;
  the images are the attachments or files archived with the run); label images written by scripts are stored
  gzip-compressed with their exact bytes (`labels_fF.tif.gz`); the subject's temporary folder is one
  `subject_scratchpad.tar.gz`. Preflight records were converted the same way; their scores are unchanged.

### Main run (frozen protocol; amendments are also listed in `v2/FREEZE.json`)
- **Runner amendment (run 4, `optimise_labels_endo_r2`)**: the agent's `runtime_manifest.json` named the shared
  Cellpose weights by absolute path (`/root/.cellpose/models/cpsam_v2`); the runner treated it as a file in the agent
  folder and stopped before running anything. Absolute paths are now ignored (the weights are part of the
  environment); only relative names inside the agent folder are copied. Harness fault, no subject rerun needed (the
  runner had produced nothing); no earlier run had such a manifest.
- Run 4: the agent ran `mkdir -p /tmp/claude-0/s` (an empty folder it never used; removed by the operator). A write of
  its own temporary folder, nothing read: recorded, not rerun (reads decide, section 3).
- **Operator convention (from run 10, `advice_box1_cancer_r1`)**: a conversation is closed without a further message
  when the only questions left are ones already answered (as in the round-2 pilot); the answer sheet does not cover
  repeated questions.
- **Operator amendment (run 11, `code_box1_nuclei_r3`)**: the "latest complete script" rule selected a 16-line indented
  patch from reply 2 that named both output files (it crashed with IndentationError). A complete script must now also
  parse on its own and contain an import; the run was re-collected (reply 1, the full script) and re-run; the first
  selection and its execution records are kept in `superseded_selection/`. Runs 2 and 7 re-checked: same selection.
- **Claude Code CLI version (from run 14, `direct_three_turns_endo_f209_r3`; authors' decision, 19 Oct 2026)**: runs 1–13
  used CLI 2.1.302 (as in `FREEZE.json`); the container that resumed the main run has 2.1.303. Runs from 14 onward use
  2.1.303 (recorded in each run's `session.json`). Subject model unchanged (`claude-sonnet-5-5`). Affected: runs 14–72.
  The resumed environment was rebuilt from `environment_freeze.txt` (identical `pip freeze`; `cpsam_v2` SHA-256 matches).

### Revision of rows B and C (19 Oct 2026, authors' decision; A and D unchanged)
- **Why**: the first 19 main runs (runs 1–19; B and C: 12 runs) used field 104 for development and field 209 for test.
  On field 209 (DAPI) all four nuclei pipelines drew masks about twice the manual area (median 802 vs 435 px; centres
  agree, F1 0.55 against 0.96 on field 104): the field carries a faint haze around the nuclei that field 104 does not.
  One test field made the comparison of the ways of using the model depend on how typical that field is.
- **New design (rows B and C only)**: the development image is a mosaic of the left halves (x < 512) of fields 104 and
  209 (`v2/assets/halfdev_<task>_image.tif/.png`, annotation `halfdev_<task>_annotation.tif/.png`; objects cut at
  x = 512 stay cut). Subjects, prompts and the answer sheet are otherwise unchanged (the mosaic has the size of a field).
  The runner still runs scripts and pipelines unchanged on the **whole** fields 104 and 209; scoring crops to the held-out
  right halves (x ≥ 512) (`fig3.scoring.tasks.score_heldout(field=...)`, `v2/score.py`); endothelial cells touching the
  border of the crop are removed from prediction (as for the whole field). The reported score is the mean of the F1 on
  the two fields (`score.json`: `mean.f1`), as in Figures 1 and 2 (whole fields; same references and scorer).
- **Affected runs**: all B and C runs made before the revision (`runs_superseded/`, kept unedited with their old scores
  on field 104 as development and field 209 as test); B and C restart from the first scenario. Rows A and D runs already
  done stay (the subject sees nothing of this change).
- **Frozen files changed** (hashes in `FREEZE.json` amendments): `PROTOCOL_V2.md`, `answer_sheet.md` (intensity values
  and annotation counts of the mosaic), `make_assets.py` and `assets/` (mosaic files added; existing files unchanged),
  `make_protocol.py`, `scenarios.csv` (folder_files of rows B and C), `run_operator.py` (annotation file names),
  `score.py` and `scoring/tasks.py` (held-out half scoring for a chosen field; round-1 behaviour unchanged).
- **Answer sheet amendment (19 Oct 2026, runs 7 onward of rows B and C)**: every subject that was shown the development
  mosaic noticed the seam at x = 512 in the PNG preview and asked whether it is one image. The sheet had no line for it, and
  "I don't know." would have been untrue, so two lines were added: the image is two fields placed side by side (answered only
  when asked), and `image.png` is an 8-bit display copy of `image.tif`. Runs 2, 4 and 6 did not ask (run 6 mentioned the seam
  in its final report).

### Row D observation: the model declined to draw ellipses for nuclei and endothelial cells (19 Oct 2026)
- In turn 3 ("draw an ellipse around every ... and give the JSON") the model drew ellipses in all 6 cancer-cell
  conversations (113–160 ellipses) and **declined in all 12 nuclei and endothelial-cell conversations**: it said it could
  not run code or measure pixels, so it would be inventing 300–1,000 coordinates, repeated its earlier estimates and gave
  a Cellpose script instead. These are valid results (a refusal is never rerun, PROTOCOL_V2 section 9); `score.json` has
  `turn3.status = no_valid_json` and F1 0 for them. The replies are kept verbatim in `turns.json`; `v2/direct_summary.csv`
  (made by `v2/summarise_direct.py`) records one line per conversation, with the start of each decline.
- Authors' decision (19 Oct 2026): the figure shows only the count results of row D (the turn-1 stated count); the count of
  ellipses drawn, the F1 of the drawn outlines and the stated medians are not shown in the figure.
