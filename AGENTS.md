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
- **Fig. 3** what changes when a cell biologist uses an LLM (Claude) in four ways, on three tasks of increasing
  difficulty (endothelial nuclei in DAPI, cancer cells and endothelial cells in brightfield: segment, count, area and
  aspect ratio), scored against manual annotation on a development field (104) and a test field (209):
  A advice (simple prompt vs Box 1), B code written by the model and run by us (simple vs Box 1), C an agent that writes,
  runs and optimises (by eye vs with labels), D direct answers (count, size and shape, ellipses drawn).
  Plan: `fig3/PROTOCOL_V2.md`; harness: `fig3/v2/`. The current draft figure is round 1 (`fig3/advice/`, `code/`,
  `optimise/`, `direct_answers/`), which v2 replaces.

## Current status (17 Oct 2026)
- Figure 1 is final. Figure 2 was updated on 17 Oct 2026 after the code audit (panel e sampling; panel a scored on
  two fields). Figure 3: the round-1 draft (`fig3/figure/output/fig3_preview.png`) is to be replaced by protocol v2.
- `make check` passes: all figures rebuild byte-identical; all scores reproduce from the stored data.
- `make full` passes: the Figure 1 and 2 source data regenerate from `data/raw` and rebuild both figures byte-identical
  (files it cannot regenerate are listed with the reason).
- Figure 3, protocol v2: preflight done (12 runs, `fig3/v2/runs_preflight/`, not used in the figure); protocol frozen on
  17 Oct 2026 (`fig3/v2/FREEZE.json`, subject model `claude-sonnet-5-5` as headless Claude Code sessions); the 72 main
  runs go to `fig3/v2/runs/`, one commit per scenario. To resume an interrupted main run, start from
  `fig3/v2/RESUME_PROMPT.md`. If you run scenarios, never show this repository to the model being tested (subjects
  are started only by `fig3/v2/run_operator.py start`, never as sub-agents, which would receive this file).

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
- **LLM runs are records.** Do not edit transcripts or LLM-written code in `fig3/*/runs/`; put any corrected copy next to
  it and say what changed.
- **Report honestly**: if something cannot be reproduced, say so in the README of that figure.

## Layout conventions
`figX/code/` scripts are run with the working directory `figX/source_data/` and `PYTHONPATH` set to the repository root
(the Makefile does this). Builders write to `figX/figure/` (Fig. 3: `fig3/figure/output/`).

## Path placeholders in records
Transcripts, logs and recovered commands (`*/code/recovered_inline/`) keep their
original commands; local folder prefixes were replaced by placeholders: `<work>` and `<work2>` (the two working folders;
`<fig3-work>` = `<work>/fig3`), `<uploads>` (the raw files, now `data/raw/` under the names in `data/raw_name_map.csv`),
`<tasks>`, `<transcript>`, `<transcript2>` (session records, not included).
