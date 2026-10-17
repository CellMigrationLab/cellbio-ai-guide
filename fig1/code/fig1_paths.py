"""Canonical locations of Figure 1 derived files (relative to fig1/source_data, the working directory of fig1/code).

Every producer writes here and every consumer reads from here, so a re-run always updates the file that is scored
and drawn (audit P0.1). Figure 2 and Figure 3 read CELLPOSE_LABELS through fig1/source_data/full_field_labels/.
"""
CELLPOSE_LABELS = "full_field_labels/cellpose_sam_labels.tif"    # Cellpose-SAM, default settings, whole field 104
THRESHOLD_LABELS = "full_field_labels/threshold_labels.tif"      # classical threshold pipeline, whole field 104
