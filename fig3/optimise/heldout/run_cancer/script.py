# Frozen agent pipeline (ref_cancer/pipeline.py, unchanged) applied to the held-out right half, which the agent never saw.
import subprocess, sys
subprocess.run([sys.executable, '../ref_cancer/pipeline.py', '../heldout/bf_heldout.tif', '../heldout/ref_cancer_labels.tif'], check=True)
