# Does Cellpose 4.2.1.1 warn when asked for the removed 'cyto3' model? (row a caveat)
# Recovered from the session transcript (2026-10-16T19:04:58Z); run with the Cellpose 4.2.1.1 environment.
python -c "
from cellpose import models
m=models.CellposeModel(gpu=False, pretrained_model='cyto3')
print('pretrained_model =', m.pretrained_model)
" > output.txt 2>&1
