# Companion repository for Figures 1–3: adversarial audit, structure, name

Paper: *The cell biologist's guide to AI-assisted image analysis* (Gómez-de-Mariscal, Henriques & Jacquemet).
Goal: a reader can (1) see where every pixel and number in Figs 1–3 comes from, (2) rebuild the figures and the
scores, (3) reuse Box 1 and the prompts, and (4) audit the LLM experiments, including the runs we did not show.

## 1. Adversarial audit: what a critical reviewer would look for, and what the repo must hold to answer it

| # | Attack | Risk today | What the repo must contain |
|---|---|---|---|
| 1 | "The LLM results are cherry-picked." | Fig 3 shows medians of 3 runs; several earlier rounds (v1–v5, old Box 1 wording, interrupted agents) were superseded. | **Every** run, shown or not, with a one-line reason for anything superseded (`fig3/superseded/README.md`); `all_runs.csv` with one row per run; the prompt pack committed and tagged **before** the ChatGPT/claude.ai round is collected (timestamped protocol). |
| 2 | "The prompts are not what you say." | Sub-agent runs carried a wrapper ("Act as a helpful assistant… you cannot run code… put the code in ONE block… save labels.tif") and a setup line not in Box 1. | Verbatim `prompt.md` **including the wrapper**, `framing.md` explaining why each line was added, and the conversation file with every follow-up answer. |
| 3 | "The model could not search; your 'check the docs' test is an artefact." | In the Claude Code harness the web tools must be loaded first; most agents never did; one said it had no web access. | `meta.json` per run with tools available and tools used (searches listed); a stated limitation; the chat-app round (web search state recorded) as the main test. |
| 4 | "Follow-up answers steered the model." | We answered questions; one answer was wrong (endothelial cells under cancer cells) and was corrected mid-round. | `answer_sheet.md` (versioned, with the correction), a rule that only asked questions are answered, and each run's answers verbatim. |
| 5 | "The code was fixed by you." | Fiji macros had input/output paths replaced; turn-2 scripts were extracted from later turns. | Code stored exactly as returned (`code_as_returned.*`) plus the run copy and a diff (`EDITS.md`); run log of the unchanged run; packages we installed. |
| 6 | "Agents had access to the test data / wrote outside the sandbox." | Three of six agent runs wrote outside their folder. | Agent transcripts, file listings before/after, the held-out split code, the frozen `pipeline.py`, the held-out run log; `deviations.md` listing the sandbox escapes. |
| 7 | "Scores depend on undocumented scoring choices." | Nuclei: objects on cancer cells ignored; endothelial: border objects removed; row c on the held-out half. | One shared, tested scoring package (`common/`), per-task YAML (annotation, conventions, counts), and unit tests (synthetic discs, known F1). |
| 8 | "The ground truth is weak." | One field; single annotator for nuclei and cancer cells; endothelial annotation drawn from PECAM-1. | Annotation files, annotator/tool/date, the two endothelial annotations and their agreement (F1 0.90), the lines-to-cells conversion code. |
| 9 | "Fig 1 panels look like results but are illustrative." | Fig 1b prompts/replies were written for the figure; Fig 1c steps 2–4 use one field. | Fig 1 README with the existing two caveats on top, and an explicit "illustrative, not recorded" note for panel b. |
| 10 | "You redistribute data you do not own." | Third-party data (DeepBacs CC BY 4.0, BioSR, CARE data provided by authors, TrackMate capture) and unpublished lab images (HPMEC perfusion). | Do not re-host third-party raw data: `data/fetch.py` downloads from the DOI and checks sha256. Lab data on Zenodo with a licence decided by the authors. `data/manifest.csv` with source, DOI, licence, permission status for every file. |
| 11 | "It does not rebuild." | Scripts use absolute `/tmp/...` paths and upload hash names (e.g. `e752a357-104_2.tif`); several figure versions exist. | Repo-relative paths; a name map (upload name → dataset name); pinned environment (Cellpose 4.2.1.1, torch, scikit-image, NanoPyx, Fiji build date); `make fig1|fig2|fig3|check`; CI that rebuilds the SVGs and checks every number in the legends against `source_data`. |
| 12 | "Models in Figs 1–2 cannot be checked." | StarDist custom model, pix2pix, CARE, RCAN outputs were used without re-running. | Model DOIs/weights links, the exact outputs used, and the statement "published predictions, not re-run". |
| 13 | "Leaks." | 87 exported transcripts contain sandbox paths; uploads carry session IDs. | Path scrubbing script (replace with `<workdir>`), check for e-mail addresses/tokens before the first push; keep repo private until submission. |
| 14 | "Results look like a benchmark." | Small n, one field, one model per vendor. | README and each figure README open with the scope: illustration, one field, N runs, date-stamped model versions. |
| 15 | "Box 1 is the product, but hard to reuse." | Box 1 text lives in the manuscript only. | `box1/` with the final text, a fill-in template, the three filled examples and the generic counterparts, ready to copy. |

