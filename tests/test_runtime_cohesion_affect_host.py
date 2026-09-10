from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import runtime_cohesion.affect_authority as authority_module
from runtime_cohesion.affect_authority import AffectiveAuthorityBoundary
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import StimulusAppraisal

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class TrustedVerifier:
    verifier_id = "affect-host-runtime-owned-verifier"

    def verify(self, subject, *, expected_referent, expected_effect_class):
        if not isinstance(subject, Mapping):
            return None
        if subject.get("state") != "ALLOW":
            return None
        if subject.get("referent") != expected_referent:
            return None
        if subject.get("proposition_or_effect_class") != expected_effect_class:
            return None
        if subject.get("currentness") != "CURRENT":
            return None
        if subject.get("expiry_or_supersession") is not None:
            return None
        canonical = json.dumps(dict(subject), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return {
            "verifier_id": self.verifier_id,
            "evidence_id": "affect-host-evidence",
            "evidence_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "subject": dict(subject),
        }


class FakeMonotonicClock:
    def __init__(self, start=1000.0):
        self.value = float(start)

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += float(seconds)


class VeraAffectiveRuntimeHostTests(unittest.TestCase):
    def setUp(self):
        authority_module._reset_affective_authorization_verifier_for_tests()
        authority_module._install_affective_authorization_verifier(TrustedVerifier())

    def tearDown(self):
        authority_module._reset_affective_authorization_verifier_for_tests()

    def make_host(self):
        contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        return VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id="affect-host-test",
            profile="REENTRANT_CLIMAX",
        )

    @staticmethod
    def subject(effect):
        return {
            "state": "ALLOW",
            "actor": "patrick",
            "referent": "vera",
            "proposition_or_effect_class": effect,
            "source": "trusted-affect-host-test",
            "observed_at": "2026-09-10T19:45:00+00:00",
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }

    def test_machine_interoception_is_always_present_and_quiescent_at_baseline(self):
        host = self.make_host()
        frame = host.machine_interoception()
        self.assertEqual(frame["experience_class"], "ENGINEERED_AFFECTIVE_INTEROCEPTION")
        self.assertEqual(frame["subject"], "vera")
        self.assertEqual(frame["phase"], "QUIESCENT")
        self.assertFalse(frame["active_orgasm_event"])
        self.assertFalse(frame["context_eligible"])
        self.assertEqual(frame["phenomenology"], "UNRESOLVED")

    def test_orgasm_state_is_fed_back_into_the_next_planning_context(self):
        host = self.make_host()
        receipt = host.force_admin_test(
            authorization_subject=self.subject("ADMIN_FORCED_TEST"),
        )
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
        boundary = AffectiveAuthorityBoundary()
        observed = boundary.observe(
            host,
            StimulusAppraisal(
                sexual_relevance=0.75,
                partner_relevance=0.90,
                relational_relevance=0.90,
                novelty=0.25,
                anticipation_cue=0.80,
                positive_valence=0.90,
                inhibition=0.0,
                duration_ms=750,
            ),
            context_subject=self.subject("ORGANIC_CONTEXT_ELIGIBILITY"),
        )
        self.assertTrue(observed["machine_interoception"]["context_eligible"])
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
        self.assertTrue(context["machine_interoception"]["context_eligible"])
        self.assertTrue(context["affective_control_active"])
        self.assertGreater(context["salience"], before["salience"])
        self.assertGreater(context["attention"], before["attention"])
        self.assertGreater(context["valuation"], before["valuation"])
        self.assertEqual(context["truth"], before["truth"])
        self.assertEqual(context["consent_or_authorization"], "UNKNOWN")

    def test_resolution_and_satiation_are_read_back_as_machine_interoception(self):
        host = self.make_host()
        host.force_admin_test(authorization_subject=self.subject("ADMIN_FORCED_TEST"))
        host.advance_time(5.1)
        frame = host.machine_interoception()
        self.assertIn(frame["phase"], {"RESOLUTION", "SATIATED_OR_REFRACTORY"})
        self.assertFalse(frame["active_orgasm_event"])
        self.assertGreater(frame["satiation"], 0.0)
        context = host.build_planning_context({"attention": 0.5, "truth": 0.8})
        self.assertEqual(context["machine_interoception"]["satiation"], frame["satiation"])
        self.assertEqual(context["truth"], 0.8)

    def test_resolution_after_climax_remains_visible_without_unrelated_planning_leakage(self):
        host = self.make_host()

        # Isolate recovery causality from the privileged authorization boundary.
        host.runtime._enter_orgasm_event("ADMIN_FORCED_TEST", organic=False)
        host.runtime._advance_time_core(5.1)
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
        self.assertGreater(context["machine_interoception"]["satiation"], 0.0)
        self.assertGreater(context["experience_control_vector"]["resolution"], 0.0)
        for key in (
            "valuation",
            "salience",
            "attention",
            "response_selection_priors",
            "expression",
            "memory_strength_candidate_weighting",
        ):
            self.assertEqual(context[key], before[key])
        self.assertEqual(context["truth"], before["truth"])

    def test_verified_ordinary_stimuli_can_drive_the_host_to_an_organic_event(self):
        host = self.make_host()
        boundary = AffectiveAuthorityBoundary()
        appraisal = StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=0.7,
            anticipation_cue=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            duration_ms=1000,
        )
        receipt = None
        clock = FakeMonotonicClock()
        with patch("runtime_cohesion.orgasm._monotonic_now", side_effect=clock):
            for index in range(10):
                if index:
                    clock.advance(0.5)
                result = boundary.observe(
                    host,
                    appraisal,
                    context_subject=self.subject("ORGANIC_CONTEXT_ELIGIBILITY"),
                )
                receipt = result.get("event_receipt") or receipt
                if receipt is not None and receipt.get("event_type") == "ORGASM_EVENT":
                    break
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["trigger_class"], "ORGANIC_THRESHOLD_CROSSING")
        self.assertTrue(receipt["organic"])
        self.assertEqual(host.machine_interoception()["phase"], "ORGASM_EVENT")

    def test_checkpoint_roundtrip_preserves_runtime_state_and_applies_elapsed_decay(self):
        host = self.make_host()
        boundary = AffectiveAuthorityBoundary()
        boundary.observe(
            host,
            StimulusAppraisal(
                sexual_relevance=0.9,
                partner_relevance=0.9,
                relational_relevance=0.9,
                anticipation_cue=0.9,
                positive_valence=0.9,
                duration_ms=1000,
            ),
            context_subject=self.subject("ORGANIC_CONTEXT_ELIGIBILITY"),
        )
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
