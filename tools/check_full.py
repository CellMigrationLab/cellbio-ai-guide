"""Full check: regenerate the Fig. 1 and Fig. 2 source data from data/raw in an emptied copy, then rebuild both figures.

Usage (from the repository root):  python tools/check_full.py [--with-models] [--with-squirrel]

What it does, in a temporary copy (the committed files are never modified):
1. Every file in fig1/source_data and fig2/source_data must be listed below, either as the output of a STEP or in
   NOT_REGENERATED with the reason. An unlisted file is a failure (so the inventory cannot silently go stale).
2. The outputs of every step that will run are deleted, so each step must find its inputs in data/raw or in the outputs
   of earlier steps; a missing input stops the check (no fallback to the committed copy).
3. The steps run in order; each output is compared with the committed file: TIFF by pixel values and dtype, JSON by
   content (documented extra keys ignored), everything else byte for byte.
4. Both figures are rebuilt from the regenerated source data and compared with the committed SVGs byte for byte.
5. The files that were not regenerated are reported with their reason, so the extent of the check is explicit.

Model steps (Cellpose-SAM, CPU, several minutes each; need cellpose and torch) run only with --with-models, and
SQUIRREL only with --with-squirrel (nanopyx must be importable by the same Python as the other requirements); otherwise their committed outputs are kept and reported as
not regenerated. `tools/check_all.py` is the fast check (committed source data -> figures and scores).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import tifffile

REPO = Path(__file__).resolve().parent.parent
COPY = ["common", "data", "fig1", "fig2"]          # folders the Fig. 1-2 code reads (data/raw is the only input)
FIGURES = {"fig1": ("code/make_fig1.py", "figure/fig1.svg"), "fig2": ("code/make_fig2.py", "figure/fig2.svg")}
KNOWN_EXTRA_KEYS = {("fig2", "panels/al_intensity.json"): {"r_pixel"},   # see fig2/README.md, caveats
                    ("fig2", "panels/squirrel.json"): {"s"}}            # runtime, no longer stored


@dataclass(frozen=True)
class Step:
    figure: str                    # fig1 or fig2; the step runs in <figure>/source_data
    script: str                    # script in <figure>/code, or "copy:<path relative to the repository>" for a copy
    outputs: tuple[str, ...]       # committed files it writes (relative to <figure>/source_data)
    args: tuple[str, ...] = ()
    needs: str = ""                # "", "models" or "squirrel": optional dependency that gates the step


STEPS = [
    # ---- Figure 1
    Step("fig1", "segment_bf_cellpose", ("full_field_labels/cellpose_sam_labels.tif",), needs="models"),
    Step("fig1", "classical_seg", ("full_field_labels/threshold_labels.tif", "panel_c_steps2_4/rep_classical.json")),
    Step("fig1", "f1_scores", ("panel_c_step3/A_scores.json",)),
    Step("fig1", "export_rep_window", ("panel_c_step3/B_rep_bf.png", "panel_c_step3/B_rep_cellpose.json",
                                       "panel_c_step3/B_rep_ref.json", "panel_c_step3/B_rep_stardist.json")),
    Step("fig1", "export_fresh_field", ("panel_c_step4/step4_scores.json", "panel_c_step4/test_bf.png",
                                        "panel_c_step4/test_ref.json", "panel_c_step4/test_stardist.json")),
    Step("fig1", "segment_panelA", ("panel_b/panelA_acquired_crop.png",), needs="models"),
    Step("fig1", "export_splits", ("panel_a/split_cells.png", "panel_a/split_denoise.png", "panel_a/split_label.png",
                                   "panel_a/split_sr_zoom.png"), needs="models"),  # reads segment_panelA's labels
    # ---- Figure 2
    Step("fig2", "copy:fig1/source_data/panel_c_step3/B_rep_bf.png", ("from_fig1_panel_c/B_rep_bf.png",)),
    Step("fig2", "copy:fig1/source_data/panel_c_step3/B_rep_ref.json", ("from_fig1_panel_c/B_rep_ref.json",)),
    Step("fig2", "norm_inputs", ()),                                     # panels/in_*.tif, inputs of cellpose_perturb
    Step("fig2", "cellpose_perturb", tuple(f"panels/cp_{r}.tif" for r in (
        "file_minmax", "file_histeq", "file_clahe", "nonorm", "down4", "down2", "up2", "flow0.8", "cellprob2")),
         args=("file_minmax", "file_histeq", "file_clahe", "nonorm", "down4", "down2", "up2", "flow0.8", "cellprob2"),
         needs="models"),
    Step("fig2", "postfilter", ("panels/cp_postfilter.tif",), args=("--threshold", "50")),
    # panel a on field 209 (same settings, threshold chosen on field 104); bars show the mean of the two fields
    Step("fig2", "norm_inputs", (), args=("--field", "209")),          # panels/field209/in_*.tif (not stored)
    Step("fig2", "cellpose_perturb", tuple(f"panels/field209/cp_{r}.tif" for r in (
        "default", "file_minmax", "file_histeq", "file_clahe", "nonorm", "down4", "down2", "up2", "flow0.8", "cellprob2")),
         args=("--field", "209", "default", "file_minmax", "file_histeq", "file_clahe", "nonorm", "down4", "down2", "up2",
               "flow0.8", "cellprob2"), needs="models"),
    Step("fig2", "postfilter", ("panels/field209/cp_postfilter.tif",), args=("--field", "209", "--threshold", "50")),
    Step("fig2", "errors", ("panels/err_ids_cellpose_default.json", "panels/err_ids_stardist.json")),
    Step("fig2", "score_perturb", ("panels/error_summary.json", "panels/perturb_scores.json") + tuple(
        f"panels/ts_cp_{r}.json" for r in ("cellprob2", "default", "down2", "down4", "file_clahe", "file_histeq",
                                           "file_minmax", "flow0.8", "nonorm", "postfilter", "up2"))),
    Step("fig2", "score_fields", ("panels/perturb_scores_fields.json",)),
    Step("fig2", "export_errors_window", ("panels/err_bf.png", "panels/err_cellpose_filtered.json",
                                          "panels/err_markers.json", "panels/err_ref.json", "panels/err_stardist.json")),
    Step("fig2", "annot_agree", ("panels/annot_agree.json", "panels/pecam_annotator1.json",
                                 "panels/pecam_annotator2.json", "panels/pecam_tile.png")),
    Step("fig2", "image_generation", ("panels/dn_acquired.png", "panels/dn_intensity.json", "panels/dn_mask.json",
                                      "panels/dn_restored.png", "panels/sr_hr.png", "panels/sr_hr_crop.npy",
                                      "panels/sr_input.png", "panels/sr_pred_crop.npy", "panels/sr_predicted.png",
                                      "panels/sr_profile.json")),
    Step("fig2", "al_roi", ("panels/roi.json", "panels/roi_acq.png", "panels/roi_annot1_cells.json",
                            "panels/roi_annot2_cells.json", "panels/roi_manual_nuclei.json",
                            "panels/roi_model_cells.json", "panels/roi_model_nuclei.json", "panels/roi_pred.png")),
    Step("fig2", "al_gray", ("panels/roi_dapi_split.png", "panels/roi_pecam_split.png")),
    Step("fig2", "al_intensity", ("panels/al_bf_full.png", "panels/al_intensity.json", "panels/al_pred_full.png")),
    Step("fig2", "tubule_width", ("panels/tubule_width.json",)),
    Step("fig2", "bio_result", ("panels/bio_result.json",)),
    Step("fig2", "squirrel_run", ("panels/squirrel.json", "panels/squirrel_high_res.tif",
                                  "panels/squirrel_predicted.tif"), needs="squirrel"),
    Step("fig2", "squirrel_tile", ("panels/sr_squirrel.png", "panels/inferno_bar.png")),
]

NOT_REGENERATED = {  # (figure, file) -> reason; these files are kept from the commit
    ("fig1", "panel_a/detect_input.png"): "recovered inline command (code/recovered_inline/data5_detect_input.png.sh)",
    ("fig1", "panel_a/detect_boxes.json"): "recovered inline command (code/recovered_inline/data5_detect_boxes.json.sh)",
    ("fig1", "panel_a/split_classif.png"): "recovered inline command (code/recovered_inline/data5_split_classif.png.sh)",
    ("fig1", "panel_c_steps2_4/rep0.png"): "producer not recovered (crop coordinates in fig1/README.md)",
    ("fig1", "panel_c_steps2_4/rep1.png"): "producer not recovered (crop coordinates in fig1/README.md)",
    ("fig1", "panel_c_steps2_4/rep2.png"): "producer not recovered (crop coordinates in fig1/README.md)",
    ("fig1", "panel_c_step5/trackmate_crop.png"): "recovered inline command (code/recovered_inline/data9_trackmate_crop.png.sh)",
    ("fig2", "from_fig1_panel_a/dark_tile.png"): "recovered inline command (code/recovered_inline/data5_dark_tile.png.sh)",
}


def report(name: str, ok: bool, detail: str = "") -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {name}{('  ' + detail) if detail else ''}", flush=True)
    return ok


def same_content(a: Path, b: Path, extra_keys: set[str]) -> bool:
    """TIFF: same dtype and pixels; JSON: same content without the documented extra keys; otherwise same bytes."""
    if a.suffix == ".tif":
        x, y = tifffile.imread(a), tifffile.imread(b)
        return x.dtype == y.dtype and np.array_equal(x, y)
    if a.suffix == ".json":
        def load(p: Path) -> object:
            d = json.loads(p.read_text())
            for v in (d.values() if isinstance(d, dict) else []):
                if isinstance(v, dict):
                    for k in extra_keys:
                        v.pop(k, None)
            return d
        return load(a) == load(b)
    return a.read_bytes() == b.read_bytes()


def check_inventory(steps: list[Step]) -> bool:
    """Every committed source-data file (git ls-files) must be a step output or listed in NOT_REGENERATED, and vice versa."""
    listed = {(s.figure, o) for s in steps for o in s.outputs} | set(NOT_REGENERATED)
    committed = subprocess.run(["git", "ls-files", *(f"{fig}/source_data" for fig in FIGURES)], cwd=REPO,
                               capture_output=True, text=True, check=True).stdout.split()
    present = {(c.split("/", 1)[0], c.split("/source_data/", 1)[1]) for c in committed}
    unlisted, missing = sorted(present - listed), sorted(listed - present)
    detail = (f"unlisted: {unlisted} " if unlisted else "") + (f"listed but absent: {missing}" if missing else "")
    return report(f"inventory: {len(present)} source-data files, each produced by a step or listed with a reason",
                  not unlisted and not missing, detail)


def run_step(step: Step, tmp: Path) -> subprocess.CompletedProcess | None:
    src = tmp / step.figure / "source_data"
    if step.script.startswith("copy:"):
        shutil.copyfile(tmp / step.script[5:], src / step.outputs[0])
        return None
    env = dict(os.environ, PYTHONPATH=f"{tmp}{os.pathsep}{tmp / step.figure / 'code'}")
    return subprocess.run([sys.executable, "-W", "ignore", f"../code/{step.script}.py", *step.args], cwd=src, env=env,
                          capture_output=True, text=True)


def main(with_models: bool, with_squirrel: bool) -> None:
    enabled = {"": True, "models": with_models, "squirrel": with_squirrel}
    results = [check_inventory(STEPS)]
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        for folder in COPY:
            shutil.copytree(REPO / folder, tmp / folder, ignore=shutil.ignore_patterns("__pycache__"))
        to_run = [s for s in STEPS if enabled[s.needs]]
        for s in to_run:                                   # empty the copy: delete every output that will be rebuilt
            for o in s.outputs:
                (tmp / s.figure / "source_data" / o).unlink()
        for s in to_run:
            proc = run_step(s, tmp)
            if proc is not None and proc.returncode:
                results.append(report(f"{s.figure}: {s.script}", False, proc.stderr.strip()[-400:]))
                break                                      # later steps would read missing inputs
            differ = [o for o in s.outputs
                      if not same_content(tmp / s.figure / "source_data" / o, REPO / s.figure / "source_data" / o,
                                          KNOWN_EXTRA_KEYS.get((s.figure, o), set()))]
            results.append(report(f"{s.figure}: {s.script} regenerates {len(s.outputs)} file(s)", not differ,
                                  f"differ: {differ}" if differ else ""))
        else:
            for fig, (builder, output) in FIGURES.items():
                proc = subprocess.run([sys.executable, f"../{builder}"], cwd=tmp / fig / "source_data",
                                      capture_output=True, text=True)
                same = proc.returncode == 0 and hashlib.sha256((tmp / fig / output).read_bytes()).hexdigest() == \
                    hashlib.sha256((REPO / fig / output).read_bytes()).hexdigest()
                results.append(report(f"{fig}: SVG rebuilt from regenerated source data is byte-identical", same,
                                      proc.stderr.strip()[-300:] if proc.returncode else ""))
    skipped = [(s.figure, o, f"needs --with-{s.needs}") for s in STEPS if not enabled[s.needs] for o in s.outputs]
    kept = skipped + [(f, o, r) for (f, o), r in NOT_REGENERATED.items()]
    print(f"\nNot regenerated ({len(kept)} files, committed copies used):")
    for fig, o, reason in kept:
        print(f"  {fig}/source_data/{o}: {reason}")
    print(f"\n{sum(results)}/{len(results)} checks passed")
    raise SystemExit(0 if all(results) else 1)


if __name__ == "__main__":
    args = sys.argv[1:]
    main("--with-models" in args, "--with-squirrel" in args)
