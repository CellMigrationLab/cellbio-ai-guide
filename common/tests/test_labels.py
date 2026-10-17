"""common.labels rejects anything that is not an instance label image."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import tifffile

from common.labels import InvalidLabels, read_labels, validate_labels


class LabelValidation(unittest.TestCase):
    def test_valid_sparse_labels(self):
        a = np.zeros((8, 8), np.uint16)
        a[1:3, 1:3] = 7
        out = validate_labels(a)
        self.assertEqual(out.dtype, np.int64)
        self.assertTrue(np.array_equal(out, a))

    def test_integer_valued_float_is_accepted(self):
        self.assertEqual(validate_labels(np.array([[0.0, 2.0]])).tolist(), [[0, 2]])

    def test_invalid_inputs_raise(self):
        bad = {"probability map": np.array([[0.2, 0.9]]), "nan": np.array([[np.nan, 1.0]]),
               "inf": np.array([[np.inf, 1.0]]), "negative": np.array([[-1, 2]]),
               "3D stack": np.zeros((2, 4, 4), int), "bool": np.zeros((4, 4), bool)}
        for what, a in bad.items():
            with self.assertRaises(InvalidLabels, msg=what):
                validate_labels(a)

    def test_shape_and_squeeze(self):
        with self.assertRaises(InvalidLabels):
            validate_labels(np.zeros((4, 4), int), expected_shape=(4, 5))
        with self.assertRaises(InvalidLabels):
            validate_labels(np.zeros((1, 4, 4), int))
        self.assertEqual(validate_labels(np.zeros((1, 4, 4), int), squeeze=True).shape, (4, 4))

    def test_read_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "l.tif"
            tifffile.imwrite(p, np.arange(12, dtype=np.uint16).reshape(3, 4))
            self.assertEqual(read_labels(p, rows=slice(1, 3)).shape, (2, 4))
            with self.assertRaises(FileNotFoundError):
                read_labels(Path(tmp) / "missing.tif")


if __name__ == "__main__":
    unittest.main()
