"""The round-2 protocol files must match the hashes recorded when it was frozen (fig3/round2/PROTOCOL_FROZEN.md)."""
import csv
import hashlib
import unittest

from common.paths import REPO_ROOT

FREEZE = REPO_ROOT / "fig3/round2/protocol_freeze.csv"


class ProtocolFreeze(unittest.TestCase):
    def test_protocol_files_unchanged(self):
        with FREEZE.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertGreater(len(rows), 0)
        changed = [r["path"] for r in rows
                   if hashlib.sha256((REPO_ROOT / r["path"]).read_bytes()).hexdigest() != r["sha256"]]
        self.assertEqual(changed, [], "protocol files changed after freezing; see fig3/round2/PROTOCOL_FROZEN.md")


if __name__ == "__main__":
    unittest.main()
