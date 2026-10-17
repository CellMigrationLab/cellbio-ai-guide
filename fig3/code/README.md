# Rows b1 (Fiji macro) and b2 (Python script): ask for code

`runs/{fiji,python}_{generic,box1}_{nuclei,cancer,endothelial}_r{1,2,3}`. Generic: "Please write a Fiji macro / Python
script to segment the … in my … image." Box 1: `box1/box1_v2_used_in_figure3.md` filled in per task, web search allowed.
The model saw a preview of the image and could not run code. `artifacts/script.py` or `macro.ijm` is the code as run
(macros: input/output lines replaced by absolute paths, see `../deviations.md`); the code as returned is in
`conversation.md`. `labels.tif` is its output; no `labels.tif` = the code crashed or wrote nothing (scored 0).
Python generic cancer/endothelial run 1 come from the two-target round (same prompt).
