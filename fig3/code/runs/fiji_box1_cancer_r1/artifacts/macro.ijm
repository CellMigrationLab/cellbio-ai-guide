input = "<fig3-work>/bf3/fj_box1_cancer_r1/bf.tif";
output = "<fig3-work>/bf3/fj_box1_cancer_r1/labels.tif";

// ---- parameters (see notes) ----
pixelSize   = 0.65;  // um per pixel, set explicitly; the file's metadata is ignored
varRadius   = 2;     // px, Variance filter radius (rim/texture energy)
smoothSigma = 3;     // px, Gaussian sigma applied after Variance
shrinkPx    = 2;     // px, binary erosion to offset filter halo (area bias; tune)
minAreaUm2  = 100;   // um^2 (about 11 um diameter)
maxAreaUm2  = 800;   // um^2 (about 32 um diameter); larger blobs are discarded
excludeEdges = false; // true = drop cells touching the image border

setBatchMode(true);
open(input);
origID = getImageID();
w = getWidth(); h = getHeight();
if (nSlices > 1) exit("Input has more than one plane; this macro expects a single 2D image.");
run("Select None");

// Work on a 32-bit copy. No resizing, no intensity normalisation.
run("Duplicate...", "title=work");
workID = getImageID();
run("32-bit");

run("Variance...", "radius=" + varRadius);
run("Gaussian Blur...", "sigma=" + smoothSigma);

setAutoThreshold("Otsu dark");
setOption("BlackBackground", true);
run("Convert to Mask");          // 8-bit, objects = 255
run("Fill Holes");
if (shrinkPx > 0) run("Minimum...", "radius=" + shrinkPx);  // erodes 255 objects
run("Watershed");

minPx = minAreaUm2 / (pixelSize * pixelSize);
maxPx = maxAreaUm2 / (pixelSize * pixelSize);
opts = "size=" + d2s(minPx, 0) + "-" + d2s(maxPx, 0) + " pixel show=[Count Masks]";
if (excludeEdges) opts = opts + " exclude";
run("Analyze Particles...", opts);
labID = getImageID();

if (getWidth() != w || getHeight() != h) exit("Label image size differs from input.");
setVoxelSize(pixelSize, pixelSize, 1, "um");
saveAs("Tiff", output);

getRawStatistics(n, mean, min, max);
print("Objects: " + max + "  (labels saved to " + output + ")");

// tidy up
selectImage(workID); close();
selectImage(origID); close();
setBatchMode(false);
