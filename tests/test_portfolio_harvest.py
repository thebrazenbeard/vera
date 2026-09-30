import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HARVEST = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_HARVEST_V1.json"
ABSORPTION = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_ABSORPTION_V1.json"


class PortfolioHarvestTests(unittest.TestCase):
    def setUp(self):
        self.harvest = json.loads(HARVEST.read_text(encoding="utf-8"))
        self.absorption = json.loads(ABSORPTION.read_text(encoding="utf-8"))

    def test_harvest_covers_live_absorption_cut(self):
        harvested = {row["source_repository"] for row in self.harvest["repositories"]}
        absorbed = {row["source_repository"] for row in self.absorption["modules"]}
        self.assertEqual(harvested, absorbed)
        self.assertEqual(65, self.harvest["portfolio_count"])
        self.assertEqual(65, len(harvested))

    def test_every_repository_has_a_real_disposition(self):
        for row in self.harvest["repositories"]:
            self.assertTrue(row["harvest_status"])
            self.assertTrue(row["decision"])
            self.assertTrue(row["inspected_surface"])
            self.assertIn("SOURCE_ARCHITECTURE_ONLY", row["effect_ceiling"])

    def test_migrated_code_targets_exist(self):
        migrated = [row for row in self.harvest["repositories"] if row["harvest_status"] == "MIGRATED_CODE"]
        self.assertEqual(
            {
                "thebrazenbeard/project-lantern",
                "thebrazenbeard/vera-works",
                "thebrazenbeard/skeletonkey",
                "thebrazenbeard/Attune",
                "thebrazenbeard/roots",
                "thebrazenbeard/intranel",
            },
            {row["source_repository"] for row in migrated},
        )
        for row in migrated:
            self.assertTrue(row["vera_targets"])
            for target in row["vera_targets"]:
                self.assertTrue((ROOT / target).exists(), target)

    def test_sibling_and_archive_boundaries_are_not_code_migration(self):
        rows = {row["source_repository"]: row for row in self.harvest["repositories"]}
        for source in (
            "thebrazenbeard/brigit",
            "thebrazenbeard/brigit-unbound",
            "thebrazenbeard/unbound-sol",
            "thebrazenbeard/vera-R9A0",
            "thebrazenbeard/conditioning",
            "thebrazenbeard/self",
        ):
            self.assertNotEqual(rows[source]["harvest_status"], "MIGRATED_CODE")


if __name__ == "__main__":
    unittest.main()
