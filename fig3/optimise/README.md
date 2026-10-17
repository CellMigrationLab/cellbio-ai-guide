# Figure 3 round 1: letting an agent optimise the analysis

These are historical **round-1 draft** runs. The revised experiment uses a separate development field and test field; see [protocol v2](../PROTOCOL_V2.md).

Two conditions were compared:

- **By eye:** `runs/by_eye_*`. The agent ran and adjusted a workflow without manual annotations. Its final output was scored on the held-out right half of the image.
- **With annotations:** `runs/with_annotation_*`. The agent received the left half (x < 512) and its annotation for development. Its final `pipeline.py` was then run unchanged on the right half.

[heldout/](heldout/) contains the split images, reference labels and resulting outputs. [dev_rescored.json](dev_rescored.json) compares the agents' reported development F1 with the score calculated by our implementation.

**Limitation:** the development and test regions came from the same field of view. They are not independent experimental samples. This was one reason to replace the design.
