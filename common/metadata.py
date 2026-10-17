"""Image metadata used in measurements (one source; analysis scripts import from here).

Pixel sizes are the exact values used for physical units; figures may print rounded values (0.65 µm).
"""
FOLLAIN_PX_UM = 0.649614          # fields 104 and 209 (brightfield, DAPI, PECAM-1); TIFF metadata
FOLLAIN_FIELD_SHAPE = (1022, 1024)
CARE_PX_UM = 0.6337               # CARE denoising example (authors' acquisition)
BIOSR_LOWRES_PX_NM = 62.6         # BioSR low-res input (Qiao et al. 2021; not in the TIFF metadata)
BIOSR_GRID_PX_NM = BIOSR_LOWRES_PX_NM / 2   # prediction and high-res reference on the 2x grid (31.3 nm)
TRACKMATE_PX_UM = 1.31483         # TrackMate capture (Fig. 1c step 5)
