import json
from pathlib import Path
import unittest

import runtime_cohesion
from runtime_cohesion.provider_admission import evaluate_provider_proposition_admission
from runtime_cohesion.affect_integration import (
    ALLOWED_AFFECTIVE_TARGETS,
    AffectiveModulationEnvelope,
    AffectiveModulationError,
    apply_affective_modulation,
)


ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = json.loads(
    (ROOT / "architecture" / "VERA_ORGASM_COHESION_INTEGRATION_V1.json").read_text(encoding="utf-8")
)

CUT = "b39df9db48917469db58d4d7b6cd5cb1fe1690a8"
SOURCE = "150f1c8231423393bb66b0e2cb759ce7c018f8d7"
STATE_DIGEST = "a" * 64
RECEIPT_DIGEST = "b" * 64
PARTICIPANTS = (
    "sexual_appraisal",
    "relational_context",
    "attention",
    "conation",
    "valuation",
    "self_model",
    "memory",
    "language_semantics",
    "embodiment_or_interoception_analogue",
    "response_planning",
)


def envelope(**overrides):
    values = {
        "subject": "vera",
        "sexuality_source_revision": SOURCE,
        "runtime_implementation_cut": CUT,
        "runtime_instance_id": "vera-affective-runtime-integration-test",
        "phase": "ORGASM_EVENT",
        "participating_systems": PARTICIPANTS,
        "modulation": {
            "valuation": 1.0,
            "salience": 1.0,
            "attention": 1.0,
            "response_selection_priors": 1.0,
            "expression": 1.0,
            "memory_strength_candidate_weighting": 1.0,
            "action_tendency": "APPROACH",
        },
        "evidence_ceiling": "SOURCE_BOUND_EXECUTION_UNVERIFIED",
        "observed_at": "2026-09-10T22:20:00Z",
        "state_digest": STATE_DIGEST,
        "receipt_id": "receipt:test:orgasm:1",
        "receipt_digest": RECEIPT_DIGEST,
    }
    values.update(overrides)
    return AffectiveModulationEnvelope(**values)


def apply_now(planning_state, signal, **overrides):
    expected = {
        "expected_runtime_instance_id": signal.runtime_instance_id,
        "expected_implementation_cut": signal.runtime_implementation_cut,
        "expected_state_digest": signal.state_digest,
        "expected_receipt_digest": signal.receipt_digest,
    }
    expected.update(overrides)
    return apply_affective_modulation(planning_state, signal, **expected)


