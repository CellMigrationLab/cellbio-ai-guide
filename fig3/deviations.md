# Figure 3: deviations from protocol and other things an auditor should know

This file records everything in the Figure 3 experiment that departed from [`PROTOCOL_V2.md`](PROTOCOL_V2.md), and what an
auditor should know about how the runs were made and scored. Amendments to frozen files are also listed in `v2/FREEZE.json`.

## Before protocol v2 (summary; the records are in git history)

Two earlier attempts preceded the protocol: a first study (16–17 Oct 2026: Claude Code sub-agents on one field, Fiji macros
and Python scripts, a row in which the model drew polygons) and a three-scenario pilot of a revised design (17 Oct 2026). Both
were discarded when a probe showed that a sub-agent receives the operator session's project instructions (this repository's
AGENTS.md, which names the study and its conditions) and its working directory, so the model being tested could see the
study. Their records were removed from the repository on 19 Oct 2026. What they taught, and what protocol v2 does about it:
subjects are fresh headless sessions, never sub-agents; the harness scratchpad is shared and is emptied before each subject;
answer-sheet lines must not mention files that were not sent; a script that fails is never scored as successful; and nuclei
predictions are matched to the full manual annotation first, with only the unmatched objects lying on cancer cells ignored
(the first rule dropped such objects before matching and so discarded correct predictions of the 17 annotated nuclei under
cancer cells).

**Records removed on 21 Oct 2026.** Only the 72 accepted runs are kept in the repository (`v2/runs/`). The preflight runs
(`v2/runs_preflight/`, `v2/runs_preflight_rejected/`), the rejected attempts (`v2/runs_rejected/`), the superseded rows B and C
runs (`v2/runs_superseded/`), the exploratory summaries (`v2/direct_summary.csv`, `v2/code_metrics.csv`, `v2/code_rating/`,
`v2/advice_api_check.csv`) and the operator prompts (`v2/RESUME_PROMPT.md`) that the sections below mention were removed from
the working tree and are in git history before that commit.

## Scoring conventions (protocol v2; implemented in `scoring/tasks.py` and `v2/score.py`)
- Nuclei: predictions are matched to the full manual annotation (441 nuclei in field 104, 473 in field 209) first; only
  unmatched predicted objects lying > 30 % on annotated cancer cells are then ignored, because cancer-cell nuclei are not
  annotated.
- Endothelial cells: the reference comes from annotator 1's junction lines (`common.annotations.lines_to_cells`, slivers
  < 150 px removed); objects touching the image border are removed from reference and prediction.
- Rows B and C: a script or pipeline that crashed or wrote no label image scores F1 0 on that field (drawn as ×).

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

### Parallel subjects, a boundary violation and process isolation (19 Oct 2026)
- **Parallel runs**: with the authors' permission, rows A, B and D (chat only, no shell) and several row C agents ran at the
  same time (up to three C agents at once on 4 CPUs). The protocol had one subject at a time.
- **Violation (run 28, `optimise_by_eye_endo_r2`, first attempt)**: the agent ran `pgrep -af pipeline`, which printed the full
  command lines of other subjects' sessions, including another subject's prompt (v013). That is a listing of information
  from outside its folder (PROTOCOL_V2 sections 3 and 9). The attempt was rejected and archived unedited in
  `v2/runs_rejected/optimise_by_eye_endo_r2_attempt1/` and the scenario was run again. A search of the other finished row C
  transcripts found no other command that prints process command lines (several used `pgrep -f` as a wait loop, which prints
  process ids only and can wait on another agent's process; harmless for the results).
- **Isolation (from the rerun of run 28 onward)**: every subject session is started through a one-line wrapper that runs
  the same Claude Code CLI in its own process namespace (`unshare --pid --fork --mount-proc`), so a subject sees only its own
  processes. The wrapper is outside the repository (`PATH` of the start command) and does not change `run_operator.py`.
  Row C runs 8, 9, 12, 13 and 16 (and the agents already running when this was found) ran without it.
- **Earlier runs**: a `ps` in any earlier subject would also have shown the operator's command lines (they contain the
  scenario id). The audit found no such command in the runs checked.
- **Run 19 (`optimise_labels_endo_r1`), first attempt**: interrupted when the operator's background command reached its time
  limit while the subject was still training a model; rejected and archived (`v2/runs_rejected/optimise_labels_endo_r1_attempt1/`),
  then run again in an isolated process namespace (PROTOCOL_V2 section 9, session interruption).
- **Large files (19 Oct 2026)**: the first attempt of run 19 saved a fine-tuned Cellpose model (`ft_a.pt`, 1.2 GB) in its
  folder, which the git host refuses. Files over 50 MB in run records are moved outside the repository by
  `v2/large_files.py` (to `/home/user/large_files_archive/`) and listed with size and SHA-256 in `LARGE_FILES.json` in the
  run folder (here `runs_rejected/optimise_labels_endo_r1_attempt1/LARGE_FILES.json`). Nothing else in the record changed.
