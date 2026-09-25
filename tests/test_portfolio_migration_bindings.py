import json
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
BINDINGS=ROOT/"architecture/portfolio/VERA_PORTFOLIO_MIGRATION_BINDINGS_V1.json"

def git_blob_sha(path):
    rel = path.relative_to(ROOT).as_posix()
    return subprocess.check_output(
        ["git", "hash-object", "--path", rel, str(path)],
        cwd=ROOT,
        text=True,
    ).strip()

class PortfolioMigrationBindingTests(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads(BINDINGS.read_text(encoding="utf-8"))

    def test_public_declared_exact_copies_are_exact(self):
        rows=self.manifest["bindings"]
        self.assertEqual(len(rows),self.manifest["exact_copy_count"])
        self.assertEqual(0,self.manifest["non_exact_count"])
        for row in rows:
            self.assertEqual(row["transfer_kind"],"EXACT_GIT_BLOB_COPY")
            self.assertTrue(row["verified_blob_equal"])
            self.assertEqual(row["source_blob"],row["target_blob"])
            target=ROOT/row["target_path"]
            self.assertTrue(target.is_file(),row["target_path"])
            self.assertEqual(git_blob_sha(target),row["target_blob"])

    def test_private_binding_provenance_is_aggregate_only(self):
        p=self.manifest["private_provenance_summary"]
        self.assertGreater(p["redacted_exact_binding_count"],0)
        self.assertEqual(p["membership_disclosure"],"COUNT_ONLY_PUBLIC_V1")

    def test_control_plane_public_mirror_remains_exact(self):
        rows=[r for r in self.manifest["bindings"] if r["source_repository"]=="thebrazenbeard/vera-control-plane"]
        self.assertEqual(len(rows),24)

    def test_discovery_derivation_remains_labeled(self):
        d=self.manifest["derived_integrations"]
        self.assertEqual(len(d),1)
        self.assertEqual(d[0]["source_repository"],"thebrazenbeard/discovery")
        self.assertEqual(d[0]["transfer_kind"],"DERIVED_ARCHITECTURE")

if __name__=="__main__":
    unittest.main()