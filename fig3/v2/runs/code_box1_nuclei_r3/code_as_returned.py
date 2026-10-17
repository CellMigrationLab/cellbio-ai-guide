    labels = keep_labels(all_labels, flags.loc[flags["kept"], "label"].to_numpy())
    shape = measure_shape(labels)
    stats = shape.loc[~shape["touches_border"]].drop(columns="touches_border")
    if stats.empty:
        raise RuntimeError("No nuclei left after excluding those touching the border")
    check_plausibility(stats)

    tifffile.imwrite("all_objects_labels.tif", all_labels)
    flags[["label", "area_um2", "aspect_ratio", "mean_intensity_ratio",
           "too_bright", "bright_and_round", "too_small", "kept"]] \
        .to_csv("all_objects.csv", index=False)
    tifffile.imwrite("labels.tif", labels)
    stats.to_csv("measurements.csv", index=False)
    save_overlay(image, all_labels, flags.loc[flags["kept"], "label"].to_numpy(), Path("overlay.png"))
    log.info("Endothelial nuclei counted: %d (labels.tif); %d measured after excluding %d touching the border "
             "(measurements.csv)", len(shape), len(stats), int(shape["touches_border"].sum()))
