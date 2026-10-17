# Frozen agent pipeline (ref_endo/pipeline.py, unchanged) applied to the held-out right half, which the agent never saw.
import subprocess, sys
subprocess.run([sys.executable, '../ref_endo/pipeline.py', '../heldout/bf_heldout.tif', '../heldout/ref_endo_labels.tif'], check=True)
