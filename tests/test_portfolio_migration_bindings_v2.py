import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BINDINGS = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_MIGRATION_BINDINGS_V2.json"
ABSORPTION = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_ABSORPTION_V2.json"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


class PortfolioMigrationBindingsV2Tests(unittest.TestCase):
    def setUp(self):
        self.bindings = json.loads(BINDINGS.read_text(encoding="utf-8"))
        self.absorption = json.loads(ABSORPTION.read_text(encoding="utf-8"))

    def test_all_named_donors_are_public_cut_members(self):
        public = {row["source_repository"] for row in self.absorption["public_inventory"]["repositories"]}
        for row in self.bindings["bindings"]:
            self.assertIn(row["source_repository"], public)

    def test_exact_copies_retain_blob_identity(self):
        rows = self.bindings["bindings"]
        self.assertEqual(len(rows), self.bindings["exact_copy_count"])
        self.assertEqual(self.bindings["non_exact_count"], 0)
        for row in rows:
            self.assertEqual(row["transfer_kind"], "EXACT_GIT_BLOB_COPY")
            self.assertEqual(row["source_blob"], row["target_blob"])
            target = ROOT / row["target_path"]
            self.assertTrue(target.is_file(), row["target_path"])
            self.assertEqual(git_blob_sha(target), row["target_blob"])

    def test_private_donor_membership_is_not_enumerated(self):
        self.assertFalse(self.bindings["private_donor_bindings_publicly_enumerated"])
        self.assertNotIn("private_bindings", self.bindings)


if __name__ == "__main__":
    unittest.main()