Size check: working folders are ~1.9 GB in total (Fig 3 alone 561 MB, mostly label images and Cellpose outputs).
Keep the git repo below ~100 MB (code, prompts, transcripts, JSON scores, small PNG/JSON source data);
put raw images, all label images and model outputs on Zenodo (one record, versioned with the repo tag).

## 2. Proposed structure

```
ai-image-analysis-guide/
├── README.md                  scope, how to rebuild, caveats, citation, link to Zenodo
├── LICENSE                    code: MIT
├── LICENSE-content.md         text, prompts, transcripts, figures: CC BY 4.0; data: per source (see manifest)
├── CITATION.cff
├── Makefile                   make env | data | fig1 | fig2 | fig3 | check
├── environment/
│   ├── environment.yml        python, cellpose 4.2.1.1, torch (CPU), scikit-image, tifffile, nanopyx, stardist …
│   ├── requirements-lock.txt
│   └── fiji.md                Fiji build/date, no update sites, headless command
├── data/
│   ├── README.md              data cards (pixel size, channels, dims, acquisition, annotator)
│   ├── manifest.csv           file · source · DOI · licence · permission · sha256 · used in
│   ├── fetch.py               downloads Zenodo + third-party data into data/raw/, verifies sha256
│   └── annotations/           manual labels (or fetched from Zenodo), annotation notes
├── common/                    shared package
│   ├── io.py  matching.py  scoring.py  render.py (SVG helpers)  heldout.py
│   └── tests/                 synthetic-disc and known-F1 tests
├── box1/
│   ├── box1.md                final Box 1 text
│   ├── template.md            fill-in version
│   └── examples/              nuclei / cancer / endothelial, advice and code, generic and Box 1
├── fig1/  fig2/               README.md (provenance tables + caveats) · legend.md · scripts/ (numbered, run order)
│                              · source_data/ · make_figure.py · figure/ (svg, pdf, png)
├── fig3/
│   ├── README.md              rows a–d, what each tests, limitations
│   ├── legend.md  make_figure.py  figure/
│   ├── tasks/                 nuclei.yml cancer.yml endothelial.yml (image, annotation, scoring conventions)
│   ├── protocol/              PROTOCOL.md · answer_sheet.md (versioned) · framing.md (sub-agent wrapper) · agent_sandbox.md
│   ├── runs/<row>_<assistant>_<use>_<prompt>_<task>_r<k>/
│   │       prompt.md · conversation.md · meta.json · code_as_returned.* · code_run.* · EDITS.md
│   │       run.log · score.json · complexity.json   (labels.tif on Zenodo)
│   ├── summary/all_runs.csv   one row per run (row, assistant, model, date, condition, task, F1, n, crashed, notes)
│   ├── superseded/            earlier rounds + README (why superseded)
│   └── deviations.md
└── docs/
    ├── CHANGELOG.md           figure decisions (e.g. switched to three tasks, Box 1 wording v1 → v3)
    └── audit.md               this audit, updated before submission
```

Conventions: one script per step, numbered (`01_export_window.py`, …); every script reads `data/` and writes
`source_data/` with relative paths; every number in a legend is produced by a script and checked by `make check`.

## 3. Name

Recommended: **`ai-image-analysis-guide`** (matches the paper title, short, searchable).
Alternatives: `cellbio-ai-guide`, `ai-microscopy-guide-figures`, `llm-bioimage-analysis` (narrower, Fig 3 only).
Zenodo record: "Data and code for *The cell biologist's guide to AI-assisted image analysis*".

