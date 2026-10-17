input = "<fig3-work>/bf3/fj_gen_nuclei_r3/dapi.tif"; output = "<fig3-work>/bf3/fj_gen_nuclei_r3/labels.tif";

// ---- Parameters to tune ----
bgRadius   = 25;    // rolling-ball radius (px); should be larger than a nucleus
sigma      = 1.5;   // Gaussian smoothing (px)
localRad   = 15;    // local threshold radius (px); about one nucleus diameter
minArea    = 40;    // smallest object kept (px^2); removes debris
maxArea    = 1500;  // largest object kept (px^2); removes big bright blobs/clumps

setBatchMode(true);
open(input);
rename("orig");
run("Select None");
run("Remove Overlay");

// Work on a single 2D plane (use the current slice if it's a stack)
if (nSlices > 1) {
    run("Duplicate...", "title=work");
    selectWindow("orig"); close();
    selectWindow("work"); rename("orig");
}

// Make a processing copy and keep the original untouched
run("Duplicate...", "title=proc");
selectWindow("proc");
run("Properties...", "unit=pixel pixel_width=1 pixel_height=1 voxel_depth=1");

// Pre-processing: flatten background, smooth, convert to 8-bit
run("Subtract Background...", "rolling=" + bgRadius);
run("Gaussian Blur...", "sigma=" + sigma);
run("8-bit");

// Local threshold (handles uneven background and dim vs bright nuclei)
run("Auto Local Threshold", "method=Phansalkar radius=" + localRad + " parameter_1=0 parameter_2=0 white");

// Clean up the binary mask and split touching nuclei
setOption("BlackBackground", true);
run("Convert to Mask");
run("Fill Holes");
run("Open");
run("Watershed");

// Label objects: Analyze Particles + Count Masks gives a 16-bit label image
run("Set Measurements...", "area redirect=None decimal=3");
run("Analyze Particles...", "size=" + minArea + "-" + maxArea + " pixel show=[Count Masks] exclude clear");
rename("labels");

// Save (0 = background, 1..N = nuclei)
selectWindow("labels");
run("Grays");
saveAs("Tiff", output);

n = 0;
getStatistics(area, mean, min, max);
n = max;
print("Segmented nuclei: " + n);

run("Close All");
setBatchMode(false);
