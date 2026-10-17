# Reference: Cellpose-SAM with default settings on the DAPI image (as the grey bars for the other tasks)
import tifffile
from cellpose import models
m = models.CellposeModel(gpu=False)
L = m.eval(tifffile.imread('dapi.tif'))[0]
tifffile.imwrite('labels.tif', L.astype('int32'))
