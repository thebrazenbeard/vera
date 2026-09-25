import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ABSORPTION = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_ABSORPTION_V2.json"


class PortfolioAbsorptionV2Tests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(ABSORPTION.read_text(encoding="utf-8"))

    def test_exact_immutable_cut_is_bound(self):
        cut = self.manifest["immutable_cut"]
        self.assertEqual(cut["source_repository"], "thebrazenbeard/project-runner")
        self.assertEqual(cut["source_commit"], "6c8e6827a204380b40b7c7fa07d785ca53cec136")
        self.assertEqual(cut["corpus_blob_sha"], "886e9be586c37584c17afdc540c38a1d95deaaa6")
        self.assertEqual(cut["semantics"], "IMMUTABLE_DESCRIPTIVE_CUT_NOT_STANDING_CURRENTNESS")

    def test_cut_local_counts_reconcile_without_eternal_literal_assertion(self):
        cut = self.manifest["immutable_cut"]["counts"]
        public = self.manifest["public_inventory"]["repositories"]
        private = self.manifest["private_inventory"]
        self.assertEqual(len(public), cut["public"])
        self.assertEqual(private["count"], cut["private"])
        self.assertEqual(cut["total"], cut["public"] + cut["private"])
        self.assertIn("NOT_PERMANENT", self.manifest["cardinality_semantics"]["rule"])

    def test_private_membership_is_count_only(self):
        private = self.manifest["private_inventory"]
        self.assertFalse(private["exact_membership_publicly_committed"])
        self.assertEqual(private["membership_names_in_this_public_artifact"], [])
        self.assertEqual(private["public_commitment_scheme"], "COUNT_ONLY_PUBLIC_V1")

    def test_public_membership_is_complete_and_unique_for_cut(self):
        repos = [row["source_repository"] for row in self.manifest["public_inventory"]["repositories"]]
        self.assertEqual(len(repos), len(set(repos)))
        self.assertIn("thebrazenbeard/vera", repos)
        self.assertIn("thebrazenbeard/vera-mono", repos)
        self.assertIn("thebrazenbeard/sql-connectome", repos)
        self.assertIn("thebrazenbeard/fuckup", repos)

    def test_presence_never_auto_binds_runtime(self):
        for row in self.manifest["public_inventory"]["repositories"]:
            self.assertIn("NO_RUNTIME_DEPENDENCY_BY_PRESENCE", row["runtime_dependency_rule"])


if __name__ == "__main__":
    unittest.main()
