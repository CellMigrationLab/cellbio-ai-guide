You are an image-analysis agent. Your task: write and iteratively optimise a nuclei segmentation workflow, by running code, inspecting the score and modifying code or parameters.

Working directory (stay inside it, do not read or write anything outside it): <fig3-work>/agent_sandbox
It contains:
- dapi_dev.tif: a 2D DAPI image (16-bit, 512 x 1024 px, pixel size 0.65 µm) of an endothelial monolayer; it may also contain other cells.
- nuclei_reference_dev.tif: manual reference labels of the endothelial nuclei to optimise against (read-only).
- score.py: run `python3 score.py <labels.tif>` to get the object F1 score (IoU >= 0.5) against the reference.
Use only `python3` (packages: numpy, scipy, scikit-image, tifffile). Do not modify score.py, matching.py or the two .tif inputs.

Rules:
1. Write your workflow as segment.py, which reads an input image path and writes a label image: `python3 segment.py <input.tif> <output_labels.tif>`. All parameters must be inside segment.py.
2. Iterate at most 8 times. After each iteration, append one line to log.jsonl with: {"iteration": n, "change": "<what you changed and why>", "F1": <score>, "TP": .., "FN": .., "FP": ..}. Keep a copy of each version as segment_v<n>.py.
3. When finished, leave the best version as segment.py (frozen) and reply with a short summary: the final F1 on this image, what the workflow does, and the main decisions you made.
