# Figure 3: Using an LLM for image analysis, from advice to delegation

**Status: round-1 draft, to be replaced.** The figure is being redone under `PROTOCOL_V2.md` (harness in `v2/`); this
README, `deviations.md` and the folders below describe **round 1**, which produced the current draft
(`figure/output/fig3_preview.png`, legend `figure/legend.md`). Builder `figure/code/make_fig3.py` (reads `figure/source_data/round1/`)
(= `fig3_head.py` + `fig3_helpers.py` + `fig3_v9.py`, see `figure/code/build_parts/`).

## Round-1 design
Three tasks on one field of view (cancer cells on an endothelial monolayer; 0.65 µm/px), easy to hard:
**nuclei** (DAPI, 441 endothelial nuclei), **cancer cells** (brightfield, 124), **endothelial cells** (brightfield, 382,
two annotators agree F1 0.90). Each row compares a common request ("before") with the request recommended in the text
and Box 1 ("after"). Model: Claude Sonnet (claude-sonnet-5-5), run as Claude Code sub-agents, 16–17 Oct 2026; three
runs per condition unless stated. Scores: object F1 at IoU ≥ 0.5 (`scoring/tasks.py`).

| Folder | Row | Before → after | What is stored |
|---|---|---|---|
| `advice/` | a | advice from memory → after reading the documentation | 4 runs (cancer, endothelial); our implementation of each piece of advice (`advice/code/advise_impl.py`, not shown); the `cyto3` silent-fallback test |
| `code/` | b1, b2 | generic request → Box 1 v2 (exact text in each run's `prompt.md`); Fiji macro and Python | 36 runs: code as returned and as run, run log, label image, score |
| `optimise/` | c | agent judging by eye → agent scored against annotation of the left half, frozen, run on the held-out right half | 6 runs (full agent transcripts, every file they wrote), held-out split, frozen-pipeline outputs, `dev_rescored.json` |
| `direct_answers/` | d | "How many … ?" → "Draw around every … and count them" | 18 runs; rasterised outlines and scores; counts as stated |

Every run folder (`<section>/runs/<run_id>/`) has `prompt.md` (exact first message, **including our wrapper text**),
`conversation.md` (all turns verbatim, tool calls listed; harness notes marked as such), `meta.json` (model, times,
tools used, web searches, files read) and `artifacts/` (files from the run's working folder; TIFFs re-saved with
lossless compression, pixel values verified). `runs_index.csv` maps each run to its section and original agent;
`all_runs.csv` lists every run with its score.

Other folders: `figure/` (builder, source data, output), `scoring/` (task definitions, `build_scores.py`,
`rescore_dev.py`, `all_runs_table.py`), `baselines/` (Cellpose default on DAPI), `harness/` (scripts that queued, ran,
collected and scored the runs, as used), `v2/` (assets and scorer for protocol v2, `PROTOCOL_V2.md`), `pilots/` (Box 1 draft v3 tests, not in the figure), `superseded/` (all earlier rounds, kept for audit).

## Reproduce the numbers
```
PYTHONPATH=. python fig3/scoring/build_scores.py --check   # every score in the figure, from the stored outputs
PYTHONPATH=. python fig3/scoring/rescore_dev.py            # agents' reported development F1 re-scored with our scorer
make fig3                                                  # figure from figure/source_data (byte-identical)
```
Re-running the code itself: Python runs need Cellpose 4.2.1.1 (`environment/`), run as `python script.py` in a folder
containing `bf.tif` or `dapi.tif` (copies of `data/raw/field104_brightfield.tif` / `field104_dapi.tif`); Fiji macros as
in `harness/queue_runner.sh`. LLM replies themselves are not reproducible bit-for-bit.

## Caveats (read before citing a number)
- Illustration, not a benchmark: one field, one model, three runs per condition.
- The sub-agent harness differs from the chat apps: our wrapper text, a fixed output format (`labels.tif`), a setup line
  (software available) not in Box 1, and web tools that must be loaded before use (most runs never loaded them). See
  `deviations.md`. The next round follows `PROTOCOL_V2.md`.
- Row c "reported" scores came from scoring code written by each agent; with our scorer they are 0.927, 0.930, 0.706
  (nuclei, cancer, endothelial) instead of 0.927, 0.930, 0.695 (`optimise/dev_rescored.json`).
- Three of six agent runs read or wrote files outside the folder they were told to use (`deviations.md`).
