# Figure 3: deviations from protocol and other things an auditor should know

## Prompts and harness
- All runs used Claude Code sub-agents (not the claude.ai app). Each prompt starts with our wrapper text (role, which
  file may be viewed, whether code can be run, which tools may be used) and ends with an output-format instruction
  (`labels.tif`, one code block). Both are visible in every `prompt.md`.
- Box 1 prompts included a setup line not in Box 1 ("My setup: Python … Cellpose 4.2.1.1 (CPU only)" / "a current Fiji
  installation") so that the code could run in our environment.
- Web tools (WebSearch/WebFetch) were allowed where stated but had to be loaded by the model before use; many runs did
  not load them, one concluded it had no web access. "Did not check the documentation" is therefore partly a harness effect.
- Box 1 v1 (stricter wording) runs were superseded by Box 1 v2 runs (`superseded/runs/python_box1_v1wording_*`).

## Running the code
- Fiji macros: the `input = …` and `output = …` lines were replaced by absolute paths so that the macros could run
  headless (`harness/collect.py`); nothing else was edited.
- Python scripts were run unchanged in a folder containing the image (`harness/queue_runner.sh`).
- Two Fiji macros failed and wrote no output, counted as F1 0 (× in the figure): `fiji_generic_cancer_r3` calls a
  non-existent command ("Set Scaling…"); `fiji_box1_nuclei_r2` calls `ceil()`, which the ImageJ macro language does not have.
- Draw runs: the model's polygons were rasterised (`direct_answers/code/rasterise_poly.py`). `draw_nuclei_r2` returned
  centres plus a hexagon rule instead of polygons; it was rasterised from its own rule. Endothelial "outlines" were a
  placeholder grid, as one reply states.

## Agents (row c)
- The nuclei agent with annotation wrote its working files outside its folder; they were copied back
  (`optimise/runs/with_annotation_nuclei/artifacts/written_outside_sandbox/`).
- The cancer agent (rerun) wrote intermediate files to `/tmp`.
- The endothelial agent (rerun) copied `pipeline.py` and `log.txt` outside its folder and deleted the copies (it said so).
- The first attempts of the cancer and endothelial agents with annotation were interrupted by a session restart and
  rerun from clean folders (`superseded/runs/optimise_with_annotation_*_interrupted`).
- By-eye agents were scored on the held-out half so that both conditions are compared on the same cells.
- Agents' reported development scores came from their own scoring code; re-scored with ours in `optimise/dev_rescored.json`.

## Answers to follow-up questions (pilots only)
- In the Box 1 v3 pilots we answered the models' questions from a fixed answer sheet (`pilots/answer_sheet_pilot.md`).
  One answer was wrong ("label the visible part of endothelial cells under cancer cells"; the annotation runs under
  them); the advice run that spotted the inconsistency received the correction, the code pilot did not.

## Scoring conventions
- Nuclei: predicted objects lying > 30 % on annotated cancer cells are ignored (cancer-cell nuclei are not annotated).
- Endothelial cells: objects touching the image border are removed from reference and prediction; reference cells come
  from annotator 1's junction lines (`lines_to_cells`, slivers < 150 px removed).
- Code that crashed or wrote no label image: F1 0, drawn as ×.
