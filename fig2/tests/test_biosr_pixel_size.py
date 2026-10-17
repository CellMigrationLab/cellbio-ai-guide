"""BioSR pixel sizes (audit P0.6): the prediction and high-res reference sit on a 2x grid of the low-res input,
so their pixel is half the input pixel (62.6 nm -> 31.3 nm); every stored value must agree with that."""
import json
import unittest

import tifffile

from common.paths import REPO_ROOT, raw_file

LOWRES_PX_NM = 62.6
GRID_PX_NM = 31.3


class BioSRPixelSize(unittest.TestCase):
    def test_prediction_and_reference_are_on_the_2x_grid(self):
        lr = tifffile.TiffFile(raw_file("biosr_er_lowres_input.tif")).pages[0].shape
        for name in ("biosr_er_rcan_prediction.tif", "biosr_er_highres_reference.tif"):
            shape = tifffile.TiffFile(raw_file(name)).pages[0].shape
            self.assertEqual(shape, (2 * lr[0], 2 * lr[1]), name)
        self.assertAlmostEqual(LOWRES_PX_NM / 2, GRID_PX_NM, places=6)

    def test_stored_profile_metadata(self):
        profile = json.loads((REPO_ROOT / "fig2/source_data/panels/sr_profile.json").read_text())
        self.assertEqual(profile["px_nm"], GRID_PX_NM)
        self.assertEqual(profile["lowres_px_nm"], LOWRES_PX_NM)

    def test_tubule_width_uses_the_2x_grid(self):
        width = json.loads((REPO_ROOT / "fig2/source_data/panels/tubule_width.json").read_text())
        self.assertEqual(width["summary"]["px_nm_assumed"], GRID_PX_NM)


if __name__ == "__main__":
    unittest.main()
