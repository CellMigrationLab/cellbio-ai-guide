input = "<fig3-work>/bf3/fj_gen_nuclei_r1/dapi.tif"; output = "<fig3-work>/bf3/fj_gen_nuclei_r1/labels.tif";

// ---- Parameters you may want to tune ----
bgRadius   = 50;   // rolling-ball radius (px); should be larger than a nucleus
blurSigma  = 1.5;  // Gaussian smoothing (px)
method     = "Li"; // try "Otsu", "Triangle" or "Huang" if Li under/over-segments
minSize    = 30;   // smallest object kept (px^2); removes debris
maxSize    = 5000; // largest object kept (px^2)

setBatchMode(true);
run("Options...", "iterations=1 count=1 black");   // binary: objects = white

open(input);
origTitle = getTitle();
run("Set Scale...", "distance=0 known=0 unit=pixel");  // work in pixels, ignore calibration
if (nSlices > 1) {
    // if this is a z-stack, use a maximum projection
    run("Z Project...", "projection=[Max Intensity]");
    close(origTitle);
    origTitle = getTitle();
}

// ---- Preprocess a working copy ----
run("Duplicate...", "title=work");
selectImage("work");
run("Grays");
run("Subtract Background...", "rolling=" + bgRadius);
run("Gaussian Blur...", "sigma=" + blurSigma);

// ---- Threshold ----
setAutoThreshold(method + " dark");
run("Convert to Mask");
run("Fill Holes");

// ---- Split touching nuclei ----
run("Watershed");

// ---- Label image: one integer per object, 0 = background ----
run("Analyze Particles...", "size=" + minSize + "-" + maxSize + " pixel show=[Count Masks] exclude clear");
// 'exclude' drops nuclei touching the image edge; delete the word 'exclude' above to keep them.
labelTitle = getTitle();
run("Grays");   // plain display; the pixel values stay as label numbers

saveAs("Tiff", output);

// ---- Clean up ----
close("*");
setBatchMode(false);
print("Done. Labels saved to " + output);
