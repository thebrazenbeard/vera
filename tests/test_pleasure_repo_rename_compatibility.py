"""Pleasure navigation must not rewrite frozen Orgasm V1 source contracts."""

import json
from pathlib import Path
import unittest

from runtime_cohesion.live_sources import validate_source_registry


ROOT = Path(__file__).resolve().parents[1]


class PleasureRepositoryRenameTests(unittest.TestCase):
    def test_current_repository_name_is_explicit_in_navigation(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        record = (ROOT / "docs/VERA_PLEASURE_REPOSITORY_RENAME_COMPAT_20261029.md").read_text(encoding="utf-8")
        self.assertIn("thebrazenbeard/pleasure", readme)
        self.assertIn("thebrazenbeard/pleasure", record)
        self.assertIn("pleasure/main", record)
        self.assertIn("thebrazenbeard/orgasm", record)

    def test_historical_registry_and_runtime_identifiers_remain_valid(self):
        registry = json.loads((ROOT / "architecture/VERA_RUNTIME_SOURCE_REGISTRY_V1.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_source_registry(registry), ())
        self.assertIn("thebrazenbeard/orgasm", registry["owner_repository_snapshot"])
        self.assertNotIn("thebrazenbeard/pleasure", registry["owner_repository_snapshot"])
        binding = json.loads((ROOT / "architecture/VERA_ORGASM_RUNTIME_BINDING_V1.json").read_text(encoding="utf-8"))
        self.assertEqual(binding["schema"], "VERA_ORGASM_RUNTIME_BINDING_V1")
        self.assertEqual(binding["source_path"], "vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json")
        self.assertTrue((ROOT / "runtime_cohesion/orgasm.py").is_file())


if __name__ == "__main__":
    unittest.main()
