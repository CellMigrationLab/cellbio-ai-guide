# Figure 3: how much analysis should an LLM do?

Figure 3 examines four ways a cell biologist might use an LLM: ask for advice, ask it to write code, let an agent run and optimise an analysis, or ask for a measurement directly.

**Current status:** the [figure preview](figure/output/fig3_preview.png) and [legend](figure/legend.md) show **round 1**, a draft that will be replaced. The current design is [protocol v2](PROTOCOL_V2.md), implemented in [v2/](v2/README.md). Do not cite the round-1 results as the final study.

## What was tested in round 1?

All three tasks used one field of cancer cells on an endothelial monolayer, with a pixel size of approximately 0.65 µm: 441 endothelial nuclei (DAPI), 124 cancer cells (brightfield) and 382 complete endothelial cells (brightfield). The model was Claude Sonnet through Claude Code sub-agents, tested on 16–17 October 2026, usually three conversations per condition.

| Row | Request | Where to find the records |
|---|---|---|
| A | Ask for advice, with or without checking documentation | [advice/](advice/README.md) |
| B | Ask for a Fiji macro or Python script, with a generic prompt or Box 1 | [code/](code/README.md) |
| C | Let an agent optimise by eye or against annotations | [optimise/](optimise/README.md) |
| D | Ask for a count directly or ask the model to draw and count objects | [direct_answers/](direct_answers/README.md) |

The run folders contain the prompts, verbatim conversations, metadata, code and outputs. [runs_index.csv](runs_index.csv) maps run IDs to records; [all_runs.csv](all_runs.csv) contains the draft scores. [deviations.md](deviations.md) records how this first study departed from its plan; earlier rounds, pilots and the run scripts are in git history.

## Other folders

| Folder | Contents |
|---|---|
| [figure/](figure/) | Draft figure builder `code/make_fig3.py`, the scores it reads (`source_data/round1/`) and its output. |
| [scoring/](scoring/) | Task references and scoring conventions (`tasks.py`), the draft score table (`build_scores.py`), rescoring of the agents' development scores and the all-runs table. |
| [baselines/](baselines/) | Cellpose with default settings on the DAPI image, for comparison. |
| [v2/](v2/README.md) | Harness of protocol v2 (prompts, runner, scorer, operator tools). |

## Recheck the draft scores

From the repository root:

```bash
PYTHONPATH=. python fig3/scoring/build_scores.py --check
PYTHONPATH=. python fig3/scoring/rescore_dev.py
make fig3
```

These commands rescore stored outputs and rebuild the draft figure. They do **not** recreate the LLM conversations. Running the returned scripts also requires the software listed in [environment/](../environment/README.md).

## Limitations of round 1

This is an illustration, not a model benchmark. It used one field, one model and few runs. The sub-agent harness differed from consumer chat interfaces: it added wrapper text, prescribed output files and controlled tool access. Some runs never loaded their available web tools. See [deviations.md](deviations.md).

The agents' reported development F1 values also did not always match independent rescoring: the endothelial score changed from 0.695 to 0.706 in [dev_rescored.json](optimise/dev_rescored.json). Three of six agent runs accessed files outside their assigned folders. These are reasons to inspect the records, not to draw general conclusions from the draft.

The replacement protocol uses two fields, a revised scoring design and more explicit controls. Its [README](v2/README.md) is the starting point for that experiment.