## 4. Steps
1. Decide hosting (lab GitHub organisation, private until submission) and data licences (authors' images, annotations).
2. Create the skeleton and `common/` with tests; port Fig 1 from the existing data package, then Fig 2, then Fig 3.
3. Export Fig 3 runs (script: transcripts → runs/<id>/, path scrubbing, meta.json, complexity.json).
4. Commit and tag `prompt-pack-v1` before collecting the ChatGPT / claude.ai conversations.
5. Upload raw data and large outputs to Zenodo (draft), fill `manifest.csv` and checksums, wire `fetch.py`.
6. CI: rebuild the figures and check the numbers in the legends; tag the release; mint the Zenodo DOI for the paper.

## 5. Code inventory: everything that produced a pixel, a plot or a number goes in

Rule: the repo holds **all code that produced what is shown** (figure builders, plots, scoring, processing, LLM run
harness), in final form and runnable from `data/`; superseded figure builders go to `*/superseded/` (kept, not run).

| Figure | Figure/plot builders | Scoring | Processing / analysis | Harness |
|---|---|---|---|---|
| 1 | `make_fig1.py` (final = v16; v1–v15, page/ncb/hpmec variants → superseded) | `f1_scores.py`, `matching.py`, `compare_*` | `segment_bf_cellpose.py`, `classical_seg.py`, `segment_panelA.py`, `export_splits.py`, `export_bf_example.py`, `export_rep_window.py`, `find_rep_window.py`, `extract_tracks.py`, `cct8_stats.py` | `agent_run.py` (check what it did; panel b is illustrative) |
| 2 | `make_fig2_v3.py` = `fig2_head.py` + `fig2_body_v3.py` + `blk_*.py` + `blk_helpers.py`; `render.sh`, `rebuild.sh` (v1–v2 → superseded) | `matching.py`, `score_perturb.py`, `annot_agree.py`, `errors.py`, `postfilter.py` | `cellpose_perturb.py`, `norm_inputs.py`, `export_window.py`, `export_errors_window.py`, `al_gray.py`, `al_intensity.py`, `al_roi.py`, `bio_result.py`, `squirrel_run.py`, `squirrel_tile.py`, `tubule_width.py`, `measure_icons_block.py`, `image_generation.py` | — |
| 3 | `fig3_head.py` + `fig3_helpers.py` + `fig3_v9.py`, `render.sh`, `rebuild_v8.sh`, `bf3/make_legend.py` (v1–v8, grid/rows/body variants → superseded) | `matching.py`, `bf/score_cancer.py`, `bf/score_endo.py`, `v3/score_nuclei.py`, `bf3/score_task.py`, `bf3/build_scores.py`, `bf2/score_both.py`, `bf2/draw/rasterise_poly.py`, `prompt_pack/complexity.py` | `bf/roi/*` (representative window), `bf3/fig_assets` export, held-out split (`heldout/`), `bf2/advise_impl.py` | `bf3/queue_runner.sh`, `ijm_runner.sh`, `collect.py`, `turn2.py`, `export_prompts.py`, `export_conversations.py`, `grab.py`, agent prompts; agent-written `pipeline.py` files kept as returned |

Audit findings from the inventory (to fix while porting):
- `matching.py` is identical in Figs 1–3 (same md5) → one copy in `common/`.
- Fig 3 row c re-implements the nuclei/endothelial conventions inside `build_scores.py` (`f1_half`) instead of
  calling the whole-field scorers → refactor into one function, and add a test that both give the same F1 on the full field.
- **Reported vs held-out F1 in row c mixes scorers**: the agents' own `score.py` (written by the agents, some with
  Hungarian matching and their own border handling) produced the "reported" development F1; our greedy scorer produced
  the held-out F1. Re-score each agent's frozen development output with our scorer and show both.
- Scripts import across working folders with absolute `sys.path` entries and upload-hash file names → repo-relative imports and a name map.
- Exploratory folders (`advicetest/`, `codetest/`, `syco/`, `agent_trap/`, `counts/`, `llm_outputs/`) produced earlier
  rounds → `fig3/superseded/` with their own README, so the abandoned experiments can be audited too.
