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
- **Fig. 3** what changes when a cell biologist uses an LLM in different ways, on three tasks of increasing difficulty
  (nuclei in DAPI, cancer cells in brightfield, endothelial cells in brightfield), all scored against manual annotation:
  - `fig3/advice/` ask for advice (from memory vs after checking the documentation);
  - `fig3/code/` ask for code (generic request vs Box 1; Fiji macro and Python);
  - `fig3/optimise/` let an agent run and optimise the analysis (judging by eye vs scored against annotation, then
    frozen and tested on a held-out half);
  - `fig3/direct_answers/` ask for the answer directly (count only vs draw outlines and count).

## Current status (17 Oct 2026)
- Figures 1 and 2 are final; Figure 3 is a late draft (`fig3/figure/output/fig3_preview.png`).
- `make check` passes: all figures rebuild byte-identical; all scores reproduce from the stored data.
- Next steps:
  1. An independent session checks that the figures can be rebuilt from a fresh clone.
  2. An independent model (ChatGPT) adversarially audits the repository; findings go to `docs/audit_findings.md`.
  3. Figure 3 round 2 (start from zero with the final Box 1): see `fig3/STRATEGY.md`. If you are asked to act as an
     **operator** for these runs, never show this repository to the model being tested (STRATEGY section 4b).

## Working rules (the same practices Box 1 asks of an LLM)
- **Never modify `data/raw/`.** Checksums are in `data/manifest.csv`; `make data` verifies them.
- **Keep provenance.** Every file in `*/source_data/` must be produced by a script in `*/code/` (or a recovered command in
  `*/code/recovered_inline/`, kept verbatim). If you change how something is made, change the script, not the output.
- **Use documented, maintained software**, check its current documentation, and state the version you used.
- **Make processing explicit**: name parameters, state defaults, resizing, normalisation and post-processing; keep the
  original coordinate system and physical units.
- **Small functions, clear names, validated inputs, informative errors, no silent fallbacks.** New code imports paths
  from `common.paths` and scoring from `common.matching`; never hard-code absolute paths.
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
