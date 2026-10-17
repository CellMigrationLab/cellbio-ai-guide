input = "<fig3-work>/bf3/fj_box1_nuclei_r2/dapi.tif";
output = "<fig3-work>/bf3/fj_box1_nuclei_r2/labels.tif";
// Use full paths if the files are not in Fiji's current working directory.

// ---------------- Parameters (pixels unless noted) ----------------
pixelSize    = 0.65;   // um per pixel (overrides file calibration)
dMinUm       = 13;     // nuclear diameter, um
dMaxUm       = 17;
sigmaPx      = 1.0;    // Gaussian denoise, px
bgRadiusPx   = 40;     // rolling ball, px (> largest nucleus diameter ~26 px)
localRadius  = 25;     // Auto Local Threshold radius, px (~ nucleus diameter)
localOffset  = 0;      // Mean method parameter_1
saturatedPct = 0.35;   // contrast clipping used for 8-bit scaling of log image
excludeEdges = false;  // true = drop nuclei touching the image border
// Size limits derived from diameters (area in px)
minAreaPx = 0.3 * PI * pow(dMinUm / 2 / pixelSize, 2);
maxAreaPx = 2.0 * PI * pow(dMaxUm / 2 / pixelSize, 2);

setBatchMode(true);
run("Options...", "iterations=1 count=1 black");   // binary ops: 255 = foreground
roiManager("reset");

open(input);
src = getTitle();
getDimensions(w, h, c, z, t);
if (c * z * t != 1) exit("Expected a single-channel 2D image (Y, X); got c=" + c + " z=" + z + " t=" + t);
if (bitDepth() == 24) exit("RGB image: convert to single-channel first.");
run("Properties...", "channels=1 slices=1 frames=1 unit=um pixel_width=" + pixelSize + " pixel_height=" + pixelSize + " voxel_depth=1.0");

// ---- working copy: denoise, remove background, log-compress, scale to 8-bit ----
run("Duplicate...", "title=work");
run("32-bit");
run("Gaussian Blur...", "sigma=" + sigmaPx);
run("Subtract Background...", "rolling=" + bgRadiusPx);
run("Add...", "value=1");
run("Log");
run("Enhance Contrast...", "saturated=" + saturatedPct);   // sets display range only
run("8-bit");                                              // scales using that range

// ---- global floor (Li) so empty background cannot pass the local threshold ----
run("Duplicate...", "title=floor");
setAutoThreshold("Li dark");
getThreshold(lo, hi);
resetThreshold();
changeValues(0, lo - 1, 0);
changeValues(lo, 255, 255);

// ---- local threshold, combine, clean up, split touching nuclei ----
selectWindow("work");
run("Auto Local Threshold", "method=Mean radius=" + localRadius + " parameter_1=" + localOffset + " parameter_2=0 white");
imageCalculator("AND", "work", "floor");
selectWindow("work");
if (is("Inverting LUT")) run("Invert LUT");
getStatistics(areaAll, meanVal);
if (meanVal > 127) exit("Mask looks inverted (foreground > 50% of image); check threshold polarity.");
run("Fill Holes");
run("Open");
run("Watershed");

// ---- objects -> ROI Manager ----
setThreshold(255, 255);
opts = "size=" + floor(minAreaPx) + "-" + ceil(maxAreaPx) + " pixel show=Nothing add";
if (excludeEdges) opts = opts + " exclude";
run("Analyze Particles...", opts);
n = roiManager("count");
if (n == 0) exit("No objects found.");

// ---- label image, same size as the input ----
if (n < 65535) bits = "16-bit"; else bits = "32-bit";
newImage("labels", bits + " black", w, h, 1);
run("Properties...", "channels=1 slices=1 frames=1 unit=um pixel_width=" + pixelSize + " pixel_height=" + pixelSize + " voxel_depth=1.0");
for (i = 0; i < n; i++) {
    roiManager("select", i);
    setColor(i + 1);
    fill();
}
run("Select None");
saveAs("Tiff", output);
print("Saved " + n + " labelled nuclei to " + output + " (size filter " + floor(minAreaPx) + "-" + ceil(maxAreaPx) + " px)");
setBatchMode(false);
