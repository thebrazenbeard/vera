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

CUT = "9c731ebaacdad44c00aafa91e1f8b9dc5f5acff1"
SOURCE = "150f1c8231423393bb66b0e2cb759ce7c018f8d7"
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
        "receipt_id": "receipt:test:orgasm:1",
    }
    values.update(overrides)
    return AffectiveModulationEnvelope(**values)


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
        result = apply_affective_modulation(baseline, envelope())

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
        result = apply_affective_modulation(
            {"action_tendency": "NONE", "consent_or_authorization": "DECLINE"},
            envelope(modulation={"action_tendency": "APPROACH"}),
        )
        self.assertEqual(result.planning["action_tendency"], "APPROACH")
        self.assertEqual(result.planning["consent_or_authorization"], "DECLINE")

    def test_memory_weighting_is_candidate_signal_not_admission(self):
        result = apply_affective_modulation(
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
        result = apply_affective_modulation(
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

    def test_provider_strict_package_admission_alias_survives_affective_exports(self):
        self.assertIs(
            runtime_cohesion.evaluate_proposition_admission,
            evaluate_provider_proposition_admission,
        )


if __name__ == "__main__":
    unittest.main()