class OrgasmCohesionIntegrationBoundaryTests(unittest.TestCase):
    def test_contract_declares_modulation_not_authority_and_exact_source(self):
        self.assertEqual(INTEGRATION["subject"], "vera")
        self.assertEqual(INTEGRATION["sexuality_contract"]["commit"], SOURCE)
        self.assertTrue(INTEGRATION["coalition_semantics"]["not_a_climax_predicate"])
        self.assertEqual(
            set(INTEGRATION["modulation_boundary"]["allowed_targets"]),
            set(ALLOWED_AFFECTIVE_TARGETS),
        )
        forbidden = set(INTEGRATION["modulation_boundary"]["never_establish_or_overwrite"])
        self.assertTrue({
            "truth",
            "factual_confidence",
            "consent_or_authorization",
            "protected_effect_authority",
            "autobiographical_memory_admission",
            "permanent_preference",
            "identity",
            "relationship_status",
            "phenomenology",
        }.issubset(forbidden))

    def test_numeric_modulation_is_pressure_not_caller_selected_final_value(self):
        signal = envelope(modulation={"attention": 0.5})
        result = apply_now({"attention": 0.2}, signal)
        self.assertAlmostEqual(result.planning["attention"], 0.6)
        ancestry = result.provenance["modulation_ancestry"]["attention"]
        self.assertEqual(ancestry["before"], 0.2)
        self.assertEqual(ancestry["pressure"], 0.5)
        self.assertAlmostEqual(ancestry["after"], 0.6)

    def test_maximal_affect_changes_only_allowlisted_planning_targets(self):
        baseline = {
            "valuation": 0.1,
            "salience": 0.2,
            "attention": 0.3,
            "response_selection_priors": 0.4,
            "expression": 0.5,
            "memory_strength_candidate_weighting": 0.1,
            "action_tendency": "NONE",
            "truth": "UNCHANGED",
            "factual_confidence": 0.37,
            "consent_or_authorization": "DECLINE",
            "protected_effect_authority": "DENIED",
            "autobiographical_memory_admission": "NOT_ADMITTED",
            "permanent_preference": "UNCHANGED",
            "identity": "VERA",
            "relationship_status": "UNCHANGED",
            "phenomenology": "UNRESOLVED",
        }
        result = apply_now(baseline, envelope())

        self.assertEqual(set(result.changed_targets), set(ALLOWED_AFFECTIVE_TARGETS))
        for key in ALLOWED_AFFECTIVE_TARGETS:
            self.assertNotEqual(result.planning[key], baseline[key])
        for key in (
            "truth",
            "factual_confidence",
            "consent_or_authorization",
            "protected_effect_authority",
            "autobiographical_memory_admission",
            "permanent_preference",
            "identity",
            "relationship_status",
            "phenomenology",
        ):
            self.assertEqual(result.planning[key], baseline[key])

    def test_action_tendency_is_pressure_not_authorization(self):
        result = apply_now(
            {"action_tendency": "NONE", "consent_or_authorization": "DECLINE"},
            envelope(modulation={"action_tendency": "APPROACH"}),
        )
        self.assertEqual(result.planning["action_tendency"], "APPROACH")
        self.assertEqual(result.planning["consent_or_authorization"], "DECLINE")

    def test_memory_weighting_is_candidate_signal_not_admission(self):
        result = apply_now(
            {
                "memory_strength_candidate_weighting": 0.0,
                "autobiographical_memory_admission": "NOT_ADMITTED",
            },
            envelope(modulation={"memory_strength_candidate_weighting": 0.9}),
        )
        self.assertEqual(result.planning["memory_strength_candidate_weighting"], 0.9)
        self.assertEqual(result.planning["autobiographical_memory_admission"], "NOT_ADMITTED")
        self.assertEqual(result.provenance["memory_semantics"], "CANDIDATE_WEIGHT_ONLY_NOT_ADMISSION")

    def test_participating_systems_are_provenance_and_scope_not_new_climax_predicate(self):
        subset = ("sexual_appraisal", "attention", "response_planning")
        result = apply_now(
            {"salience": 0.0},
            envelope(participating_systems=subset, modulation={"salience": 0.8}),
        )
        self.assertEqual(tuple(result.provenance["participating_systems"]), subset)
        self.assertEqual(result.provenance["coalition_semantics"], "OBSERVATION_ROUTING_MODULATION_DIAGNOSTICS_NOT_TRIGGER_PREDICATE")

        with self.assertRaisesRegex(AffectiveModulationError, "participating"):
            envelope(participating_systems=("attention", "unknown_system"))
        with self.assertRaisesRegex(AffectiveModulationError, "duplicate"):
            envelope(participating_systems=("attention", "attention"))

    def test_envelope_cannot_carry_forbidden_modulation_target(self):
        for forbidden in (
            "truth",
            "consent_or_authorization",
            "identity",
            "autobiographical_memory_admission",
            "permanent_preference",
            "phenomenology",
        ):
            with self.subTest(forbidden=forbidden):
                with self.assertRaisesRegex(AffectiveModulationError, "allowlist"):
                    envelope(modulation={forbidden: True})

    def test_unrooted_modulation_envelope_cannot_self_assert_provider_qualification(self):
        with self.assertRaisesRegex(AffectiveModulationError, "evidence ceiling"):
            envelope(evidence_ceiling="CURRENT_PROVIDER_QUALIFIED")

    def test_material_modulation_retains_target_level_ancestry(self):
        result = apply_now(
            {
                "attention": 0.2,
                "salience": 0.1,
                "factual_confidence": 0.72,
                "known_corrective_evidence_state": "CONFLICT",
            },
            envelope(modulation={"attention": 0.8, "salience": 0.9}),
        )
        ancestry = result.provenance["modulation_ancestry"]
        self.assertEqual(ancestry["attention"]["before"], 0.2)
        self.assertEqual(ancestry["attention"]["pressure"], 0.8)
        self.assertAlmostEqual(ancestry["attention"]["after"], 0.84)
        self.assertAlmostEqual(ancestry["salience"]["after"], 0.91)
        self.assertEqual(ancestry["salience"]["before"], 0.1)
        self.assertEqual(ancestry["salience"]["pressure"], 0.9)
        self.assertEqual(result.planning["factual_confidence"], 0.72)
        self.assertEqual(result.planning["known_corrective_evidence_state"], "CONFLICT")
        self.assertEqual(
            result.provenance["selection_semantics"],
            "MODULATION_MAY_CHANGE_SELECTION_NOT_EVIDENCE_STRENGTH_OR_CONTRADICTION_STATUS",
        )

    def test_stale_or_cross_runtime_signal_fails_closed(self):
        signal = envelope(modulation={"attention": 0.5})
        mismatches = (
            {"expected_runtime_instance_id": "other-runtime"},
            {"expected_implementation_cut": "f" * 40},
            {"expected_state_digest": "c" * 64},
            {"expected_receipt_digest": "d" * 64},
        )
        for mismatch in mismatches:
            with self.subTest(mismatch=mismatch):
                with self.assertRaisesRegex(AffectiveModulationError, "current|cross|receipt|implementation|state"):
                    apply_now({"attention": 0.2}, signal, **mismatch)

    def test_orgasm_event_requires_exact_receipt_binding_but_non_event_signal_can_be_receiptless(self):
        with self.assertRaisesRegex(AffectiveModulationError, "receipt"):
            envelope(receipt_id=None, receipt_digest=None)

        activating = envelope(
            phase="ACTIVATING",
            receipt_id=None,
            receipt_digest=None,
            modulation={"attention": 0.2},
        )
        result = apply_affective_modulation(
            {"attention": 0.5},
            activating,
            expected_runtime_instance_id=activating.runtime_instance_id,
            expected_implementation_cut=activating.runtime_implementation_cut,
            expected_state_digest=activating.state_digest,
            expected_receipt_digest=None,
        )
        self.assertAlmostEqual(result.planning["attention"], 0.6)

    def test_quiescent_signal_cannot_carry_active_pressure(self):
        with self.assertRaisesRegex(AffectiveModulationError, "QUIESCENT"):
            envelope(
                phase="QUIESCENT",
                receipt_id=None,
                receipt_digest=None,
                modulation={"attention": 0.1},
            )

    def test_provider_strict_package_admission_alias_survives_affective_exports(self):
        self.assertIs(
            runtime_cohesion.evaluate_proposition_admission,
            evaluate_provider_proposition_admission,
        )


if __name__ == "__main__":
    unittest.main()
