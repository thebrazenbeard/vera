import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BINDINGS = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_MIGRATION_BINDINGS_V2.json"
CUT = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_PUBLIC_CUT_V2.json"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


class PublicMigrationBindingsV2Tests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(BINDINGS.read_text(encoding="utf-8"))
        self.cut = json.loads(CUT.read_text(encoding="utf-8"))

    def test_every_binding_is_public_and_exact(self):
        public = {row["repository"] for row in self.cut["public_repositories"]}
        rows = self.manifest["bindings"]
        self.assertEqual(self.manifest["exact_copy_count"], len(rows))
        self.assertEqual(self.manifest["non_exact_count"], 0)
        self.assertEqual(self.manifest["private_source_bindings_in_public_manifest"], 0)
        for row in rows:
            self.assertIn(row["source_repository"], public)
            self.assertEqual(row["transfer_kind"], "EXACT_GIT_BLOB_COPY")
            self.assertTrue(row["verified_blob_equal"])
            self.assertEqual(row["source_blob"], row["target_blob"])
            target = ROOT / row["target_path"]
            self.assertTrue(target.is_file(), row["target_path"])
            self.assertEqual(git_blob_sha(target), row["target_blob"])

    def test_binding_freshness_is_explicit_not_implied(self):
        for row in self.manifest["bindings"]:
            self.assertIn(
                row["binding_freshness"],
                {
                    "SOURCE_HEAD_UNCHANGED_SINCE_PR200_HARVEST",
                    "IMMUTABLE_PR200_HARVEST_SOURCE_CUT_HEAD_HAS_SINCE_MOVED",
                },
            )
            self.assertRegex(row["source_current_head"], r"^[0-9a-f]{40}$")

    def test_predecessor_pr200_is_provenance_not_current_authority(self):
        predecessor = self.manifest["predecessor"]
        self.assertEqual(predecessor["pull_request"], 200)
        self.assertRegex(predecessor["head"], r"^[0-9a-f]{40}$")
        self.assertIn("immutable", self.manifest["freshness_rule"].lower())
        self.assertIn("not", self.manifest["claim_ceiling"].lower())


if __name__ == "__main__":
    unittest.main()
