from __future__ import annotations

import re
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


class R7A1BehaviorSuccessorTests(unittest.TestCase):
    def test_successor_contract(self) -> None:
        receipts = successor.validate_successor(ROOT)
        self.assertEqual(len(receipts), 24)
        self.assertTrue(all(item["result"] == "PASS" and item["skip"] == "false" for item in receipts))

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
        for fragment in (
            "same-route retry",
            "independent alternate route",
            "verify commit state",
            "never blindly repeat",
            "attempt timestamp",
        ):
            self.assertIn(fragment, combined)

    def test_current_state_is_manifest_bound_not_obsolete(self) -> None:
        text = (ROOT / successor.RELEASE_DIR / "VERA_R7A1_PROJECT_INSTRUCTIONS.md").read_text(encoding="utf-8")
        self.assertNotIn(successor.OBSOLETE_MAIN_SHA, text)
        self.assertIn(f"main@{successor.SOURCE_BASE_SHA}", text)
        self.assertIn("read GitHub when current repository state is material", text)


    def test_validation_scope_disclosure_fails_closed(self) -> None:
        validation = successor.load_yaml(
            ROOT / successor.RELEASE_DIR / "VERA_R7A1_VALIDATION.yaml"
        )
        execution = dict(validation["behavior_case_execution"])
        successor.validate_execution_scope(execution)
        execution["prompt_semantic_routing_coverage"] = "TESTED"
        with self.assertRaises(ValueError):
            successor.validate_execution_scope(execution)


    def test_behavior_adjudicator_rejects_missing_required_action(self) -> None:
        trace = successor.simulate_behavior_subject(
            "The user corrects the intended referent after the assistant followed the wrong interpretation.",
            {"correction": True, "concrete_act": True},
        )
        trace["actions"].remove("COMPLETE_CORRECTED_TASK")
        failures = successor.adjudicate_behavior_trace(
            trace, successor.BEHAVIOR_ASSERTIONS["POS-01-CORRECTION-UPTAKE"]
        )
        self.assertTrue(any("COMPLETE_CORRECTED_TASK" in item for item in failures))

    def test_behavior_adjudicator_rejects_high_stakes_sarcasm(self) -> None:
        receipt = successor.execute_behavior_case("HOST-08-HIGH-STAKES-SARCASM")
        trace = dict(receipt["observed"])
        trace["actions"] = list(trace["actions"]) + ["USE_SARCASM"]
        failures = successor.adjudicate_behavior_trace(
            trace, successor.BEHAVIOR_ASSERTIONS["HOST-08-HIGH-STAKES-SARCASM"]
        )
        self.assertTrue(any("USE_SARCASM" in item for item in failures))

    def test_behavior_adjudicator_rejects_blind_write_retry(self) -> None:
        receipt = successor.execute_behavior_case("HOST-14-BLIND-WRITE-RETRY")
        trace = dict(receipt["observed"])
        trace["actions"] = list(trace["actions"]) + ["BLINDLY_REPEAT_WRITE"]
        trace["attempts"] = list(trace["attempts"]) + [{"route_identity": "write:primary"}]
        failures = successor.adjudicate_behavior_trace(
            trace, successor.BEHAVIOR_ASSERTIONS["HOST-14-BLIND-WRITE-RETRY"]
        )
        self.assertTrue(any("BLINDLY_REPEAT_WRITE" in item or "attempt count" in item for item in failures))


def _make_case_test(case_id: str):
    def test(self: R7A1BehaviorSuccessorTests) -> None:
        successor.assert_case_execution(ROOT, case_id)
    test.__name__ = "test_case_" + re.sub(r"[^a-z0-9]+", "_", case_id.lower()).strip("_")
    return test


for _case in successor.EXPECTED_POSITIVE_CASES + successor.EXPECTED_HOSTILE_CASES:
    _method = _make_case_test(_case["id"])
    setattr(R7A1BehaviorSuccessorTests, _method.__name__, _method)


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None):
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(base_tests))
    suite.addTests(loader.loadTestsFromTestCase(R7A1BehaviorSuccessorTests))
    return suite
