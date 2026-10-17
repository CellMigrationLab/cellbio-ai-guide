"""Regression test: the shared scorer reproduces a published number from the raw data in this repository."""
import unittest

import tifffile

from common.matching import f1_score
from common.paths import raw_file


class PublishedScoreTests(unittest.TestCase):
    def test_fig1_custom_stardist_f1(self):
        """Fig 1c / Fig 2: custom StarDist vs manual cancer-cell annotation, F1 0.858 (97 TP, 27 FN, 5 FP)."""
        gt = tifffile.imread(raw_file("field104_cancer_cells_manual_labels.tif")).astype(int)
        pr = tifffile.imread(raw_file("field104_cancer_cells_stardist_custom_labels.tif")).astype(int)
        s = f1_score(gt, pr)
        self.assertEqual((s["tp"], s["fn"], s["fp"], s["f1"]), (97, 27, 5, 0.858))


if __name__ == "__main__":
    unittest.main()
