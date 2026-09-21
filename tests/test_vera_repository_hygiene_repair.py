from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class VeraRepositoryHygieneRepairTests(unittest.TestCase):
    def test_pr_inventory_is_typed_and_collision_reconciled(self):
        data = json.loads(
            (ROOT / "state" / "whole-system-repair" / "VERA_OPEN_PR_CLASSIFICATION_V1.json")
            .read_text(encoding="utf-8")
        )
        rows = data["pull_requests"]
        self.assertEqual(data["counts"]["total"], len(rows))
        self.assertEqual(len(rows), len({row["number"] for row in rows}))
        allowed = set(data["allowed_classifications"])
        self.assertTrue(all(row["classification"] in allowed for row in rows))
        by_number = {row["number"]: row for row in rows}
        self.assertEqual("STACKED_DEPENDENCY", by_number[155]["classification"])
        self.assertEqual("SUPERSEDED", by_number[156]["classification"])
        self.assertEqual("STACKED_DEPENDENCY", by_number[147]["classification"])
        self.assertEqual("REVIEW_BLOCKED", by_number[148]["classification"])
        self.assertNotIn(153, by_number)
        self.assertTrue(data["recently_closed"][0]["closed_state_verified"])

    def test_readme_refuses_stale_release_and_branch_currentness(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("native control root is **R10A0 / R10**", text)
        self.assertNotIn(
            "The active design branch `work/vera-runtime-cohesion-v1-20260908`",
            text,
        )
        self.assertIn("exact installed native control release is currently **UNKNOWN**", text)
        self.assertIn(
            "architecture/VERA_LIVE_CURRENTNESS_AUTHORITY_MANIFEST_V1.json",
            text,
        )


if __name__ == "__main__":
    unittest.main()
