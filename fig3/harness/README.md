# Harness: how the Figure 3 runs were executed and collected (as used; paths are those of the working folder)

| File | Role |
|---|---|
| `collect.py` | read each finished sub-agent transcript, extract the first code block, write `script.py` / `macro.ijm` (macro input/output lines replaced by absolute paths), queue it |
| `queue_runner.sh`, `ijm_runner.sh` | run queued Python scripts (Cellpose 4.2.1.1, CPU, 1 h timeout) and Fiji macros (headless, 30 min timeout) one at a time, then score |
| `score_task.py` + `legacy_scorers/` | the scorers used at the time (`score_cancer.py`, `score_endo.py`, `score_nuclei.py`, `matching.py`); `../scoring/tasks.py` re-implements them on repository paths and reproduces every score |
| `build_scores.py`, `make_legend.py` | built `fig_scores.json` and the legend for the figure |
| `turn2.py` | queue the script from a model's second reply (pilots) |
| `export_prompts.py`, `export_conversations.py`, `grab.py`, `grab_round2.py` | export prompts, replies and hand-back reports from transcripts |
