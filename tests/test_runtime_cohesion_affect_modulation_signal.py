from collections.abc import Mapping
import hashlib
import inspect
import json
from pathlib import Path
import unittest

import runtime_cohesion.affect_authority as authority_module
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"
UNROOTED = "IN_PROCESS_UNROOTED_NON_QUALIFYING"
NUMERIC_TARGETS = {
    "valuation",
    "salience",
    "attention",
    "response_selection_priors",
    "expression",
    "memory_strength_candidate_weighting",
}


class TrustedVerifier:
    verifier_id = "affect-modulation-signal-verifier"

    def verify(self, subject, *, expected_referent, expected_effect_class):
        if not isinstance(subject, Mapping):
            return None
        if subject.get("state") != "ALLOW":
            return None
        if subject.get("referent") != expected_referent:
            return None
        if subject.get("proposition_or_effect_class") != expected_effect_class:
            return None
        if subject.get("currentness") != "CURRENT" or subject.get("expiry_or_supersession") is not None:
            return None
        canonical = json.dumps(dict(subject), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return {
            "verifier_id": self.verifier_id,
            "evidence_id": "affect-modulation-signal-evidence",
            "evidence_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "subject": dict(subject),
        }


class AffectiveModulationSignalTests(unittest.TestCase):
    def setUp(self):
        authority_module._reset_affective_authorization_verifier_for_tests()
        authority_module._install_affective_authorization_verifier(TrustedVerifier())

    def tearDown(self):
        authority_module._reset_affective_authorization_verifier_for_tests()

    @staticmethod
    def subject():
        return {
            "state": "ALLOW",
            "actor": "patrick",
            "referent": "vera",
            "proposition_or_effect_class": "ADMIN_FORCED_TEST",
            "source": "trusted-affect-modulation-signal-test",
            "observed_at": "2026-09-10T22:55:00+00:00",
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }

    def host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="affect-modulation-signal-test",
            profile="REENTRANT_CLIMAX",
        )

    def build_signal(self, host):
        from runtime_cohesion.affect_signal import build_affective_modulation_signal
        return build_affective_modulation_signal(host)

    def test_signal_builder_has_no_generic_planning_mutation_input(self):
        from runtime_cohesion.affect_signal import build_affective_modulation_signal
        params = inspect.signature(build_affective_modulation_signal).parameters
        self.assertEqual(set(params), {"host"})

    def test_quiescent_signal_is_typed_source_bound_and_non_authoritative(self):
        host = self.host()
        signal = self.build_signal(host)
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))

        self.assertEqual(signal["schema"], "VERA_AFFECTIVE_MODULATION_SIGNAL_V1")
        self.assertEqual(signal["subject"], "vera")
        self.assertEqual(signal["runtime_instance_id"], "affect-modulation-signal-test")
        self.assertEqual(signal["source_binding"]["source_commit"], binding["source_commit"])
        self.assertEqual(signal["runtime_implementation_cut"], binding["runtime_implementation_cut"])
        self.assertEqual(signal["phase"], "QUIESCENT")
        self.assertEqual(set(signal["target_modulation_strength"]), NUMERIC_TARGETS)
        self.assertTrue(all(value == 0.0 for value in signal["target_modulation_strength"].values()))
        self.assertEqual(signal["evidence_effect"], "NONE")
        self.assertEqual(signal["authorization_effect"], "NONE")
        self.assertEqual(signal["memory_admission_effect"], "NONE")
        self.assertEqual(signal["identity_effect"], "NONE")
        self.assertEqual(signal["relationship_state_effect"], "NONE")
        self.assertEqual(signal["phenomenology"], "UNRESOLVED")
        self.assertFalse(signal["usable_as_currentness_evidence"])
        self.assertRegex(signal["signal_digest"], r"^[0-9a-f]{64}$")

    def test_active_forced_event_emits_nonzero_numeric_signal_and_separate_action_tendency(self):
        host = self.host()
        receipt = host.force_admin_test(authorization_subject=self.subject())
        self.assertEqual(receipt["authority_composition_trust"], UNROOTED)
        signal = self.build_signal(host)

        self.assertEqual(set(signal["target_modulation_strength"]), NUMERIC_TARGETS)
        self.assertNotIn("action_tendency", signal["target_modulation_strength"])
        self.assertEqual(signal["action_tendency"], "HOLD")
        self.assertGreater(signal["target_modulation_strength"]["salience"], 0.0)
        self.assertGreater(signal["target_modulation_strength"]["attention"], 0.0)
        self.assertEqual(signal["authority_context_trust"], UNROOTED)
        self.assertEqual(signal["event_lineage"]["receipt_id"], receipt["receipt_id"])
        self.assertEqual(signal["event_lineage"]["event_digest"], receipt["event_digest"])
        self.assertNotIn("claim", signal)
        self.assertEqual(signal["provider_currentness"], "UNRESOLVED")
        self.assertEqual(signal["durability"], "NOT_QUALIFIED")

    def test_signal_contains_bounded_participating_systems_and_control_vector(self):
        host = self.host()
        signal = self.build_signal(host)
        declared = set(host.runtime.contract["participating_systems"])
        self.assertTrue(set(signal["participating_systems"]).issubset(declared))
        self.assertEqual(len(signal["participating_systems"]), len(set(signal["participating_systems"])))
        for value in signal["control_vector"].values():
            self.assertIsInstance(value, float)
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)

    def test_signal_does_not_accept_or_return_arbitrary_planning_fields(self):
        host = self.host()
        signal = self.build_signal(host)
        protected = {
            "truth",
            "factual_confidence",
            "consent_or_authorization",
            "autobiographical_memory_admission",
            "permanent_preference",
            "identity",
            "relationship_status",
            "phenomenology_claim",
        }
        self.assertTrue(protected.isdisjoint(signal["target_modulation_strength"]))


if __name__ == "__main__":
    unittest.main()
