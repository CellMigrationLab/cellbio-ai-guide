# Figure 3 (protocol v2): legend draft

**Figure 3. Four ways of using an LLM for image analysis, on three tasks.** Top: the three tasks, each with one
field of view (FOV 1: DAPI for the nuclei, brightfield for the cells) and its manual annotation. For rows b and c the model was given only the left halves of FOV 1 and
FOV 2 (dashed line: "given"); every result in those rows is scored on the right halves of both FOVs ("held out"), against
the authors' manual annotation. **a**, Ask for advice: nine replies per prompt (three per task). A basic prompt asks which
tool to use; the detailed prompt also asks the model to check the current documentation. The replies were classified by
the authors' operator for outdated models or code (for example Cellpose `cyto3` or `nuclei`, removed in Cellpose 4);
outdated code can fail, raise errors, or fall back silently (example in the black box: `cyto3` loads the current model
without any message). **b**, Ask for code: three scripts per prompt and task, written by the model and run by us unchanged
on both FOVs. Bars: median over the three scripts of the mean object F1 (IoU ≥ 0.5) on the held-out halves of the two
FOVs; open circles: each script; red cross: a script that failed on at least one FOV (a failed FOV counts 0). **c**, Let an agent write, run and optimise a pipeline in its own folder, three runs per arm
and task: by eye (no annotation) or scored (given the annotation of the development halves). The final pipeline was run
by us on both FOVs; symbols as in b. **d**, Ask for the answer: "How many … are in this image?", three conversations per
FOV and task. Each dot is the count the model stated; the dashed line, with its value, is the manual count of that FOV (each panel has
its own scale). Repeating the same question gives different answers. All conversations used Claude Sonnet 5.5 (model ID `claude-sonnet-5-5`) in
headless Claude Code sessions (versions 2.1.302 and 2.1.303).

Notes for the authors (not for the figure): the model refused to draw ellipses for nuclei and endothelial cells (12 of 18
conversations, `fig3/v2/direct_summary.csv`), so the drawn results and the stated size and shape (turn 2) are not shown;
area and aspect-ratio results of rows b and c are in `fig3/figure_v2/source_data/fig_scores_v2.json` and
`fig3/v2/runs/*/score.json` (not shown); script differences and rating: `fig3/v2/code_metrics.csv`,
`fig3/v2/code_rating/`.
