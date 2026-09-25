import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "architecture" / "VERA_SYSTEM_MANIFEST_V2.json"
CONTROL = ROOT / "architecture" / "control" / "VERA_CONTROL_PLANE_ABSORPTION_V2.json"
BINDINGS = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_MIGRATION_BINDINGS_V2.json"


class PublicSuccessorNavigationTests(unittest.TestCase):
    def setUp(self):
        self.system = json.loads(SYSTEM.read_text(encoding="utf-8"))
        self.control = json.loads(CONTROL.read_text(encoding="utf-8"))
        self.bindings = json.loads(BINDINGS.read_text(encoding="utf-8"))

    def test_navigation_has_no_fixed_system_or_portfolio_count(self):
        semantics = self.system["navigation_semantics"]
        self.assertEqual(semantics["fixed_system_count"], "NONE")
        self.assertEqual(
            semantics["portfolio_cardinality"],
            "IMMUTABLE_CUT_FACT_NOT_PERMANENT_SYSTEM_INVARIANT",
        )
        self.assertNotIn("system_count", self.system)
        self.assertNotIn("portfolio_count", self.system)

    def test_control_mirror_is_exact_public_binding_subset(self):
        expected = [
            row for row in self.bindings["bindings"]
            if row["source_repository"] == "thebrazenbeard/vera-control-plane"
        ]
        actual = self.control["mirrored_sources"]
        self.assertEqual(self.control["mirrored_source_count"], len(actual))
        self.assertEqual(len(actual), len(expected))
        expected_pairs = {
            (row["source_path"], row["source_blob"], row["target_path"], row["target_blob"])
            for row in expected
        }
        actual_pairs = {
            (
                row["source_path"],
                row["source_blob_sha"],
                row["mirror_path"],
                row["mirror_blob_sha"],
            )
            for row in actual
        }
        self.assertEqual(actual_pairs, expected_pairs)

    def test_control_absorption_does_not_promote_install_or_runtime(self):
        transition = self.control["ownership_transition"]
        self.assertEqual(
            transition["current_release_authority"],
            "UNCHANGED_BY_THIS_SOURCE_CONSOLIDATION",
        )
        self.assertEqual(transition["project_installation"], "NOT_CLAIMED")
        self.assertEqual(transition["runtime_consumption"], "NOT_CLAIMED")


if __name__ == "__main__":
    unittest.main()
