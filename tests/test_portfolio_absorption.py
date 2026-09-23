import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ABSORPTION = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_ABSORPTION_V1.json"
REGISTRY = ROOT / "architecture" / "VERA_RUNTIME_SOURCE_REGISTRY_V1.json"
CONTROL = ROOT / "architecture" / "control" / "VERA_CONTROL_PLANE_ABSORPTION_V1.json"
CAPABILITIES = ROOT / "architecture" / "portfolio" / "VERA_PORTFOLIO_CAPABILITY_ARCHITECTURE_V1.json"


class PortfolioAbsorptionTests(unittest.TestCase):
    def setUp(self):
        self.absorption = json.loads(ABSORPTION.read_text(encoding="utf-8"))
        self.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.control = json.loads(CONTROL.read_text(encoding="utf-8"))
        self.capabilities = json.loads(CAPABILITIES.read_text(encoding="utf-8"))

    def test_absorption_covers_exact_runtime_portfolio_snapshot(self):
        modules = self.absorption["modules"]
        module_repos = {row["source_repository"] for row in modules}
        snapshot = set(self.registry["owner_repository_snapshot"])
        self.assertEqual(module_repos, snapshot)
        self.assertEqual(self.absorption["portfolio_count"], len(snapshot))
        self.assertEqual(65, len(snapshot))

    def test_every_module_is_owned_inside_vera_without_presence_activation(self):
        for row in self.absorption["modules"]:
            self.assertEqual(row["internal_owner_repository"], "thebrazenbeard/vera")
            self.assertEqual(row["absorption_mode"], "VERA_INTERNAL_ARCHITECTURE_MODULE")
            self.assertIn("NO_RUNTIME_DEPENDENCY_BY_PRESENCE", row["runtime_dependency_rule"])

    def test_control_plane_is_absorbed_but_not_falsely_promoted(self):
        modules = {row["source_repository"]: row for row in self.absorption["modules"]}
        self.assertIn("thebrazenbeard/vera-control-plane", modules)
        self.assertEqual(self.control["owner_repository"], "thebrazenbeard/vera")
        self.assertEqual(self.control["upstream_repository"], "thebrazenbeard/vera-control-plane")
        self.assertEqual(
            self.control["ownership_transition"]["current_release_authority"],
            "UNCHANGED_BY_THIS_SOURCE_ABSORPTION",
        )
        for binding in self.control["mirrored_sources"]:
            self.assertTrue((ROOT / binding["mirror_path"]).is_file())

    def test_sibling_identity_does_not_transfer_into_vera(self):
        modules = {row["source_repository"]: row for row in self.absorption["modules"]}
        sol = modules["thebrazenbeard/unbound-sol"]
        self.assertEqual(sol["source_activation_mode"], "NO_IDENTITY_TRANSFER")
        self.assertIn("do not transfer to Vera", sol["source_authority_ceiling"])


    def test_every_source_maps_to_internal_capability_plane(self):
        modules = self.capabilities["modules"]
        self.assertEqual(65, len(modules))
        self.assertEqual(
            {row["source_repository"] for row in self.absorption["modules"]},
            {row["source_repository"] for row in modules},
        )
        for row in modules:
            self.assertTrue(row["capability_planes"])
            self.assertNotIn("SPECIALIST_OR_FUTURE_MODULE", row["capability_planes"])
        self.assertEqual(
            [],
            self.capabilities["planes"]["SPECIALIST_OR_FUTURE_MODULE"]["module_ids"],
        )
        self.assertEqual(
            ["VERA_PORTFOLIO_MODULE__CCB_CORE"],
            self.capabilities["planes"]["UNRESOLVED_EMPTY_REPOSITORY"]["module_ids"],
        )

    def test_new_portfolio_sources_are_present(self):
        modules = {row["source_repository"] for row in self.absorption["modules"]}
        self.assertTrue({
            "thebrazenbeard/meso-crct",
            "thebrazenbeard/unbound-sol",
            "thebrazenbeard/RepairTracker",
            "thebrazenbeard/freerowcochkar",
            "thebrazenbeard/identify-ai",
            "thebrazenbeard/ccb-core",
        }.issubset(modules))


if __name__ == "__main__":
    unittest.main()
