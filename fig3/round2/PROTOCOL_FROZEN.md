# Round-2 protocol frozen (17 Oct 2026, before any run)

Frozen at commit `725e484397df703d29581d7bb044364599398db7` (local tag `fig3-round2-protocol`; the tag could not be pushed through this environment's
git proxy, so the freeze is recorded here instead). `protocol_freeze.csv` lists the SHA-256 of every file that defines
the protocol: Box 1, the 30 prompts, `scenarios.csv` (run order, seed 20261017), the answer sheet, the operator rules,
the scorers and the image assets. `fig3/tests/test_protocol_freeze.py` (run by `make check`) fails if any of them
changes. A change after this point is a protocol deviation: record it in `fig3/deviations.md` with the reason and the
scenarios affected, and update the freeze file in the same commit.
