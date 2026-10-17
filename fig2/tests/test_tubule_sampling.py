"""Fig. 2e sampling and width measurement on synthetic data (code audit P0.5)."""
import importlib.util
import unittest

import numpy as np

from common.paths import REPO_ROOT

_spec = importlib.util.spec_from_file_location("tubule_width", REPO_ROOT / "fig2/code/tubule_width.py")
tw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tw)


class Sampling(unittest.TestCase):
    def test_horizontal_and_vertical_lines_are_sampled_equally(self):
        horizontal = np.array([[100, x] for x in range(20, 500)])
        vertical = np.array([[y, 100] for y in range(20, 500)])
        n_h = len(tw.sample_min_distance(horizontal, 12))
        n_v = len(tw.sample_min_distance(vertical, 12))
        self.assertEqual(n_h, n_v)
        self.assertEqual(n_h, 40)          # 480 px / 12 px

    def test_diagonal_line_has_comparable_density(self):
        diagonal = np.array([[20 + i, 20 + i] for i in range(480)])   # length 480 * sqrt(2)
        n = len(tw.sample_min_distance(diagonal, 12))
        self.assertAlmostEqual(n, 480 * np.sqrt(2) / 12, delta=3)

    def test_minimum_spacing_holds(self):
        rng = np.random.default_rng(0)
        pts = rng.integers(0, 200, size=(2000, 2))
        kept = tw.sample_min_distance(pts, 12).astype(float)
        d = np.hypot(*(kept[:, None, :] - kept[None, :, :]).transpose(2, 0, 1))
        np.fill_diagonal(d, np.inf)
        self.assertGreaterEqual(d.min(), 12)


class Width(unittest.TestCase):
    def test_fwhm_of_a_gaussian_profile(self):
        sigma = 3.0                         # in samples
        t = np.arange(-24, 25, 1.0)
        p = 100 * np.exp(-t ** 2 / (2 * sigma ** 2)) + 10
        self.assertAlmostEqual(tw.fwhm(p), 2 * np.sqrt(2 * np.log(2)) * sigma, delta=0.15)

    def test_undefined_width_is_nan(self):
        self.assertTrue(np.isnan(tw.fwhm(np.zeros(49))))
        self.assertTrue(np.isnan(tw.fwhm(np.linspace(0, 1, 49))))   # no peak inside the profile


if __name__ == "__main__":
    unittest.main()
