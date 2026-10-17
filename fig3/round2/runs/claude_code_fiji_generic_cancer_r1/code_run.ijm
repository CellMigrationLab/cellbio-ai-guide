// Count and measure cancer cells sitting on an endothelial monolayer (brightfield).
// Input : image.tif in the working folder      Output: labels.tif (16-bit label image),
//         results table (Label, Area, Solidity...) saved as results.csv, overlay shown.
// Idea  : cancer cells are round with a dark rim; the endothelium is low contrast.
//         Flatten illumination -> threshold the dark rims -> close/fill -> split touching
//         cells with watershed -> keep objects by size and solidity (removes debris).

// ---------------- parameters (tune these) ----------------
dir        = "/home/user/r2exec/claude_code_fiji_generic_cancer_r1/";  // working folder
bgSigma    = 40;     // px, illumination flattening (much larger than a cell, ~28 px wide)
smooth     = 1;      // px, noise smoothing
rimThresh  = 60;     // dark-rim threshold in grey levels below local background (16-bit data)
closeIter  = 3;      // binary close iterations (joins broken rims)
openIter   = 5;      // binary open iterations (removes debris)
minArea    = 250;    // px^2, smaller objects are debris (single cell is ~400-1000 px^2)
maxArea    = 5000;   // px^2, larger objects are unresolved clumps
minSolidity= 0.80;   // ragged debris has low solidity
// ----------------------------------------------------------

setBatchMode(true);
run("Clear Results"); roiManager("reset");
open(dir + "image.tif");
rawTitle = getTitle();
getPixelSize(unit, pw, ph);            // area is reported in calibrated units if the scale is set

// 1. flatten background and smooth
run("32-bit");
run("Duplicate...", "title=bg");
run("Gaussian Blur...", "sigma=" + bgSigma);
imageCalculator("Subtract create 32-bit", rawTitle, "bg");
rename("flat");
run("Gaussian Blur...", "sigma=" + smooth);

// 2. dark cell rims -> binary mask
setThreshold(-1e9, -rimThresh);
run("Convert to Mask");                 // objects = 255
run("Options...", "iterations=" + closeIter + " count=1 black do=Close");
run("Fill Holes");
run("Options...", "iterations=" + openIter + " count=1 black do=Open");

// 3. split touching cells
run("Options...", "iterations=1 count=1 black");
run("Watershed");
rename("mask");

// 4. detect objects, then filter on solidity
run("Set Measurements...", "area shape redirect=None decimal=2");
run("Analyze Particles...", "size=" + minArea + "-" + maxArea + " pixel add");
n = roiManager("count");

selectWindow("mask");
w = getWidth(); h = getHeight();
newImage("labels", "16-bit black", w, h, 1);
kept = 0;
for (i = 0; i < n; i++) {
    roiManager("select", i);
    List.setMeasurements;
    if (List.getValue("Solidity") >= minSolidity) {
        kept++;
        setColor(kept);
        fill();
        // record per-cell measurements
        setResult("Cell", nResults, kept);
        r = nResults - 1;
        setResult("Area_px", r, List.getValue("Area") / (pw * ph));
        setResult("Area_" + unit + "^2", r, List.getValue("Area"));
        setResult("Solidity", r, List.getValue("Solidity"));
        setResult("Circ", r, List.getValue("Circ."));
    }
}
roiManager("deselect");
resetMinAndMax();
saveAs("Tiff", dir + "labels.tif");
if (nResults > 0) saveAs("Results", dir + "results.csv");

// 5. report
selectWindow(rawTitle); run("Enhance Contrast", "saturated=0.35");
setBatchMode("exit and display");
print("Cancer cells counted: " + kept);
if (kept > 0) {
    s = 0; for (i = 0; i < kept; i++) s += getResult("Area_" + unit + "^2", i);
    print("Mean area (" + unit + "^2): " + s / kept);
}
