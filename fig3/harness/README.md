# Historical Figure 3 execution scripts

These scripts record how the **round-1 draft** LLM runs were collected, executed and scored. They are retained for audit, not recommended as the runner for a new experiment. For the replacement study, see [protocol v2](../PROTOCOL_V2.md) and its [current harness](../v2/README.md).

| File | Historical role |
|---|---|
| `collect.py` | Read transcripts, extract the first code block, save a Python script or Fiji macro and queue it. |
| `queue_runner.sh`, `ijm_runner.sh` | Execute queued scripts and macros sequentially, with timeouts, then score outputs. |
| `score_task.py`, `legacy_scorers/` | Scoring implementations used at the time. [scoring/tasks.py](../scoring/tasks.py) reproduces their scores on repository paths. |
| `build_scores.py`, `make_legend.py` | Assemble the draft figure scores and legend. |
| `turn2.py` | Queue a script returned in a second reply during the pilots. |
| `export_prompts.py`, `export_conversations.py`, `grab.py`, `grab_round2.py` | Export conversations, prompts and hand-back records. |

The scripts retain the working-folder paths and execution conventions used at the time. Consult the saved transcripts and [deviations](../deviations.md) before interpreting a historical score.
