import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ABSORPTION = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_ABSORPTION_V1.json"
CAPABILITIES = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_CAPABILITY_ARCHITECTURE_V1.json"

class PortfolioAbsorptionTests(unittest.TestCase):
    def setUp(self):
        self.absorption=json.loads(ABSORPTION.read_text(encoding="utf-8"))
        self.capabilities=json.loads(CAPABILITIES.read_text(encoding="utf-8"))

    def test_public_safe_immutable_cut_binding(self):
        cut=self.absorption["portfolio_cut"]
        self.assertEqual(cut["binding"]["counts"], {"total":67,"public":49,"private":18})
        self.assertEqual(len(self.absorption["modules"]),49)
        self.assertEqual(cut["private_inventory"]["count"],18)
        self.assertFalse(cut["private_inventory"]["exact_membership_publicly_committed"])
        self.assertEqual(cut["private_inventory"]["public_commitment_scheme"],"COUNT_ONLY_PUBLIC_V1")

    def test_every_named_module_is_public_and_no_presence_activation(self):
        for row in self.absorption["modules"]:
            self.assertEqual(row["source_visibility"],"public")
            self.assertEqual(row["internal_owner_repository"],"thebrazenbeard/vera")
            self.assertIn("NO_RUNTIME_DEPENDENCY_BY_PRESENCE",row["runtime_dependency_rule"])

    def test_capability_architecture_matches_named_public_cut(self):
        a={r["source_repository"] for r in self.absorption["modules"]}
        c={r["source_repository"] for r in self.capabilities["modules"]}
        self.assertEqual(a,c)
        self.assertEqual(len(c),49)
        for row in self.capabilities["modules"]:
            self.assertTrue(row["capability_planes"])

    def test_new_cut_members_are_no_auto_bind_or_bounded(self):
        rows={r["source_repository"]:r for r in self.absorption["modules"]}
        for repo in ("thebrazenbeard/fuckup","thebrazenbeard/sql-connectome","thebrazenbeard/vera-mono"):
            self.assertIn(repo,rows)
            self.assertEqual(rows[repo]["source_activation_mode"],"NO_AUTO_BIND")

    def test_freshness_drift_does_not_rewrite_cut(self):
        fresh=self.absorption["portfolio_cut"]["freshness"]
        self.assertEqual(fresh["latest_connected_counts"]["total"],68)
        self.assertEqual(self.absorption["portfolio_cut"]["binding"]["counts"]["total"],67)
        self.assertIn("FRESHNESS_OBSERVATION_ONLY",fresh["semantics"])

if __name__=="__main__":
    unittest.main()