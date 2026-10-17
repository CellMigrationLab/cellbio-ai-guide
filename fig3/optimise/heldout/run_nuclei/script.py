# Frozen agent pipeline (ref_nuclei/pipeline.py, unchanged) applied to the held-out right half, which the agent never saw.
import subprocess, sys
subprocess.run([sys.executable, '../ref_nuclei/pipeline.py', '../heldout/dapi_heldout.tif', '../heldout/ref_nuclei_labels.tif'], check=True)
