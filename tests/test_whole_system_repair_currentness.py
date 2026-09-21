from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WholeSystemRepairCurrentnessTests(unittest.TestCase):
    def test_currentness_manifest_refuses_installed_release_guess(self):
        data = json.loads(
            (ROOT / "architecture" / "VERA_LIVE_CURRENTNESS_AUTHORITY_MANIFEST_V1.json")
            .read_text(encoding="utf-8")
        )
        governing = data["governing_release_resolution"]
        self.assertEqual("UNKNOWN", governing["exact_release_id"])
        self.assertEqual("UNAVAILABLE", governing["exact_installation_receipt"])
        self.assertEqual("BLOCKED_EXTERNAL", governing["resolution"])
        self.assertFalse(
            any(item["installation_promotion"] for item in data["project_file_observations"])
        )

    def test_pr_classification_is_complete_and_typed(self):
        data = json.loads(
            (ROOT / "state" / "whole-system-repair" / "VERA_OPEN_PR_CLASSIFICATION_V1.json")
            .read_text(encoding="utf-8")
        )
        rows = data["pull_requests"]
        self.assertEqual(20, len(rows))
        self.assertEqual(20, len({row["number"] for row in rows}))
        allowed = set(data["allowed_classifications"])
        self.assertTrue(all(row["classification"] in allowed for row in rows))
        by_number = {row["number"]: row for row in rows}
        self.assertNotIn(153, by_number)
        self.assertEqual(153, data["recently_closed"][0]["number"])
        self.assertTrue(data["recently_closed"][0]["closed_state_verified"])
        self.assertEqual("STACKED_DEPENDENCY", by_number[147]["classification"])
        self.assertEqual("REVIEW_BLOCKED", by_number[148]["classification"])

    def test_readme_does_not_claim_stale_installed_r10a0_or_old_active_branch(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("native control root is **R10A0 / R10**", text)
        self.assertNotIn(
            "The active design branch `work/vera-runtime-cohesion-v1-20260908`",
            text,
        )
        self.assertIn("exact installed native control release is currently **UNKNOWN**", text)


if __name__ == "__main__":
    unittest.main()
