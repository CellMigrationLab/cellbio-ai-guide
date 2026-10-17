"""Protocol v2 is frozen (fig3/v2/FREEZE.json): every file that defines it is unchanged, and no file was added to or
removed from the frozen set. A change must be undone or recorded in fig3/deviations.md with a new freeze record."""
import json
import unittest

from fig3.v2.freeze import V2, frozen_files, sha256


class Freeze(unittest.TestCase):
    def test_frozen_files_unchanged(self):
        record = json.loads((V2 / "FREEZE.json").read_text())
        self.assertEqual(sorted(record["files"]), sorted(frozen_files()), "files added to or removed from the freeze")
        changed = [f for f, digest in record["files"].items() if sha256(f) != digest]
        self.assertEqual(changed, [], "frozen protocol files changed")


if __name__ == "__main__":
    unittest.main()
