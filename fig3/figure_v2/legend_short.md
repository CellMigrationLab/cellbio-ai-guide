**Figure 3. Four ways of using an LLM for image analysis.** The task, on three datasets, is to segment and count
endothelial nuclei, cancer cells or endothelial cells and to measure the area and aspect ratio of each (top: one field of view,
FOV 1, with its manual annotation). In **b** and **c** the model worked only on the left halves of FOV 1 and FOV 2 ("given");
results are scored against the manual annotation on the right halves of both FOVs ("held out"). **a**, Ask for advice: three
replies per prompt and task; red dots mark replies that suggested an outdated model or code. **b**, Ask for code: three scripts
per prompt and task, run unchanged. Bars: median over the three scripts of the object F1 (IoU ≥ 0.5) averaged over the two
FOVs; circles: single scripts; red cross: a script that failed on a FOV (counted as 0). **c**, Let an agent write, run and
optimise a pipeline, without (by eye) or with a score against the annotation; symbols as in b. **d**, Ask for the count: each dot
is the count stated in one conversation (three per FOV); dashed line: manual count. All conversations used Claude Sonnet 5.5 (model ID `claude-sonnet-5-5`) in headless Claude Code
sessions (versions 2.1.302 and 2.1.303); web search was available in a, and a shell in c.
