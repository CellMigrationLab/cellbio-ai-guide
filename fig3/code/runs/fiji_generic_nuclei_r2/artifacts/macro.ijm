input = "<fig3-work>/bf3/fj_gen_nuclei_r2/dapi.tif"; output = "<fig3-work>/bf3/fj_gen_nuclei_r2/labels.tif";

// ---- Parameters to tune ----
bgRadius   = 30;     // rolling-ball radius (px); keep larger than the biggest nucleus
blurSigma  = 1;      // smoothing before thresholding (px)
method     = "Li";   // try "Otsu" or "Triangle" if Li under/over-segments
minSize    = 40;     // smallest object kept (px^2); removes debris

setBatchMode(true);
open(input);
origTitle = getTitle();
run("Select None");

// Work on a copy so the raw data stay untouched
run("Duplicate...", "title=work");
selectWindow("work");
if (nSlices > 1) {
    // Only the current plane is segmented if the file is a stack
    run("Duplicate...", "title=work2");
    selectWindow("work");
    close();
    selectWindow("work2");
    rename("work");
}
run("32-bit");
run("Subtract Background...", "rolling=" + bgRadius);
run("Gaussian Blur...", "sigma=" + blurSigma);

// Threshold -> binary mask
setAutoThreshold(method + " dark");
run("Convert to Mask");
run("Fill Holes");
run("Open");                 // remove small specks
run("Watershed");            // split touching nuclei

// Label image: one integer per object, 0 = background
run("Set Measurements...", "area redirect=None decimal=3");
run("Analyze Particles...", "size=" + minSize + "-Infinity pixel show=[Count Masks] exclude clear");
labelTitle = getTitle();     // the "Count Masks of work" window
selectWindow(labelTitle);
run("Select None");
resetMinAndMax();

saveAs("Tiff", output);

// Report and tidy up
getStatistics(area, mean, min, max);
print("Nuclei segmented: " + max);
close("*");
setBatchMode(false);
