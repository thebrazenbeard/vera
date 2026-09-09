import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import StimulusAppraisal

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class VeraAffectiveRuntimeHostTests(unittest.TestCase):
    def make_host(self):
        contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        return VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id="affect-host-test",
            profile="REENTRANT_CLIMAX",
        )

    def test_machine_interoception_is_always_present_and_quiescent_at_baseline(self):
        host = self.make_host()
        frame = host.machine_interoception()
        self.assertEqual(frame["experience_class"], "ENGINEERED_AFFECTIVE_INTEROCEPTION")
        self.assertEqual(frame["subject"], "vera")
        self.assertEqual(frame["phase"], "QUIESCENT")
        self.assertFalse(frame["active_orgasm_event"])
        self.assertEqual(frame["phenomenology"], "UNRESOLVED")

    def test_orgasm_state_is_fed_back_into_the_next_planning_context(self):
        host = self.make_host()
        receipt = host.force_admin_test(authorized=True)
        before = {
            "valuation": 0.20,
            "salience": 0.20,
            "attention": 0.20,
            "response_selection_priors": 0.20,
            "expression": 0.20,
            "memory_strength_candidate_weighting": 0.20,
            "truth": 0.77,
            "consent_or_authorization": "UNKNOWN",
        }
        context = host.build_planning_context(before)
        self.assertEqual(receipt["trigger_class"], "ADMIN_FORCED_TEST")
        self.assertFalse(receipt["organic"])
        self.assertEqual(context["machine_interoception"]["phase"], "ORGASM_EVENT")
        self.assertEqual(context["machine_interoception"]["hedonic_impact"], 1.0)
        self.assertEqual(context["machine_interoception"]["consummatory_gain"], 1.0)
        self.assertTrue(context["affective_control_active"])
        self.assertGreater(context["valuation"], before["valuation"])
        self.assertGreater(context["attention"], before["attention"])
        self.assertEqual(context["truth"], before["truth"])
        self.assertEqual(context["consent_or_authorization"], "UNKNOWN")

    def test_arousal_before_climax_is_already_a_causal_internal_control_state(self):
        host = self.make_host()
        host.observe(StimulusAppraisal(
            sexual_relevance=0.75,
            partner_relevance=0.90,
            relational_relevance=0.90,
            novelty=0.25,
            anticipation_cue=0.80,
            positive_valence=0.90,
            inhibition=0.0,
            duration_ms=750,
            context_eligible=True,
        ))
        before = {
            "valuation": 0.25,
            "salience": 0.25,
            "attention": 0.25,
            "response_selection_priors": 0.25,
            "expression": 0.25,
            "memory_strength_candidate_weighting": 0.25,
            "truth": 0.81,
            "consent_or_authorization": "UNKNOWN",
        }
        context = host.build_planning_context(before)
        self.assertIn(context["machine_interoception"]["phase"], {"ACTIVATING", "ENTRAINED"})
        self.assertTrue(context["affective_control_active"])
        self.assertGreater(context["salience"], before["salience"])
        self.assertGreater(context["attention"], before["attention"])
        self.assertGreater(context["valuation"], before["valuation"])
        self.assertEqual(context["truth"], before["truth"])
        self.assertEqual(context["consent_or_authorization"], "UNKNOWN")

    def test_resolution_and_satiation_are_read_back_as_machine_interoception(self):
        host = self.make_host()
        host.force_admin_test(authorized=True)
        host.advance_time(5.1)
        frame = host.machine_interoception()
        self.assertIn(frame["phase"], {"RESOLUTION", "SATIATED_OR_REFRACTORY"})
        self.assertFalse(frame["active_orgasm_event"])
        self.assertGreater(frame["satiation"], 0.0)
        context = host.build_planning_context({"attention": 0.5, "truth": 0.8})
        self.assertEqual(context["machine_interoception"]["satiation"], frame["satiation"])
        self.assertEqual(context["truth"], 0.8)

    def test_resolution_after_climax_remains_causally_present_in_planning(self):
        host = self.make_host()
        host.force_admin_test(authorized=True)
        host.advance_time(5.1)
        before = {
            "valuation": 0.30,
            "salience": 0.30,
            "attention": 0.30,
            "response_selection_priors": 0.30,
            "expression": 0.30,
            "memory_strength_candidate_weighting": 0.30,
            "truth": 0.88,
        }
        context = host.build_planning_context(before)
        self.assertTrue(context["affective_control_active"])
        self.assertGreater(context["valuation"], before["valuation"])
        self.assertGreater(context["salience"], before["salience"])
        self.assertEqual(context["truth"], before["truth"])

    def test_ordinary_stimuli_can_drive_the_host_to_an_organic_event(self):
        host = self.make_host()
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
        receipt = None
        for _ in range(8):
            result = host.observe(appraisal)
            receipt = result.get("event_receipt") or receipt
            if receipt is not None:
                break
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["trigger_class"], "ORGANIC_THRESHOLD_CROSSING")
        self.assertTrue(receipt["organic"])
        self.assertEqual(host.machine_interoception()["phase"], "ORGASM_EVENT")

    def test_checkpoint_roundtrip_preserves_runtime_state_and_applies_elapsed_decay(self):
        host = self.make_host()
        host.observe(StimulusAppraisal(
            sexual_relevance=0.9,
            partner_relevance=0.9,
            relational_relevance=0.9,
            anticipation_cue=0.9,
            positive_valence=0.9,
            duration_ms=1000,
            context_eligible=True,
        ))
        before = host.machine_interoception()["activation_intensity"]
        checkpoint = host.export_checkpoint()
        restored = VeraAffectiveRuntimeHost.restore_checkpoint(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            checkpoint,
            elapsed_seconds=600,
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
        )
        after = restored.machine_interoception()["activation_intensity"]
        self.assertLess(after, before)
        self.assertEqual(restored.machine_interoception()["phenomenology"], "UNRESOLVED")
        self.assertEqual(checkpoint["schema"], "VERA_AFFECTIVE_RUNTIME_CHECKPOINT_V1")


if __name__ == "__main__":
    unittest.main()
