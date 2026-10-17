# Superseded rounds (kept so that the abandoned experiments can be audited too)

`runs/` holds the transcripts of every earlier LLM run (see `../runs_index.csv`, status `superseded`); `workfolders/`
holds their working folders (TIFFs losslessly compressed; raw-image copies removed); `figure_builders/` holds earlier
figure versions (v1–v8). Why each round was dropped:

| Round | Runs | Why superseded |
|---|---|---|
| Counting crops with three models (Opus/Sonnet/Haiku), full-field counts | `count_objects_*`, `full_fov_counts_*` | design changed to one free-tier model, three runs, full field, three tasks |
| Sycophancy test (neutral vs leading question) | `sycophancy_*` | dropped from the figure (text covers it) |
| First code and advice tests (nuclei, vague/specific/Box 1), sandboxed agent, agent "trap" | `code_*_prompt`, `cellpose_advice_*`, `advice_only_*`, `sandboxed_segmentation_agent`, `agent_trap_optimisation_run`, `realistic_analysis_agent` | single task; optimisation set-up judged unrealistic |
| Brightfield cancer-cell round | `bf_*`, `draw_cancer_cells_*`, `count_cells_sonnet_*`, `draw_nuclei_from_bf_*` | replaced by the two-target round, then the three-task round |
| Old "specific" code prompts (cancer, endothelial) | `code_specific_*`, `workfolders/bf2/codeS_*` | replaced by Box 1 |
| Box 1 v1 (stricter wording) | `python_box1_v1wording_*` | Box 1 text revised; rerun with v2 |
| Interrupted agents with annotation | `optimise_with_annotation_*_interrupted` | session restart; rerun from clean folders |
