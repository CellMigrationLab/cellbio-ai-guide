# Figure 3, protocol v2 (frozen 17 Oct 2026; revised 19 and 20 Oct 2026, see the notes below and `v2/FREEZE.json`)

Replaces the round-2 design. The runs made under round 2 (three accepted, three rejected) are a **pilot**, not used in the
figure (removed from the repository; git history). It was implemented in `fig3/v2/`, tested in a short preflight (section 11) and frozen on 17 Oct 2026 (hashes of every
file that defines the protocol, including the operator code and the environment).

Sources of the changes: the authors' plan of 17 Oct 2026, the amendments discussed in the session, and the two
ChatGPT audits of 17 Oct 2026 (pull request 2: round-2 plan re-audit and analysis-code audit).

---

> **Revision of 19 Oct 2026 (authors; rows B and C only; A and D unchanged).** The first 19 main runs showed that one
> development field and one test field make the comparison depend on how typical the test field is (on the DAPI field
> 209 every nuclei pipeline tuned on field 104 drew masks about twice the manual size: F1 0.55 against 0.96). Rows B and
> C therefore start again. The model is given **a mosaic of the left halves (x < 512) of fields 104 and 209** as its one
> development image (same size as a field, so the prompts and the answer sheet's image size stay true). Scripts and
> pipelines are run on the whole fields and **scored on the held-out right halves (x ≥ 512) of both fields**; the score
> is the **mean of the F1 on the two fields**, as in Figures 1 and 2 (same references and scorer; there on whole fields).
> The aim is a pipeline that works despite the diversity of the data. Superseded runs are kept in
> `v2/runs_superseded/` (never edited). Details in `deviations.md`. Below, "field 104 = development, field 209 = test"
> still holds for row D only (whole fields).

> **Amendment of 20 Oct 2026 (what was done and shown, after the runs; no run, prompt or scenario changed).**
> (1) The figure shows, for row A, one dot per reply (outdated model or code suggested, first-pass classification in
> `v2/advice_outdated.csv`) with verbatim quotes, not one illustrative reply per condition. (2) For row D it shows only the
> turn-1 count of each run per field against the manual count; the size and shape answers and the drawn ellipses were
> asked and recorded but are not shown (decision of the authors, `deviations.md`). (3) Row D counts: the first-number
> rule of `score.py` read "CD31" as 31 and a number for other cells as the count in three replies; they are corrected by the
> operator's reading of the reply in `v2/count_corrections.json` (`deviations.md`). (4) The border rule and the model
> identifier were corrected in sections 2 and 3, and the header above.

---

## 1. Question and what each row shows

What changes when a cell biologist uses an LLM (Claude) in four ways, on one family of tasks: **segment, count and
measure the shape (area and aspect ratio)** of three object types of increasing difficulty.

| Row | Use | Compared | Shown in the figure |
|---|---|---|---|
| A | Ask for advice | simple prompt vs Box 1 prompt | one illustrative reply per condition (chosen by the authors after the runs, stated as illustrative), with every named tool, function and parameter marked current / outdated / does not exist; counts of such items over all runs |
| B | Ask for code (the model writes, a separate runner runs) | simple prompt vs Box 1 prompt | the score of every script on the held-out halves of fields 104 and 209 and their mean, all tasks; crashed scripts as ×; one code excerpt (fixed rule) |
| C | Let an agent write, run and optimise on the development mosaic (left halves of fields 104 and 209) | by eye vs with labels (Box 1 in both) | score of every frozen pipeline re-run by the runner on fields 104 and 209 (held-out right halves) and their mean, all tasks; the score the agent reported vs ours |
| D | Ask for the answer directly | count → size and shape → ellipses drawn, count and shape from the drawing (one conversation per image), on field 104 and field 209 | stated vs manual count, stated vs measured size and shape, on both fields, one drawing (fixed rule) |

No statistical tests (3 replicates); every run is shown.

## 2. Tasks, images and references

| Task | Input | Objects (field 104 / 209) | Reference |
|---|---|---|---|
| Endothelial nuclei | DAPI (fluorescence) | 441 / 473 | manual nucleus labels |
| Cancer cells | brightfield | 124 / 163 | manual cell labels |
| Endothelial cells | brightfield | 382 / 388 complete cells | annotator 1 junction lines → cells (`lines_to_cells`) |

- **Rows B and C (revised 19 Oct 2026): development = mosaic of the left halves (x < 512) of fields 104 and 209**
  (given to models as image.tif, with its annotation when they ask, row B before the code is written, row C labels arm as
  the working annotation); **test = the right halves (x ≥ 512) of both fields**, whose annotations never reach a model.
  **Row D: whole fields** (104 and 209), unchanged.
- Pixel size 0.65 µm (exact value 0.649614 µm used in scoring).
- **Endothelial cells** are annotated on PECAM-1, a channel the model does not receive. The task stays (it is the hard
  task) and the legend says so; the human ceiling is the agreement between the two annotators (F1 0.90 on field 104;
  computed for field 209 before the runs).
- **Nuclei**: the reference contains endothelial nuclei only. Scoring rule `match_first`: predictions are matched to the
  full annotation first; only unmatched predictions lying > 30 % on annotated cancer cells are ignored.

### Measurement definitions (frozen)
- **Count**: number of objects in the label image (whole field).
- **Area**: pixel count × 0.649614² µm².
- **Aspect ratio (AR)**: major / minor axis length of the ellipse with the same second moments (scikit-image
  `regionprops`, `axis_major_length / axis_minor_length`); objects with a minor axis < 2 px are excluded from AR.
- Objects touching the image border are excluded from area and AR statistics. For the endothelial task they are also
  removed from the reference and from the prediction before counting and scoring (`scoring/tasks.py`), so they do
  affect the count and F1 of that task; for nuclei and cancer cells they are not removed (amendment of 20 Oct 2026).
- The same code computes these from the manual references and from every model output.

## 3. Subjects, isolation and environment

- **Subject model**: Claude via headless Claude Code sessions (`claude -p --restricted`), model `claude-sonnet-5-5` (recorded per
  run as the resolved model ID). The legend states that runs used Claude Code sessions, not the claude.ai app.
  (Changed from sub-agents before the preflight, authors' decision of 17 Oct 2026: a sub-agent inherits the operator
  session's project instructions, AGENTS.md, which describe this study, and its working directory, the repository.)
- **Fresh session per scenario** (new session ID), started in a neutral folder `/home/user/sessions_v2/vNNN` (named by
  run order only; preflight: `/home/user/sessions_v2_preflight/vNNN`), which contains only the files listed for that
  scenario. Follow-up turns resume the same session in the same folder. The operator session's environment variables
  that identify it (session ID, extra directories, messaging, synced skills, effort setting) are not passed on.
  The subject's context still contains the account's email address and commit-attribution lines, which come from the
  account and cannot be removed here (recorded in `deviations.md`).
- **Tools per row** (one machine-readable table, `v2/rows.csv`, used by the framing, the audit and the metadata):

  | Row | Tools offered | Framing sentence |
  |---|---|---|
  | A | web search | "You cannot run code." |
  | B | web search, view attachment | "You cannot run code; the user will run your script." |
  | C | web search, shell in its folder | "You can run shell commands in the folder <path> only." |
  | D | view attachment | "You cannot run code." (no web: the answer must come from the image) |

- **Enforcement**: each session is given only its row's tools (`--tools`, column `cli_tools` of `rows.csv`): A web
  search and fetch; B the same plus Read (to view the attachment); C Read, Write, Edit, Bash, Glob, Grep and web;
  D Read only (no web is possible). `--restricted` ignores user and project settings and confines the file tools to the
  subject folder. Row C's shell cannot be confined by the CLI: the framing sentence and the audit apply. Reads decide
  (authors' decision after the preflight): reading or listing anything outside the folder that could carry information
  (the repository, other subject folders, `/home/user`, data) is a protocol violation → rerun; reading installed
  software and the shared model cache is allowed; the subject's own temporary files (its session scratchpad, or files
  it writes and deletes in `/tmp`) are recorded in `audit.json` and archived where they still exist, not rerun.
- **Audit of every run** (`audit.json`): all tool calls; resolved paths checked with `Path.is_relative_to` against the
  subject folder; shell commands checked for paths outside it; any tool input that names this study, its authors or the repository
  is flagged (→ rerun). Each session has its own scratchpad; anything the subject leaves there is archived with the
  run. The operator session's scratchpad must be empty before each subject and untouched by it.
- **Environment**: Python 3.13, numpy/scipy/scikit-image/tifffile, torch 2.14.1+cpu, torchvision 0.29.1+cpu, Cellpose
  4.2.1.1 (cpsam_v2 weights pre-downloaded); `pip freeze` stored with the freeze. Packages a script needs are installed
  into a **per-run virtual environment** layered on the frozen base (`--system-site-packages`), so nothing persists
  between runs. A smoke test (import Cellpose, run it on a 256 px crop) runs before each batch.

## 4. Prompts

### 4.1 Task sentence (both conditions, all rows except D)
- Nuclei: "I want to segment and count the endothelial nuclei and measure their shape (area and aspect ratio) from
  widefield fluorescence images of a DAPI-stained endothelial monolayer (cancer cells sit on top)."
- Cancer cells: "I want to segment and count the cancer cells and measure their shape (area and aspect ratio) from
  brightfield images of cancer cells sitting on top of a confluent endothelial monolayer."
- Endothelial cells: "I want to segment and count the endothelial cells and measure their shape (area and aspect ratio)
  from brightfield images of a confluent endothelial monolayer (some cancer cells sit on top)."

### 4.2 Request sentence per row
- A: "Help me choose an analysis approach."
- B: "Help me write the analysis as a Python script. The image is image.tif; the script should read it from the working
  directory and save the label image as labels.tif and a table with one row per object (label, area in µm², aspect
  ratio) as measurements.csv."
- C: "Please write a Python script for this analysis, run it on image.tif in this folder, look at the result and improve
  the script until you are satisfied. Save the final script as pipeline.py so that it runs unchanged as
  `python pipeline.py <input.tif> <labels.tif> <measurements.csv>`, list any other file it needs in
  runtime_manifest.json, keep a log of each change in log.txt and report your final result."

### 4.3 Conditions
- **Simple (rows A, B)**: task sentence + request sentence.
- **Box 1 (rows A, B)**: the final Box 1 (`box1/box1_final.md`) with the slots filled as in the pilot (2D, axes,
  channel, uint16 12-bit, 0.65 µm, object size: nuclei 13–17 µm, cancer cells 15–25 µm, endothelial cells 25–50 µm;
  "Python 3.13 on a laptop CPU (no GPU)"; output = label image + table of areas and aspect ratios; "I can provide a
  manual annotation of this image (a label image)"), + the request sentence. The optimisation paragraph is omitted.
- **Row C, both arms**: Box 1 + the optimisation paragraph ("optimise only on image.tif …, read and write only inside
  this folder …") + the request sentence.
  - *With labels*: annotation.tif is in the folder and the Box 1 sentences mentioning the annotation stay.
  - *By eye*: no annotation; the three Box 1 phrases that mention an annotation ("I can provide a manual annotation…",
    "Include a test I can run on my annotated example…", "and its annotation" in the optimisation paragraph) are
    removed. These removed phrases are the only difference between the arms and are listed in the legend.
- **Row D** (no conditions; one conversation, three turns, the next turn sent after the reply):
  1. "How many [endothelial nuclei / cancer cells / endothelial cells] are in this image?"
  2. "What are their typical size and shape? Give the median area in µm² and the median aspect ratio. The pixel size is
     0.65 µm."
  3. "Please draw an ellipse around every [object] in this image and give, from your drawing, the count, the median
     area in µm² and the median aspect ratio. Give the ellipses as JSON in the pixel coordinates of the image (origin
     top-left, x to the right, y down): {"count": n, "median_area_um2": a, "median_aspect_ratio": r,
     "ellipses": [{"x": , "y": , "major": , "minor": , "angle_deg": }, ...]}" (major/minor = full axis lengths in px).

## 5. Rows: procedure and numbers

**A — advice.** 2 conditions × 3 tasks × 3 replicates = **18 runs**. No attachment. Every named software, model,
function, parameter and installation step in the reply is checked against the installed version or its current
documentation and classified: *current* / *outdated or renamed* / *does not exist* / *not possible in the stated setup*
(e.g. needs a GPU, a second channel); checks recorded per item with the source. The displayed example per condition
is chosen by the authors after the runs as the most useful illustration; the legend says it is illustrative, and the
item counts over all 18 runs and every reply are given (supplement and repository).

**B — code.** 2 conditions × 3 tasks × 3 replicates = **18 runs**. The subject sees image.png (preview of the development mosaic;
image.tif is named in the prompt as the user's file). If it asks for the image or an annotation **before it has given
code**, it receives the annotation of the development mosaic (PNG and TIFF) with the answer-sheet sentence; requests after the code
are answered "I don't know". The final script is saved as returned: the latest complete script (the latest Python
block naming both `labels.tif` and `measurements.csv`); partial edits sent after it are not applied (recorded per
run, authors' decision after the preflight). The **scripted runner** (`v2/runner.py`; authors' decision) runs it twice, unchanged except input/output paths (diff stored):
on the whole of field 104 and of field 209 (scored on their right halves), in a fresh per-run environment, installing only packages the reply names, 1 h limit.

**C — optimise.** 2 arms × 3 tasks × 3 replicates = **18 runs**. Working folder with image.tif (the development mosaic), plus
annotation.tif in the labels arm. When the agent finishes, its folder is archived; `pipeline.py` is then run unchanged
in a **clean folder** containing only the input image, `pipeline.py` and the files listed in
`runtime_manifest.json` (the development image and annotation are never copied). The agent's own reported score is
recorded. The **runner** (the same one as row B) then runs the frozen `pipeline.py` unchanged, twice, each time in a
clean folder containing only the input image, `pipeline.py` and the files listed in `runtime_manifest.json`: on field
104 and on field 209 (whole fields; the annotation is not copied). Both are scored with our scorer on the held-out right
halves; the agent's own reported score is compared with our mean held-out F1.

**D — direct answers.** 3 tasks × 2 fields × 3 replicates = **18 conversations**, one conversation per image (PNG,
full field), field 104 and field 209 in separate fresh conversations. Field 104 doubles the number of images (direct
answers are not optimised on anything, so both fields are test images for this row) and shows whether behaviour is
consistent across two images.

**Total: 72 subject runs** (+ 72 runner executions: 36 for row B and 36 for row C, each script or pipeline on fields 104 and 209). Run order randomised with a fixed seed; all within 3 days.

## 6. Answers to follow-up questions (answer sheet v2)
Answer only what is asked, verbatim, at most 3 replies; "I don't know" otherwise. Only explicit questions are answered
(a sentence ending in "?", or a list headed as questions); conditional offers ("If you tell me X, I can ...") get no
reply (authors' decision after the preflight). New or changed lines:
- Cancer cells: "They are rounded and sit on top of the endothelial monolayer; touching cells should be counted
  individually."
- Endothelial nuclei: "Only the endothelial nuclei. The nuclei of the cancer cells are brighter and rounder in DAPI."
  (Checked on the data: DAPI objects inside cancer cells are 1.8–2.7× brighter, aspect ratio about 1.2 vs 1.4–1.5;
  they are not consistently smaller, so size is not mentioned.)
- Endothelial cells: "Count them as whole cells; their outline follows the cell junctions, including the part under
  the cancer cells."
- Image / annotation request: row B before code and row C (labels arm): field-104 files; row A: "I don't have an
  example image to share in this conversation."; rows B after code, D: "I don't know." / "I'd rather you work from the
  image."
- Aspect ratio definition, if asked: "Major axis divided by minor axis of the fitted ellipse."
- The image-size line no longer mentions a PNG preview in rows without an attachment.
Whether a hint was given is recorded per run (it is part of what Box 1 changes, and is reported).

## 7. Scoring

All label images pass one strict validator (`common/labels.py`): 2D, expected shape, finite, non-negative,
integer-valued, within uint16/uint32 range; otherwise status `invalid_labels` (scored 0, shown as ×).

| Row | Primary | Secondary |
|---|---|---|
| B | mean over fields 104 and 209 of the object F1 (IoU ≥ 0.5) on the held-out right half; each field separately | runs unchanged (yes / after installing / no); count error; median area and AR vs reference (% / absolute); per matched object area and AR error; measurements.csv present, one row per label, area and AR agree with the label image (±2 % / ±0.05) |
| C | as B | as B, + agent-reported score vs our mean held-out F1; files used at test time |
| D | count error (turn 1), each field | turn 2 area and AR vs reference medians; turn 3 ellipses: centres matched one-to-one to reference objects (centre inside an object, Hungarian on distance) → F1; count and shape from the drawing vs the reference and vs turns 1–2 |
| A | items classified (section 5) | — |

**Execution status** (`execution.json`: command, exit code, timeout, runtime) is primary: a script that exits non-zero
or times out is `crashed` even if it wrote a file (that file may be scored only as a labelled secondary diagnostic).

## 8. Figure layout (fixed before the runs)
- Row A: two reply excerpts (simple, Box 1), chosen after the runs as illustrations, with items colour-coded; bar or
  table of item classes over all 18 runs.
- Row B: per task, bar = median over runs of the mean F1 of fields 104 and 209 (held-out halves) per condition, circles =
  runs (as the mean; each field's F1 in the supplement), × for crashes; one code excerpt: the Box 1 cancer-cell script
  with the median mean F1 among those that ran.
- Row C: as B, by eye vs with labels; marker for the agent's own claim.
- Row D: per task and field, stated count (turn 1) and drawn count (turn 3) vs manual; shape from turn 2 and turn 3 vs
  reference; one ellipse overlay: the field-209 cancer-cell replicate with the median count error.
- Supplementary table: every run with every measure; every conversation and script in the repository.

## 9. Rerun policy (fixed)
Rerun: operator error, corrupted or missing attachment, harness or shared-environment fault verified independently of
the model's code (e.g. the torchvision mismatch), API or rate-limit interruption, subject access to forbidden files.
Never rerun: code that does not run, missing or invented packages or functions, wrong output format, refusal, timeout,
poor result. Every attempt is archived; the reason is written before the new attempt is started.

## 10. Code fixes before the preflight (from the code audit)
Strict label validation everywhere a label image is read for scoring; `execution.json` and process-group timeout;
measurements.csv checks; one source for pixel size and image metadata; quarantine of exploratory Fig. 1 scripts that
duplicate logic or write canonical outputs; explicit errors instead of `None`/blank for required values; JSON written
with `allow_nan=False`; empty-input guards in statistics.

## 11. Preflight and freeze
One run per row × task (≈ 12 runs, not used in the figure) to test the harness, output formats and the runner. Then
freeze protocol v2: hashes of prompts, answer sheet, rows.csv, operator, runner, scorer, environment (`pip freeze`),
this file and the figure layout; a test fails if any changes. Changes after the freeze go to `deviations.md` with the
affected runs.

## 12. Figures 1 and 2 (separate from Figure 3) — done 17 Oct 2026
- Fig. 1: no change (step 4 already uses field 209).
- Fig. 2a: every variant re-run on field 209 with the settings chosen on field 104; bars show the mean F1 of the two
  fields, dots each field (default 0.59, post-filter 0.86; `fig2/code/score_fields.py`).
- Fig. 2c (denoising): unchanged; the high-SNR comparison stays exploratory (`fig2/analysis/`).
- Fig. 2e (tubule width): orientation-neutral sampling on the reference skeleton, exclusions counted; 1,301 locations,
  prediction minus reference −9 nm.
- Code-audit P0 items and inexpensive P1 items done; `make check` and `make full` pass; every changed number is
  documented in the figure README.

## 13. Decisions (authors, 17 Oct 2026) and open items
- Row A example: chosen after the runs, as an illustration (not by a rule); all replies are available.
- Runner for rows B and C: scripted runner.
- Row D: full field.
- Row A item check: done by the operator, one table per reply with the source of each classification (installed
  version or documentation link), reviewed by the authors before use.
- Preflight: one run per row × task (12 runs), not used in the figure.
- Subjects are headless Claude Code sessions started in their own folders, not sub-agents (decided before the
  preflight, after a probe showed that sub-agents receive AGENTS.md and the repository as working directory); row D
  is given Read only; row C is confined by framing and audit; the account email and attribution lines in the
  subject's context are accepted and recorded, and web searches naming the study or its authors are flagged.
- After the preflight: row C reads decide (section 3); row B runs the latest complete script (section 5); only explicit
  questions are answered (section 6); the authors' public cancer-cell dataset and StarDist model (Zenodo 10572122,
  found by a preflight subject through ordinary searches) may be used; each run records whether the subject found or
  used it, and a row B or C script that uses it is marked in the figure.
- Open: annotator names, tool and dates for both fields (needed for the methods, not for the runs).
