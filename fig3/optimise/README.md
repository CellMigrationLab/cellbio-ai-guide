# Row c: let an agent run and optimise the analysis

- `runs/by_eye_*`: "Please run the analysis pipeline …, assess the result, improve the analysis, and give me the result"
  on the whole image; no annotation. Scored on the held-out right half.
- `runs/with_annotation_*`: "Please build and optimise an analysis pipeline … Score every version against my annotation
  … Other images are held out …" with the left half (x < 512) and its annotation; the final `pipeline.py` was then run
  unchanged on the right half (`heldout/run_*`, output `heldout/ref_*_labels.tif`).
- `heldout/`: split images and references (`code/recovered_inline/` has the commands that made them).
- `dev_rescored.json`: agents' reported development F1 re-scored with our scorer.
