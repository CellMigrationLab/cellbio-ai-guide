input = "<fig3-work>/bf3/fj_box1_cancer_r3/bf.tif"; output = "<fig3-work>/bf3/fj_box1_cancer_r3/labels.tif";

// ---- parameters (see notes) ----
pixelSize   = 0.65;   // um per pixel
preSigma    = 1;      // px, Gaussian before variance
varRadius   = 3;      // px (~2 um), Variance filter radius
postSigma   = 4;      // px (~2.6 um), Gaussian after variance
method      = "Triangle dark";  // auto-threshold on the 32-bit variance map
minDiamUm   = 10;     // um, smallest object kept
minCirc     = 0.30;
shrinkPx    = 0;      // optional erosion (px) of the mask before watershed, to correct a measured area bias

setBatchMode(true);
setOption("BlackBackground", true);
run("Conversions...", "scale weighted");   // default conversion behaviour, stated explicitly

open(input);
origTitle = getTitle();
getDimensions(w, h, nC, nZ, nT);
if (nC > 1 || nZ > 1 || nT > 1)
    exit("Expected a single 2D plane (Y, X); got C=" + nC + " Z=" + nZ + " T=" + nT);
if (bitDepth() == 24) run("8-bit");   // RGB -> grey, only if the file is RGB
run("Set Scale...", "distance=1 known=" + pixelSize + " pixel=1 unit=um");

// ---- work on a 32-bit copy; the original is untouched ----
run("Duplicate...", "title=work");
run("32-bit");
run("Gaussian Blur...", "sigma=" + preSigma);
run("Variance...", "radius=" + varRadius);
run("Gaussian Blur...", "sigma=" + postSigma);
setAutoThreshold(method);
run("Convert to Mask");               // white objects on black (BlackBackground = true)
run("Fill Holes");
for (i = 0; i < shrinkPx; i++) run("Erode");
run("Watershed");

// ---- label image: one integer per object ----
minAreaPx = PI * pow(minDiamUm / 2, 2) / (pixelSize * pixelSize);
n0 = nImages;
run("Analyze Particles...", "size=" + minAreaPx + "-Infinity pixel circularity=" + minCirc + "-1.00 show=[Count Masks]");
if (nImages == n0) {                  // no objects found
    newImage("labels", "16-bit black", w, h, 1);
} 
labTitle = getTitle();
run("Set Scale...", "distance=1 known=" + pixelSize + " pixel=1 unit=um");
getStatistics(a, m, mn, nObjects);
print("Objects: " + nObjects + "  (min area " + d2s(minAreaPx, 0) + " px)");
saveAs("Tiff", output);
close("*");
setBatchMode(false);
