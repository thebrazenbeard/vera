import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BINDINGS = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_MIGRATION_BINDINGS_V1.json"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


class PortfolioMigrationBindingTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(BINDINGS.read_text(encoding="utf-8"))

    def test_all_declared_exact_copies_are_exact(self):
        rows = self.manifest["bindings"]
        self.assertEqual(49, len(rows))
        self.assertEqual(49, self.manifest["exact_copy_count"])
        self.assertEqual(0, self.manifest["non_exact_count"])
        for row in rows:
            self.assertEqual(row["transfer_kind"], "EXACT_GIT_BLOB_COPY")
            self.assertTrue(row["verified_blob_equal"])
            self.assertEqual(row["source_blob"], row["target_blob"])
            target = ROOT / row["target_path"]
            self.assertTrue(target.is_file(), row["target_path"])
            self.assertEqual(git_blob_sha(target), row["target_blob"], row["target_path"])

    def test_control_plane_mirror_is_complete_for_bound_cut(self):
        vcp = [
            row for row in self.manifest["bindings"]
            if row["source_repository"] == "thebrazenbeard/vera-control-plane"
        ]
        self.assertEqual(24, len(vcp))
        paths = {row["source_path"] for row in vcp}
        self.assertIn("protocol/VERA_RESTORE_YOURSELF_PROTOCOL_V2.md", paths)
        self.assertIn(
            "project-instructions/r10a0/rounds/r10/VERA_R10A0_PUBLICATION_RECEIPT_R10.json",
            paths,
        )

    def test_derived_discovery_integration_is_not_mislabeled_as_exact_copy(self):
        derived = self.manifest["derived_integrations"]
        self.assertEqual(1, len(derived))
        self.assertEqual(derived[0]["source_repository"], "thebrazenbeard/discovery")
        self.assertEqual(derived[0]["transfer_kind"], "DERIVED_ARCHITECTURE")


if __name__ == "__main__":
    unittest.main()
