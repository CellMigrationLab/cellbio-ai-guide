"""Input guards added after the 19 Oct 2026 audit: invalid dtypes, 2D statistics samples and paths outside data/raw."""
import unittest

import numpy as np

from common.labels import InvalidLabels, validate_labels
from common.paths import raw_file
from common.stats import finite_values, pearson_r


class Guards(unittest.TestCase):
    def test_complex_labels_are_rejected(self):
        a = np.array([[0 + 0j, 3 + 0.4j]])
        with self.assertRaises(InvalidLabels):
            validate_labels(a)

    def test_2d_statistics_sample_is_rejected(self):
        xy = np.array([[1.0, 2.0], [2.0, 4.0], [3.0, 6.0]])
        with self.assertRaises(ValueError):
            finite_values(xy, name="pairs")
        with self.assertRaises(ValueError):
            pearson_r(xy, xy, name="pairs")     # used to return 1.0 after silently flattening

    def test_raw_file_confines_to_data_raw(self):
        with self.assertRaises(FileNotFoundError):
            raw_file("/tmp/field104_cancer_cells_manual_labels.tif")
        with self.assertRaises(FileNotFoundError):
            raw_file("../outside.tif")


if __name__ == "__main__":
    unittest.main()
