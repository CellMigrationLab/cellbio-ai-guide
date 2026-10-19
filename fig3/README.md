# Figure 3: how much analysis should an LLM do?

Figure 3 examines four ways a cell biologist might use an LLM (here Claude Sonnet 5.5, run as headless Claude Code sessions)
on three tasks of increasing difficulty: endothelial nuclei in DAPI, cancer cells in brightfield, and endothelial cells in
brightfield. Results are scored against the authors' manual annotations.

| Row | Request | Scored how |
|---|---|---|
| A | Ask for advice (basic prompt or detailed prompt) | Replies checked for outdated models or code ([v2/advice_outdated.csv](v2/advice_outdated.csv), first-pass classification by the operator, to be reviewed by the authors) |
| B | Ask for a Python script, which we run (basic or detailed prompt) | F1 on held-out halves of two fields, mean of the two |
| C | Let an agent write, run and improve a pipeline (by eye, or with the annotation as score) | Same as B |
| D | Ask for the answer (count) | Count against the manual count, per field |

**Status (19 Oct 2026):** all 72 runs of [protocol v2](PROTOCOL_V2.md) are recorded and scored; the figure is a draft under
review by the authors.

## Where things are

| Path | Contents |
|---|---|
| [PROTOCOL_V2.md](PROTOCOL_V2.md) | The plan, frozen on 17 Oct 2026 and revised for rows B and C on 19 Oct 2026. |
| [v2/](v2/README.md) | The harness (prompts, runner, scorer, operator tools) and every run record (`runs/`; replaced, interrupted or preflight runs are kept unedited in `runs_superseded/`, `runs_rejected/`, `runs_preflight/`). |
| [figure_v2/](figure_v2/README.md) | The figure builder (`make fig3`), its source data, SVG/PNG output and legends. |
| [scoring/](scoring/) | Task references and scoring conventions (`tasks.py`). |
| [deviations.md](deviations.md) | Everything that departed from the protocol, and other things an auditor should know. |
| [tests/](tests/) | Unit tests of the references, the freeze and the harness. |

An earlier first study (round 1: sub-agents on one field, Fiji and Python) was superseded by protocol v2 and removed from the
working tree on 19 Oct 2026; it remains in git history. Its deviations are still described in `deviations.md`.

## Recheck the scores and rebuild the figure

From the repository root:

```bash
PYTHONPATH=. python fig3/v2/check_scores.py   # every score recomputed from the stored runs (nothing is run again)
make fig3                                     # rebuild fig3/figure_v2/output/fig3_v2.svg and .png
```

These commands rescore stored outputs and redraw the figure. They do **not** recreate the LLM conversations. Running the
returned scripts again requires the software listed in [environment/](../environment/README.md).

## Limitations

This is an illustration, not a model benchmark: one model, three tasks, three runs per condition. The subjects were
headless Claude Code sessions, which differ from consumer chat interfaces (wrapper text, prescribed output files, controlled
tools). See [deviations.md](deviations.md).
