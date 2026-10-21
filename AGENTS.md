# AGENTS.md: purpose of this repository and how to work in it

Read this first, whether you are a person or an AI agent (Claude Code, ChatGPT, Codex, ...).

## Purpose
This repository holds everything used to make Figures 1–3 of *The cell biologist's guide to AI-assisted image analysis*
(Gómez-de-Mariscal, Henriques & Jacquemet): raw data, the code that processed it, the code that scored the results and
drew the figures, and, for Figure 3, every prompt, reply and output of the LLM runs. The aim is that anyone can
**audit** the figures: trace each number to its source, rebuild it, and look for mistakes.

## What the figures show
- **Fig. 1** uses of AI in microscopy and how to start a project (illustrative panels; some panels are not recorded
  results, see `fig1/README.md`).
- **Fig. 2** is the deep-learning output good enough for the measurement? (Cellpose perturbations, denoising,
  artificial labelling, super-resolution with SQUIRREL).
- **Fig. 3** what changes when a cell biologist uses an LLM (Claude Sonnet 5.5) in four ways, on three tasks of increasing
  difficulty (endothelial nuclei in DAPI, cancer cells and endothelial cells in brightfield: segment, count, area and
  aspect ratio), scored against manual annotation: A advice (basic prompt vs a detailed prompt, the "Box 1" checklist),
  B code written by the model and run by us (basic vs detailed), C an agent that writes, runs and optimises (by eye vs
  with the annotation), D direct answers (count; size and shape and drawn ellipses were also asked but are not in the
  figure). Rows B and C: the model gets a mosaic of the left halves of fields 104 and 209 and is scored on the right halves
  of both (mean F1); rows A and D use whole fields. Plan: `fig3/PROTOCOL_V2.md`; harness: `fig3/v2/`; figure:
  `fig3/figure_v2/` (`make fig3`). The superseded round-1 draft was removed on
  19 Oct 2026 (it is in git history).

## Current status (21 Oct 2026)
- **All three figures are final (signed off by the authors, 20 Oct 2026); the article was finalised on 21 Oct 2026 and the
  attribution in `CITATION.cff`, `data/sources.csv` and the READMEs was aligned with it.** Figure 2 was updated on 17 Oct 2026 after the code
  audit (panel e sampling; panel a scored on two fields); on 20–21 Oct 2026 Figures 1 and 2 were tightened horizontally,
  Figure 1's panel letters set in lower case and Figure 3 laid out as a full-page portrait. Figure 3: all 72 protocol-v2 main
  runs are recorded (`fig3/v2/runs/`), 54 are scored (rows B, C and D) and the 18 row-A runs are classified rather than
  scored; the figure is in `fig3/figure_v2/` (`output/fig3_v2.svg`, `.png`, `.pdf`; the legends of all figures are in the
  article, not here). On 21 Oct 2026 the repository was reduced to what the figures need (records, analyses and drafts that no
  figure uses were removed; they are in git history).
- `make check` passes: all figure SVGs rebuild byte-identical; all scores reproduce from the stored data (Fig. 3). `make full` passes for Figures 1 and 2 (files it cannot regenerate are listed with the reason).
- Figure 3, protocol v2: protocol frozen on 17 Oct 2026 (`fig3/v2/FREEZE.json`, subject model `claude-sonnet-5-5` as headless
  Claude Code sessions), revised for rows B and C on 19 Oct 2026 (development mosaic, held-out halves, answer-sheet lines) and
  the harness hardened on 20 Oct 2026. Every change to a frozen file since the freeze is an amendment entry in `FREEZE.json`
  (old and new hash, reason, runs affected) with a matching section in `fig3/deviations.md`; `fig3/tests/test_v2_freeze.py`
  fails if a frozen file changes without one. Only the 72 accepted runs are
  kept (`fig3/v2/runs/`); the preflight, rejected and superseded runs were removed from the working tree on 21 Oct 2026 and
  are in git history (`fig3/deviations.md` describes them). Files over 50 MB are listed in `LARGE_FILES.json` and stored
  outside git (`fig3/v2/large_files.py`).
  If you run scenarios again, never show this repository to the model being tested (subjects are started only by
  `fig3/v2/run_operator.py start`, never as sub-agents, which would receive this file) and start each in its own
  process namespace.

## Working rules (the same practices Box 1 asks of an LLM)
- **Never modify `data/raw/`.** Checksums are in `data/manifest.csv`; `make data` verifies them.
- **Keep provenance.** Every file in `*/source_data/` must be produced by a script in `*/code/` (or a recovered command in
  `*/code/recovered_inline/`, kept verbatim). If you change how something is made, change the script, not the output.
- **Use documented, maintained software**, check its current documentation, and state the version you used.
- **Make processing explicit**: name parameters, state defaults, resizing, normalisation and post-processing; keep the
  original coordinate system and physical units.
- **Small functions, clear names, validated inputs, informative errors, no silent fallbacks.** New code uses the
  shared modules: `common.paths` (paths), `common.labels` (strict reading of label images), `common.matching`
  (matching and F1), `common.annotations` (junction lines to cells), `common.pix2pix` (registered pix2pix rows),
  `common.metadata` (pixel sizes), `common.stats` (no NaN results); never hard-code absolute paths, never write NaN.
- **Always score against the authors' manual annotations** in `data/raw/` (never against a model output or a derived
  copy you cannot trace to them). If you are unsure which file is the manual annotation, or it seems wrong or
  incomplete, stop and ask the authors to provide it again.
- **Test against reference data.** Any change must keep `make check` passing, or the change must explain, in the same
  commit, why a number changed.
- **Record deviations** (anything that departed from the stated protocol) in the relevant `deviations.md`.
- **LLM runs are records.** Do not edit transcripts or LLM-written code in `fig3/v2/runs/`; put any corrected copy next to
  it and say what changed (as `v2/count_corrections.json` does for three misread counts).
- **Report honestly**: if something cannot be reproduced, say so in the README of that figure.

## Layout conventions
`figX/code/` scripts are run with the working directory `figX/source_data/` and `PYTHONPATH` set to the repository root
(the Makefile does this). Builders write to `figX/figure/` (Fig. 3: `fig3/figure_v2/output/`).

## Path placeholders in records
Transcripts, logs and recovered commands (`*/code/recovered_inline/`) keep their
original commands; local folder prefixes were replaced by placeholders: `<work>` and `<work2>` (the two working folders;
`<fig3-work>` = `<work>/fig3`), `<uploads>` (the raw files, now `data/raw/` under the names in `data/raw_name_map.csv`),
`<tasks>`, `<transcript>`, `<transcript2>` (session records, not included). The protocol-v2 run records (`fig3/v2/runs*/`)
keep the real paths of the operator's throwaway cloud container (`/home/user/sessions_v2/`, `/home/user/r2exec_v2/`,
`/home/user/large_files_archive/`); they contain no personal data.
