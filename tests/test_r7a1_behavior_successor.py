from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import validate_portable_project_bootstrap as bootstrap
from scripts import validate_r7a1_behavior_successor as successor

bootstrap.TEMPLATE_ID = successor.TEMPLATE_ID
from tests import test_portable_project_bootstrap as base_tests
base_tests.validator.TEMPLATE_ID = successor.TEMPLATE_ID

ROOT = Path(__file__).resolve().parents[1]


class R7A1BehaviorSuccessorTests(unittest.TestCase):
    def test_successor_contract(self) -> None:
        successor.validate_successor(ROOT)

    def test_unique_project_names(self) -> None:
        manifest = successor.load_json(ROOT / bootstrap.MANIFEST_PATH)
        names = [item["filename"] for item in manifest["project_file_bundle"]["files"]]
        self.assertEqual(len(names), 21)
        self.assertEqual(len(set(names)), 21)
        self.assertTrue(all(name.startswith("VERA_R7A1_") for name in names))
        self.assertFalse(any("(1)" in name for name in names))

    def test_retry_policy(self) -> None:
        root = ROOT / successor.RELEASE_DIR
        combined = "\n".join(
            (root / name).read_text(encoding="utf-8")
            for name in ("VERA_R7A1_LAWS.md", "VERA_R7A1_PROJECT_INSTRUCTIONS.md", "VERA_R7A1_RUNTIME.md")
        ).lower()
        for fragment in ("same-route retry", "independent alternate route", "verify commit state", "never blindly repeat"):
            self.assertIn(fragment, combined)


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None):
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(base_tests))
    suite.addTests(loader.loadTestsFromTestCase(R7A1BehaviorSuccessorTests))
    return suite
