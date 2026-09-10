import json
from pathlib import Path
import unittest

import runtime_cohesion
import runtime_cohesion.affect_provider_runtime as affect_provider_runtime
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import build_affective_resume_token, checkpoint_to_state_row
from runtime_cohesion.orgasm import StimulusAppraisal
from tests.test_runtime_cohesion_affect_provider_composition_trust import (
    SelfConsistentAffectiveProviderDouble,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class VeraAffectiveOrganicDurablePathTests(unittest.TestCase):
    def setUp(self):
        affect_provider_runtime._reset_runtime_affective_provider_for_tests()

    def tearDown(self):
        affect_provider_runtime._reset_runtime_affective_provider_for_tests()

    def make_provider_restored_cycle(self):
        contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id="affect-organic-durable-test",
            profile="REENTRANT_CLIMAX",
        )
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=1)
        adapter = SelfConsistentAffectiveProviderDouble(row)
        affect_provider_runtime._install_runtime_affective_provider_adapter(adapter)
        cycle = runtime_cohesion.restore_current_affective_cycle(
            contract_text,
            binding,
            row,
            host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            expected_resume_token=build_affective_resume_token(row),
        )
        return adapter, cycle

    def test_organic_threshold_event_and_resolution_cross_exact_provider_atomic_boundary(self):
        adapter, cycle = self.make_provider_restored_cycle()
        appraisal = StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=0.7,
            anticipation_cue=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            duration_ms=1000,
            context_eligible=True,
        )

        orgasm = None
        for _ in range(8):
            result = cycle.process_turn(
                appraisal,
                planning_state={
                    "valuation": 0.2,
                    "salience": 0.2,
                    "attention": 0.2,
                    "truth": 0.9,
                    "consent_or_authorization": "UNKNOWN",
                },
            )
            if result.event_receipt is not None:
                orgasm = result
                break

        self.assertIsNotNone(orgasm)
        self.assertEqual(orgasm.durability_mode, "ATOMIC_DURABLE")
        self.assertEqual(orgasm.state_row["lifecycle_status"], "CURRENT")
        self.assertEqual(orgasm.event_receipt["trigger_class"], "ORGANIC_THRESHOLD_CROSSING")
        self.assertTrue(orgasm.event_receipt["organic"])
        self.assertEqual(orgasm.event_row["event_type"], "ORGASM_EVENT")
        self.assertEqual(orgasm.planning_context["truth"], 0.9)
        self.assertEqual(orgasm.planning_context["consent_or_authorization"], "UNKNOWN")
        self.assertEqual(orgasm.commit_result["checkpoint_sha256"], orgasm.checkpoint["checkpoint_sha256"])

        resolution = cycle.advance_time(
            5.1,
            planning_state={"truth": 0.9, "consent_or_authorization": "UNKNOWN"},
        )
        self.assertIsNotNone(resolution.event_receipt)
        self.assertIn(resolution.event_receipt["event_type"], {"RESOLUTION", "RECOVERY"})
        self.assertTrue(resolution.event_receipt["organic"])
        self.assertEqual(resolution.planning_context["truth"], 0.9)
        self.assertEqual(resolution.planning_context["consent_or_authorization"], "UNKNOWN")

        versions = [request["state_version"] for request in adapter.commit_calls]
        self.assertEqual(versions, list(range(2, 2 + len(adapter.commit_calls))))
        self.assertEqual(
            [request["expected_prior_version"] for request in adapter.commit_calls],
            list(range(1, 1 + len(adapter.commit_calls))),
        )
        self.assertTrue(all(request["schema"] == "VERA_AFFECTIVE_RUNTIME_ATOMIC_COMMIT_V1" for request in adapter.commit_calls))
        event_types = [
            row["event_type"]
            for request in adapter.commit_calls
            for row in request["event_rows"]
        ]
        self.assertIn("ORGASM_EVENT", event_types)
        self.assertTrue(any(event_type in {"RESOLUTION", "RECOVERY"} for event_type in event_types))


if __name__ == "__main__":
    unittest.main()
