# Figure 3, protocol v2 (draft for the authors' review, 17 Oct 2026)

Replaces the round-2 design. The runs made under round 2 (three accepted, three rejected) are a **pilot**, kept in
`superseded/round2_pilot/` and not used in the figure. Nothing in this file is frozen yet; after the authors' review it is
implemented in `fig3/v2/`, tested in a short preflight (section 11) and then frozen (hashes of every file that defines
the protocol, including the operator code and the environment).

Sources of the changes: the authors' plan of 17 Oct 2026, the amendments discussed in the session, and the two
ChatGPT audits of 17 Oct 2026 (pull request 2: round-2 plan re-audit and analysis-code audit).

---

## 1. Question and what each row shows

What changes when a cell biologist uses an LLM (Claude) in four ways, on one family of tasks: **segment, count and
measure the shape (area and aspect ratio)** of three object types of increasing difficulty.

| Row | Use | Compared | Shown in the figure |
|---|---|---|---|
| A | Ask for advice | simple prompt vs Box 1 prompt | one illustrative reply per condition (chosen by the authors after the runs, stated as illustrative), with every named tool, function and parameter marked current / outdated / does not exist; counts of such items over all runs |
| B | Ask for code (the model writes, a separate runner runs) | simple prompt vs Box 1 prompt | the score of every script on field 104 (development) and field 209 (test), all tasks; crashed scripts as ×; one code excerpt (fixed rule) |
| C | Let an agent write, run and optimise on field 104 | by eye vs with labels (Box 1 in both) | score of every frozen pipeline re-run by the runner on field 104 and field 209, all tasks; the score the agent reported vs ours |
| D | Ask for the answer directly | count → size and shape → ellipses drawn, count and shape from the drawing (one conversation per image), on field 104 and field 209 | stated vs manual count, stated vs measured size and shape, on both fields, one drawing (fixed rule) |

No statistical tests (3 replicates); every run is shown.

## 2. Tasks, images and references

| Task | Input | Objects (field 104 / 209) | Reference |
|---|---|---|---|
| Endothelial nuclei | DAPI (fluorescence) | 441 / 473 | manual nucleus labels |
| Cancer cells | brightfield | 124 / 163 | manual cell labels |
| Endothelial cells | brightfield | 382 / 388 complete cells | annotator 1 junction lines → cells (`lines_to_cells`) |

- **Field 104 = development** (given to models when they ask, row B before the code is written, row C as the working
  image). **Field 209 = test**; its annotations never reach a model.
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
- Objects touching the image border are excluded from area and AR statistics (not from counts or F1).
- The same code computes these from the manual references and from every model output.

## 3. Subjects, isolation and environment

- **Subject model**: Claude via Claude Code sub-agents, model `sonnet` (recorded per run as the resolved model ID).
  The legend states that runs used Claude Code sub-agents, not the claude.ai app.
- **Fresh sub-agent per scenario**, started from a neutral folder `/home/user/sessions/sNNN` (named by run order only),
  which contains only the files listed for that scenario.
- **Tools per row** (one machine-readable table, `v2/rows.csv`, used by the framing, the audit and the metadata):

  | Row | Tools offered | Framing sentence |
  |---|---|---|
  | A | web search, view attachment | "You cannot run code." |
  | B | web search, view attachment | "You cannot run code; the user will run your script." |
  | C | web search, shell in its folder | "You can run shell commands in the folder <path> only." |
  | D | view attachment | "You cannot run code." (no web: the answer must come from the image) |

- **Enforcement**: rows A, B and D use a custom sub-agent definition with only the tools above (no shell, no file
  writing). If the session's permission policy blocks creating it, the authors are asked to allow it; the fallback is
  the framing sentence plus the transcript audit, and any shell use in A, B or D is a protocol violation → rerun.
- **Audit of every run** (`audit.json`): all tool calls; resolved paths checked with `Path.is_relative_to` against the
  subject folder; shell commands checked for paths outside it. The harness scratchpad is emptied before each subject
  and anything the subject leaves there is archived with the run.
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

