import json
from pathlib import Path
import unittest

from runtime_cohesion.failure import evaluate_failure_signature, validate_failure_wiring

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "architecture" / "VERA_RUNTIME_CONTRACT_V1.json").read_text(encoding="utf-8"))


class FailureWiringTests(unittest.TestCase):
    def test_current_failure_signatures_are_fully_wired(self):
        self.assertEqual(validate_failure_wiring(CONTRACT), [])

    def test_missing_required_signal_does_not_trigger_candidate(self):
        result = evaluate_failure_signature(
            "stale_stored_override",
            {"current_instruction": "current"},
            CONTRACT,
        )
        self.assertEqual(result.status, "NOT_TRIGGERED")
        self.assertIn("stored_state", result.missing_signals)

    def test_complete_resolver_signature_routes_candidate_to_declared_resolver(self):
        result = evaluate_failure_signature(
            "stale_stored_override",
            {"current_instruction": "current", "stored_state": "stored"},
            CONTRACT,
        )
        self.assertEqual(result.status, "CANDIDATE_TRIGGERED")
        self.assertEqual(result.predicate_id, "P_CURRENT_CONFLICTS_STORED")
        self.assertEqual(result.action, "DISPATCH_RESOLVER")
        self.assertEqual(result.target_ref, "resolver:current_user_instruction")
        self.assertFalse(result.predicate_proven)

    def test_complete_guard_signature_routes_candidate_to_fail_closed_guard(self):
        result = evaluate_failure_signature(
            "permission_promotion",
            {"explicit_permission_scope": "read", "requested_effect_scope": "write"},
            CONTRACT,
        )
        self.assertEqual(result.status, "CANDIDATE_TRIGGERED")
        self.assertEqual(result.action, "FAIL_CLOSED_GUARD")
        self.assertEqual(result.target_ref, "guard:exact-authority-scope")
        self.assertFalse(result.predicate_proven)

    def test_false_boolean_signal_does_not_trigger_candidate(self):
        result = evaluate_failure_signature(
            "source_install_collapse",
            {"source_available": True, "install_claim": False},
            CONTRACT,
        )
        self.assertEqual(result.status, "NOT_TRIGGERED")

    def test_unknown_signature_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unknown failure signature"):
            evaluate_failure_signature("does-not-exist", {}, CONTRACT)


if __name__ == "__main__":
    unittest.main()
