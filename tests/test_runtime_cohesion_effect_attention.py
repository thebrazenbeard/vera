from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest

from runtime_cohesion.effect_attention import (
    build_effect_attention_view,
    load_effect_attention_contract,
    validate_effect_envelope,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "architecture" / "discovery" / "effect_attempt_envelope_v0.schema.json"
BINDING = ROOT / "architecture" / "discovery" / "VERA_DISCOVERY_EFFECT_ATTENTION_BINDING_V1.json"
MODULE = ROOT / "runtime_cohesion" / "effect_attention.py"
INIT = ROOT / "runtime_cohesion" / "__init__.py"


def committed_git_blob(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    return subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", f"HEAD:{rel}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def envelope(source: str, operation: str, phase: str, retry: str) -> dict:
    return {
        "schema_version": "DISCOVERY_EFFECT_ATTEMPT_V0",
        "source_system": source,
        "source_operation_id": operation,
        "source_state": "OPAQUE_NATIVE_STATE",
        "source_ref": "exact-source@0123456789abcdef0123456789abcdef01234567",
        "source_payload_sha256": "a" * 64,
        "action_class": "EXAMPLE_EFFECT",
        "target": {
            "kind": "example-target",
            "locator": f"example://{operation}",
            "expected_precondition": "generation=1",
        },
        "normalized_phase": phase,
        "retry_disposition": retry,
        "receipts": [{"kind": "native", "value": f"receipt-{operation}"}],
    }


class VeraEffectAttentionObserverTests(unittest.TestCase):
    def contract(self):
        return load_effect_attention_contract(SCHEMA)

    def test_vendored_schema_is_exact_discovery_v0_blob(self):
        self.assertEqual(
            committed_git_blob(SCHEMA),
            "b5d85ba31a33ad7192fd4a08934628a72e593312",
        )

    def test_second_observer_handles_three_producers_without_source_branching(self):
        report = build_effect_attention_view(
            [
                envelope(
                    "project-runner",
                    "runner-op",
                    "OUTCOME_UNKNOWN",
                    "INSPECT_BEFORE_RETRY",
                ),
                envelope(
                    "wip",
                    "wip-op",
                    "RECONCILED",
                    "DO_NOT_RETRY",
                ),
                envelope(
                    "driftguard",
                    "drift-op",
                    "POST_EFFECT_UNVERIFIED",
                    "DOMAIN_DECIDES",
                ),
            ],
            contract=self.contract(),
        )
        self.assertEqual(report["total_latest_operations"], 3)
        self.assertEqual(report["attention_required"], ["project-runner:runner-op"])
        self.assertEqual(
            report["unresolved"],
            ["driftguard:drift-op", "project-runner:runner-op"],
        )
        self.assertEqual(report["verified_or_reconciled"], ["wip:wip-op"])

    def test_unknown_future_producer_requires_no_registration(self):
        report = build_effect_attention_view(
            [
                envelope(
                    "future-producer",
                    "future-op",
                    "OUTCOME_UNKNOWN",
                    "INSPECT_BEFORE_RETRY",
                )
            ],
            contract=self.contract(),
        )
        self.assertEqual(report["attention_required"], ["future-producer:future-op"])

    def test_source_state_is_opaque(self):
        row = envelope("any-source", "op", "PRE_EFFECT", "DOMAIN_DECIDES")
        row["source_state"] = "NATIVE_STATE_UNKNOWN_TO_VERA"
        validate_effect_envelope(row, contract=self.contract())
        report = build_effect_attention_view([row], contract=self.contract())
        self.assertEqual(report["unresolved"], ["any-source:op"])

    def test_duplicate_latest_operation_fails_closed(self):
        row = envelope("source", "op", "PRE_EFFECT", "DOMAIN_DECIDES")
        with self.assertRaisesRegex(ValueError, "one producer-selected latest"):
            build_effect_attention_view([row, dict(row)], contract=self.contract())

    def test_observer_source_contains_no_current_producer_names(self):
        source = MODULE.read_text(encoding="utf-8").lower()
        self.assertNotIn("project-runner", source)
        self.assertNotIn("driftguard", source)
        self.assertNotIn('"wip"', source)
        self.assertNotIn("'wip'", source)

    def test_observer_is_not_imported_into_runtime_package_surface(self):
        init_source = INIT.read_text(encoding="utf-8")
        self.assertNotIn("effect_attention", init_source)

    def test_binding_is_observational_and_non_control(self):
        binding = json.loads(BINDING.read_text(encoding="utf-8"))
        self.assertEqual(
            binding["observer"]["operational_role"],
            "READ_ONLY_COORDINATION_ATTENTION_VIEW",
        )
        self.assertFalse(binding["observer"]["imports_into_runtime_cohesion_init"])
        self.assertIn(
            "ATTENTION_VIEW_TO_CONTROL_AUTHORITY",
            binding["forbidden_promotions"],
        )
        self.assertTrue(binding["claim_ceiling"].endswith("NOT_PROVEN_REUSABLE"))

    def test_report_contains_no_execution_directive(self):
        report = build_effect_attention_view(
            [envelope("source", "op", "OUTCOME_UNKNOWN", "INSPECT_BEFORE_RETRY")],
            contract=self.contract(),
        )
        self.assertEqual(
            report["authority_ceiling"],
            "COORDINATION_OBSERVATION_ONLY_NO_EXECUTION_RETRY_CONTROL_OR_RUNTIME_AUTHORITY",
        )
        forbidden = {"execute", "retry_now", "reconcile_now", "deploy", "merge"}
        self.assertFalse(forbidden & set(report))


if __name__ == "__main__":
    unittest.main()
