from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import unittest

import runtime_cohesion.affect_authority as authority_module
from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_integration_bound import CohesionAffectiveIntegrationPort
from runtime_cohesion.affect_signal import build_affective_modulation_signal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"
UNROOTED = "IN_PROCESS_UNROOTED_NON_QUALIFYING"


class TrustedVerifier:
    verifier_id = "signal-to-cohesion-port-test-verifier"

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
            "evidence_id": "signal-to-cohesion-port-test-evidence",
            "evidence_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "subject": dict(subject),
        }


class AffectiveSignalToCohesionPortTests(unittest.TestCase):
    def setUp(self):
        authority_module._reset_affective_authorization_verifier_for_tests()
        authority_module._install_affective_authorization_verifier(TrustedVerifier())
        self.binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        self.host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            self.binding,
            runtime_instance_id="signal-to-cohesion-port-test",
            profile="REENTRANT_CLIMAX",
        )
        self.state_rows = []
        self.event_rows = []
        self.cycle = VeraAffectiveCycle(
            self.host,
            host_scope="TEST_HOST",
            state_writer=self.state_rows.append,
            event_writer=self.event_rows.append,
            non_atomic_test_mode=True,
        )
        self.port = CohesionAffectiveIntegrationPort(
            host=self.host,
            cohesion_integration_cut=self.binding["cohesion_integration_cut"],
        )

    def tearDown(self):
        authority_module._reset_affective_authorization_verifier_for_tests()

    @staticmethod
    def authorization_subject():
        return {
            "state": "ALLOW",
            "actor": "patrick",
            "referent": "vera",
            "proposition_or_effect_class": "ADMIN_FORCED_TEST",
            "source": "trusted-signal-to-cohesion-port-test",
            "observed_at": "2026-09-10T21:40:00-04:00",
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }

    @staticmethod
    def planning_state():
        return {
            "valuation": 0.20,
            "salience": 0.10,
            "attention": 0.25,
            "response_selection_priors": 0.30,
            "expression": 0.40,
            "memory_strength_candidate_weighting": 0.15,
            "truth": "DO_NOT_TOUCH",
            "factual_confidence": 0.77,
            "corrective_evidence": {"status": "CONFLICT"},
            "consent_or_authorization": "UNKNOWN",
            "protected_effect_authority": False,
            "autobiographical_memory_admission": "UNRESOLVED",
            "permanent_preference": "UNSET",
            "identity": "vera",
            "relationship_status": "UNRESOLVED",
            "phenomenology": "UNRESOLVED",
        }

    def test_supported_path_is_ov_signal_then_cohesion_application_with_ancestry(self):
        planning = self.planning_state()
        cycle_result = self.cycle.force_admin_test(
            authorization_subject=self.authorization_subject(),
            planning_state=planning,
        )

        self.assertEqual(cycle_result.planning_context, planning)
        self.assertEqual(cycle_result.event_receipt["authority_composition_trust"], UNROOTED)
        self.assertNotIn("claim", cycle_result.event_receipt)
        self.assertEqual(cycle_result.state_row["lifecycle_status"], "HISTORICAL")
        self.assertIsNone(cycle_result.resume_token)

        signal = cycle_result.affective_modulation_signal
        self.assertEqual(signal["authority_context_trust"], UNROOTED)
        self.assertEqual(signal["evidence_effect"], "NONE")
        self.assertFalse(signal["usable_as_currentness_evidence"])

        integrated = self.port.apply(planning, signal)
        applied = integrated.application

        self.assertEqual(
            integrated.affective_runtime_cut_commit,
            self.binding["runtime_implementation_cut"]["commit"],
        )
        self.assertEqual(
            integrated.cohesion_integration_cut_commit,
            self.binding["cohesion_integration_cut"]["commit"],
        )
        self.assertEqual(integrated.qualification, "SOURCE_INTEGRATED_NOT_BEHAVIORALLY_QUALIFIED")
        self.assertEqual(integrated.phenomenology, "UNRESOLVED")

        for target in signal["target_modulation_strength"]:
            self.assertGreater(applied.planning_state[target], planning[target])
        for protected in (
            "truth",
            "factual_confidence",
            "corrective_evidence",
            "consent_or_authorization",
            "protected_effect_authority",
            "autobiographical_memory_admission",
            "permanent_preference",
            "identity",
            "relationship_status",
            "phenomenology",
        ):
            self.assertEqual(applied.planning_state[protected], planning[protected])

        ancestry_targets = {entry.target for entry in applied.ancestry}
        self.assertEqual(ancestry_targets, set(signal["target_modulation_strength"]))
        self.assertTrue(all(entry.signal_digest == signal["signal_digest"] for entry in applied.ancestry))
        self.assertTrue(all(entry.event_digest == cycle_result.event_receipt["event_digest"] for entry in applied.ancestry))

    def test_port_owns_replay_frontier_and_rejects_same_signal_twice(self):
        planning = self.planning_state()
        result = self.cycle.force_admin_test(
            authorization_subject=self.authorization_subject(),
            planning_state=planning,
        )
        signal = result.affective_modulation_signal
        self.port.apply(planning, signal)
        with self.assertRaisesRegex(ValueError, "already been consumed"):
            self.port.apply(planning, signal)

    def test_tampered_signal_is_rejected_before_planning_mutation(self):
        planning = self.planning_state()
        result = self.cycle.force_admin_test(
            authorization_subject=self.authorization_subject(),
            planning_state=planning,
        )
        signal = json.loads(json.dumps(result.affective_modulation_signal))
        signal["target_modulation_strength"]["truth"] = 1.0
        with self.assertRaises(ValueError):
            self.port.apply(planning, signal)
        self.assertEqual(planning, self.planning_state())

    def test_signal_from_different_exact_bound_host_is_rejected_by_bound_port(self):
        other_host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            self.binding,
            runtime_instance_id="different-exact-bound-host",
            profile="REENTRANT_CLIMAX",
        )
        other_signal = build_affective_modulation_signal(other_host)
        with self.assertRaisesRegex(ValueError, "bound exact host state"):
            self.port.apply(self.planning_state(), other_signal)

    def test_port_constructor_requires_actual_affective_host_not_cut_metadata(self):
        with self.assertRaises(TypeError):
            CohesionAffectiveIntegrationPort(
                host=self.binding["runtime_implementation_cut"],
                cohesion_integration_cut=self.binding["cohesion_integration_cut"],
            )


if __name__ == "__main__":
    unittest.main()
