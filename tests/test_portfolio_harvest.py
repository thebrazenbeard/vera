import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
HARVEST=ROOT/"architecture/portfolio/VERA_PORTFOLIO_HARVEST_V1.json"
ABSORPTION=ROOT/"architecture/portfolio/VERA_PORTFOLIO_ABSORPTION_V1.json"

class PortfolioHarvestTests(unittest.TestCase):
    def setUp(self):
        self.harvest=json.loads(HARVEST.read_text(encoding="utf-8"))
        self.absorption=json.loads(ABSORPTION.read_text(encoding="utf-8"))

    def test_harvest_matches_named_public_cut(self):
        h={r["source_repository"] for r in self.harvest["repositories"]}
        a={r["source_repository"] for r in self.absorption["modules"]}
        self.assertEqual(h,a)
        self.assertEqual(len(h),49)
        self.assertEqual(self.harvest["portfolio_cut"]["binding"]["counts"]["total"],67)

    def test_private_harvest_is_count_only(self):
        p=self.harvest["private_harvest_summary"]
        self.assertEqual(p["member_count"],18)
        self.assertEqual(p["membership_disclosure"],"COUNT_ONLY_PUBLIC_V1")

    def test_every_public_repository_has_disposition(self):
        for row in self.harvest["repositories"]:
            self.assertTrue(row["harvest_status"])
            self.assertTrue(row["decision"])
            self.assertTrue(row["inspected_surface"])
            self.assertIn("SOURCE_ARCHITECTURE_ONLY",row["effect_ceiling"])

    def test_public_migrated_targets_exist(self):
        migrated=[r for r in self.harvest["repositories"] if r["harvest_status"]=="MIGRATED_CODE"]
        for row in migrated:
            for target in row["vera_targets"]:
                self.assertTrue((ROOT/target).exists(),target)

    def test_public_sibling_boundaries_are_not_migrations(self):
        rows={r["source_repository"]:r for r in self.harvest["repositories"]}
        for source in ("thebrazenbeard/unbound-sol","thebrazenbeard/vera-R9A0"):
            self.assertNotEqual(rows[source]["harvest_status"],"MIGRATED_CODE")

if __name__=="__main__":
    unittest.main()