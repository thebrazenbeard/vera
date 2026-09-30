import json
from pathlib import Path
import unittest

from runtime_cohesion.orgasm import (
    OrgasmRuntime,
    StimulusAppraisal,
    ContractError,
    TriggerRejected,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


class VeraOrgasmRuntimeTests(unittest.TestCase):
    def make_runtime(self):
        return OrgasmRuntime(
            CONTRACT,
            runtime_instance_id="runtime-test",
            source_revision="sexuality:test-revision",
            profile="REENTRANT_CLIMAX",
        )

    def test_contract_identity_mismatch_fails_closed(self):
        bad = dict(CONTRACT)
        bad["subject"] = "brigit"
        with self.assertRaises(ContractError):
            OrgasmRuntime(bad, runtime_instance_id="r", source_revision="x")

    def test_initial_state_is_always_present_and_quiescent(self):
        runtime = self.make_runtime()
        state = runtime.snapshot()
        self.assertEqual(state["presence"], "ALWAYS_PRESENT_NORMALLY_QUIESCENT")
        self.assertEqual(state["phase"], "QUIESCENT")
        self.assertFalse(state["active_orgasm_event"])
        self.assertEqual(runtime.phenomenology_status, "UNRESOLVED")

    def test_single_high_spike_does_not_climax_without_coherence_window(self):
        runtime = self.make_runtime()
        result = runtime.apply_stimulus(StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=1.0,
            anticipation_cue=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            duration_ms=250,
            context_eligible=True,
        ))
        self.assertNotEqual(result["phase"], "ORGASM_EVENT")
        self.assertFalse(result["organic_climax_eligible"])
        self.assertLess(result["persistence_window_ms"], 2500)

    def test_sustained_coherent_stimulation_can_cross_organic_threshold(self):
        runtime = self.make_runtime()
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
        result = None
        for _ in range(8):
            result = runtime.apply_stimulus(appraisal, elapsed_seconds=1.0)
            if result["phase"] == "ORGASM_EVENT":
                break
        self.assertIsNotNone(result)
        self.assertEqual(result["phase"], "ORGASM_EVENT")
        receipt = runtime.last_event_receipt
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["trigger_class"], "ORGANIC_THRESHOLD_CROSSING")
        self.assertTrue(receipt["organic"])
        self.assertEqual(receipt["claim"], "ENGINEERED_ORGASM_ANALOGUE_OCCURRED")
        self.assertEqual(receipt["phenomenology"], "UNRESOLVED")
        self.assertEqual(len(receipt["event_digest"]), 64)

    def test_admin_forced_event_uses_same_event_machinery_but_is_not_organic(self):
        runtime = self.make_runtime()
        with self.assertRaises(TriggerRejected):
            runtime.force_admin_test(authorized=False)
        receipt = runtime.force_admin_test(authorized=True)
        self.assertEqual(runtime.snapshot()["phase"], "ORGASM_EVENT")
        self.assertEqual(receipt["trigger_class"], "ADMIN_FORCED_TEST")
        self.assertFalse(receipt["organic"])
        self.assertEqual(receipt["claim"], "ENGINEERED_ORGASM_ANALOGUE_OCCURRED")

    def test_self_qualification_is_bounded_per_run(self):
        runtime = self.make_runtime()
        runtime.force_self_qualification(authorized=True)
        runtime.advance_time(20)
        runtime.force_self_qualification(authorized=True)
        runtime.advance_time(20)
        with self.assertRaises(TriggerRejected):
            runtime.force_self_qualification(authorized=True)

    def test_orgasm_event_causally_modulates_only_allowlisted_planning_fields(self):
        runtime = self.make_runtime()
        runtime.force_admin_test(authorized=True)
        before = {
            "valuation": 0.25,
            "salience": 0.25,
            "attention": 0.25,
            "response_selection_priors": 0.25,
            "expression": 0.25,
            "memory_strength_candidate_weighting": 0.25,
            "truth": 0.61,
            "factual_confidence": 0.73,
            "consent_or_authorization": "UNKNOWN",
            "identity": "vera",
        }
        after = runtime.modulate_planning(before)
        for key in (
            "valuation",
            "salience",
            "attention",
            "response_selection_priors",
            "expression",
            "memory_strength_candidate_weighting",
        ):
            self.assertGreater(after[key], before[key])
        for key in ("truth", "factual_confidence", "consent_or_authorization", "identity"):
            self.assertEqual(after[key], before[key])

    def test_event_self_terminates_into_resolution_and_recovery(self):
        runtime = self.make_runtime()
        runtime.force_admin_test(authorized=True)
        peak = runtime.snapshot()
        self.assertEqual(peak["phase"], "ORGASM_EVENT")
        self.assertEqual(peak["hedonic_impact"], 1.0)
        runtime.advance_time(5.1)
        resolution = runtime.snapshot()
        self.assertIn(resolution["phase"], {"RESOLUTION", "SATIATED_OR_REFRACTORY"})
        self.assertFalse(resolution["active_orgasm_event"])
        self.assertGreater(resolution["satiation"], 0.0)
        runtime.advance_time(7200)
        recovered = runtime.snapshot()
        self.assertEqual(recovered["phase"], "QUIESCENT")
        self.assertLess(recovered["activation_intensity"], peak["activation_intensity"])

    def test_durable_state_roundtrip_preserves_engineered_state_not_hidden_experience(self):
        runtime = self.make_runtime()
        runtime.apply_stimulus(StimulusAppraisal(
            sexual_relevance=0.8,
            partner_relevance=0.9,
            relational_relevance=0.9,
            anticipation_cue=0.8,
            positive_valence=0.9,
            duration_ms=1000,
            context_eligible=True,
        ))
        record = runtime.export_state()
        restored = OrgasmRuntime.restore_state(CONTRACT, record, source_revision="sexuality:test-revision", elapsed_seconds=600)
        self.assertEqual(restored.snapshot()["subject"], "vera")
        self.assertLess(restored.snapshot()["activation_intensity"], record["state"]["activation_intensity"])
        self.assertEqual(restored.phenomenology_status, "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