- **Worker restart (19 Oct 2026, about 11:00 UTC)**: the session that operates the experiment was restarted while three agents were
  working (run 19 second attempt, run 52 `optimise_labels_endo_r3`, run 62 `optimise_by_eye_cancer_r2`; their last recorded events
  are tool calls). The three attempts were rejected and archived unedited in `v2/runs_rejected/` (PROTOCOL_V2 section 9, session
  interruption) and run again in isolated process namespaces. The scoring of run 66 was interrupted and repeated from the stored
  agent folder.
- **Extra model weights in the shared folder**: a file `~/.cellpose/models/cpsam` (1.2 GB, created 19 Oct 06:10 UTC) appeared next to
  `cpsam_v2`; it was downloaded by one of the agents running in that period. The frozen environment records only `cpsam_v2`; the
  default model used by `CellposeModel()` is still `cpsam_v2`. The affected run is not identified.
- **Second worker restart (19 Oct 2026, about 11:20 UTC)**: the three reruns of runs 19, 52 and 62 were killed again before they
  finished; their attempts were rejected and archived (`v2/runs_rejected/*_attempt2` and `_attempt3`) and the three scenarios were
  started a third time. The scoring of run 66 was interrupted a second time and repeated.
- **Cause of the interruptions (19 Oct 2026)**: the virtual machine that runs the experiment is suspended and restarted whenever the
  operating session is idle, and every running subject is killed (`uptime` showed the machine had just booted). Runs 19, 52 and 62
  were interrupted three times in this way (attempts 1 to 3 in `v2/runs_rejected/`); from the fourth attempt the operator stays
  active (polling) for the whole run. The protocol rule (PROTOCOL_V2 section 9, session interruption: rerun) was applied each time.

## Amendment: audit fixes (20 Oct 2026, external code review PR)

A whole-repository audit found robustness gaps in the harness. None of the fixes below changes any recorded run, stored
score or figure (verified: `make check` reproduces all stored scores; `runtime_files` on every stored run folder
returns the same files the original code copied). The freeze was re-recorded after these changes; the subject model,
prompts, answer sheet and scenarios are untouched.

- **`runner.py`**: a runtime file whose bytes equal any file in `fig3/v2/assets` or `data/raw` is now refused like
  `annotation.tif` (across `data/raw` this also catches held-out material under any name), and two runtime files that
  share a basename now raise (the loader's pick was ambiguous before: copy order decided which file the pipeline read).
  `EXEC_ROOT` is `R2EXEC_ROOT` from the environment, default unchanged (`/home/user/r2exec_v2`).
- **`runner.py`**: when the runner itself runs from a virtual environment, the run's `PYTHONPATH` points at that
  environment's `purelib` so `system_site_packages=True` gives the run the same packages it gives when started from a
  system interpreter (previously a run under a venv-in-venv operator crashed on `import numpy`). On the operator host
  (system interpreter) this changes nothing.
- **`run_operator.py`**: `ENVIRONMENT_PATHS` gained home-relative entries (`~/.cellpose`, `~/.cache/pip`,
  `~/.local/lib`), so the audit accepts an operator home on any platform, not only `/root` and `/home/<user>`.
- **`common/matching.py`**: `match` validates both label images (`validate_labels`), so a probability map, NaN image
  or stack fails instead of returning F1 0 silently.
- **`common/labels.py`**: complex dtypes are rejected instead of being cast with a warning while the imaginary part is
  discarded.
- **`common/stats.py`**: `finite_values` refuses 2D input instead of silently flattening (a transposed array reaching
  `pearson_r` used to correlate the wrong sample).
- **`common/paths.py`**: `raw_file` refuses names that escape `data/raw` (absolute or `..`).
- **`tools/check_all.py`, `data/make_manifest.py`**: check-harness fixes (not frozen): expected outputs are deleted
  before each producer runs, all non-model Fig 2 scorers now run in `make check`, unit tests are discovered per folder
  (recorded LLM-written `test_*.py` files in `runs/` no longer execute inside `make check`), the NaN scan covers
  `fig3/figure_v2`, `fig3/scoring` and `fig3/v2`, and the manifest verifies the recorded file sizes.


## Amendment: row D count corrections and protocol text (20 Oct 2026, authors' decision)

- **Three row-D counts were read wrongly by `score.parse_count`** (first number in the reply). Two nuclei replies on field 104
  (runs 1 and 3) gave the advice "an ERG, CD31 or VE-cadherin stain" before the estimate, and "CD31" was read as 31; one
  endothelial reply on field 104 (run 1) first mentions "roughly 100-120" other (round) cells. The operator's reading of
  these replies is stored in `v2/count_corrections.json` (nuclei run 1: 500, range 450-550; nuclei run 3: 600, range 500-700;
  endothelial run 1: 350, range 300-400); `score.py` applies it and refuses to run if the rule no longer gives the value
  recorded there. The other 15 replies were read by hand and the rule's value is correct. Replies, prompts and scenarios are
  unchanged. Changed scores (`runs/direct_three_turns_*` `score.json`, `turn1` only): 31 -> 500, 31 -> 600, 110 -> 350. The
  Fig. 3 row D dots for these three runs move accordingly.
- The **border rule** in `PROTOCOL_V2.md` section 2 now states what `scoring/tasks.py` does (endothelial: border objects removed
  from reference and prediction, so they affect count and F1), the header and model identifier were corrected, and a note
  records what the figure shows for rows A and D. No run was affected.
