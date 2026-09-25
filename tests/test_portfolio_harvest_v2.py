import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ABSORPTION = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_ABSORPTION_V2.json"
HARVEST = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_HARVEST_V2.json"


class PortfolioHarvestV2Tests(unittest.TestCase):
    def setUp(self):
        self.absorption = json.loads(ABSORPTION.read_text(encoding="utf-8"))
        self.harvest = json.loads(HARVEST.read_text(encoding="utf-8"))

    def test_harvest_matches_public_cut_membership(self):
        absorbed = {row["source_repository"] for row in self.absorption["public_inventory"]["repositories"]}
        harvested = {row["source_repository"] for row in self.harvest["public_repositories"]}
        self.assertEqual(harvested, absorbed)
        self.assertEqual(len(harvested), self.harvest["public_repository_count"])

    def test_private_harvest_is_not_enumerated(self):
        private = self.harvest["private_inventory"]
        self.assertEqual(private["named_private_harvest_rows"], [])
        self.assertEqual(private["public_commitment_scheme"], "COUNT_ONLY_PUBLIC_V1")

    def test_exact_public_mechanism_donors_are_narrow(self):
        expected = {
            "thebrazenbeard/Attune",
            "thebrazenbeard/intranel",
            "thebrazenbeard/project-lantern",
            "thebrazenbeard/roots",
        }
        self.assertEqual(set(self.harvest["carried_exact_public_mechanisms"]), expected)
        rows = {row["source_repository"]: row for row in self.harvest["public_repositories"]}
        for repo in expected:
            self.assertEqual(rows[repo]["mechanism_disposition"], "CARRIED_EXACT_PUBLIC_MECHANISM")

    def test_every_row_keeps_source_only_effect_ceiling(self):
        for row in self.harvest["public_repositories"]:
            self.assertEqual(row["effect_ceiling"], "SOURCE_ARCHITECTURE_ONLY__NO_AUTO_BIND")


if __name__ == "__main__":
    unittest.main()