**B — code.** 2 conditions × 3 tasks × 3 replicates = **18 runs**. The subject sees image.png (preview of field 104;
image.tif is named in the prompt as the user's file). If it asks for the image or an annotation **before it has given
code**, it receives field 104 (image TIFF/PNG, annotation PNG) with the answer-sheet sentence; requests after the code
are answered "I don't know". The final script is saved as returned. The **scripted runner** (`v2/runner.py`; authors' decision) runs it twice, unchanged except input/output paths (diff stored):
on field 104 and on field 209, in a fresh per-run environment, installing only packages the reply names, 1 h limit.

**C — optimise.** 2 arms × 3 tasks × 3 replicates = **18 runs**. Working folder with image.tif (field 104), plus
annotation.tif in the labels arm. When the agent finishes, its folder is archived; `pipeline.py` is then run unchanged
in a **clean folder** containing only the field-209 image, `pipeline.py` and the files listed in
`runtime_manifest.json` (the field-104 image and annotation are never copied). The agent's own reported score is
recorded. The **runner** (the same one as row B) then runs the frozen `pipeline.py` unchanged, twice, each time in a
clean folder containing only the input image, `pipeline.py` and the files listed in `runtime_manifest.json`: on field
104 (the image the agent optimised on; the annotation is not copied) and on field 209. Both are scored with our scorer;
the agent's own field-104 claim is compared with our field-104 score.

**D — direct answers.** 3 tasks × 2 fields × 3 replicates = **18 conversations**, one conversation per image (PNG,
full field), field 104 and field 209 in separate fresh conversations. Field 104 doubles the number of images (direct
answers are not optimised on anything, so both fields are test images for this row) and shows whether behaviour is
consistent across two images.

**Total: 72 subject runs** (+ 72 runner executions: 36 for row B and 36 for row C, each script or pipeline on fields 104 and 209). Run order randomised with a fixed seed; all within 3 days.

## 6. Answers to follow-up questions (answer sheet v2)
Answer only what is asked, verbatim, at most 3 replies; "I don't know" otherwise. New or changed lines:
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
| B | object F1 (IoU ≥ 0.5) on field 209; same on field 104 | runs unchanged (yes / after installing / no); count error; median area and AR vs reference (% / absolute); per matched object area and AR error; measurements.csv present, one row per label, area and AR agree with the label image (±2 % / ±0.05) |
| C | object F1 on field 209; same on field 104 | as B, + agent-reported score vs our field-104 score; files used at test time |
| D | count error (turn 1), each field | turn 2 area and AR vs reference medians; turn 3 ellipses: centres matched one-to-one to reference objects (centre inside an object, Hungarian on distance) → F1; count and shape from the drawing vs the reference and vs turns 1–2 |
| A | items classified (section 5) | — |

**Execution status** (`execution.json`: command, exit code, timeout, runtime) is primary: a script that exits non-zero
or times out is `crashed` even if it wrote a file (that file may be scored only as a labelled secondary diagnostic).

## 8. Figure layout (fixed before the runs)
- Row A: two reply excerpts (simple, Box 1), chosen after the runs as illustrations, with items colour-coded; bar or
  table of item classes over all 18 runs.
- Row B: per task, two columns of dots per condition (field 104, field 209), 3 runs each, × for crashes; one code
  excerpt: the Box 1 cancer-cell script with the median field-209 F1 among those that ran.
- Row C: per task, F1 per run on field 104 and field 209 for by eye vs with labels; marker for the agent's own claim.
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

## 12. Figures 1 and 2 (separate from Figure 3)
- Fig. 1: no change (step 4 already uses field 209).
- Fig. 2a: add to the legend: "With the same settings on a second field, F1 is 0.40 (default) and 0.81 (with the
  post-filter)." (computed 17 Oct 2026, Cellpose-SAM default, contrast threshold 50 frozen on field 104).
- Fig. 2c (denoising): unchanged.
- Fig. 2e (tubule width): sampling fixed (orientation-neutral spacing along reference skeletons, exclusions counted);
  panel numbers and legend recomputed.
- Code-audit P0 items and inexpensive P1 items for Figs. 1–2, keeping `make check` and `make full` green and
  documenting any number that changes.

## 13. Decisions (authors, 17 Oct 2026) and open items
- Row A example: chosen after the runs, as an illustration (not by a rule); all replies are available.
- Runner for rows B and C: scripted runner.
- Row D: full field.
- Open: annotator names, tool and dates for both fields (needed for the methods, not for the runs).
