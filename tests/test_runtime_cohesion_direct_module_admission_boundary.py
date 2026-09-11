from types import SimpleNamespace
import unittest

from runtime_cohesion import ProviderEvidenceEnvelope
import runtime_cohesion.runtime as runtime


CONTRACT = {
    "authority_resolvers": {
        "self_report_and_inference": {
            "accepted_evidence_classes": ["vera_current_self_report"],
        },
    },
    "resolver_dispatch": [
        {
            "id": "dispatch:vera-current-stance",
            "domain_scope": "*",
            "proposition_or_effect_class": "VERA_CURRENT_STANCE_SELF_REPORT",
            "referent_scope": "VERA",
            "resolver_ref": "self_report_and_inference",
            "precedence": 95,
            "conflict_disposition": "FAIL_CLOSED",
        },
    ],
    "resolver_dispatch_decisive_evidence": {
        "dispatch:vera-current-stance": {
            "all_of": ["vera_current_self_report"],
            "any_of": [],
        },
    },
}


def envelope():
    return ProviderEvidenceEnvelope(
        provider="TEST_PROVIDER",
        locator="test://vera/current-stance",
        revision="fixture-v1",
        observed_at="2026-09-09T22:15:00Z",
        evidence_class="vera_current_self_report",
        referent="SELF_APPRAISAL_AND_EMPATHY",
        scope="VERA",
        privacy_class="PRIVATE",
        currentness_basis="SYNTHETIC_TEST_FIXTURE",
        supersession_state="CURRENT_OBSERVATION",
        conflict_state="NONE",
        metadata={
            "proposition_or_effect_class": "VERA_CURRENT_STANCE_SELF_REPORT",
            "referent_scope": "VERA",
        },
    )


class DirectModuleAdmissionBoundaryTests(unittest.TestCase):
    def test_direct_runtime_public_admission_rejects_lightweight_evidence(self):
        with self.assertRaises(TypeError):
            runtime.evaluate_proposition_admission(
                "SELF_APPRAISAL_AND_EMPATHY",
                "VERA_CURRENT_STANCE_SELF_REPORT",
                "VERA",
                [SimpleNamespace(evidence_class="vera_current_self_report")],
                CONTRACT,
            )

    def test_direct_runtime_abstract_evaluator_is_explicit_and_preserves_fixture_semantics(self):
        decision = runtime.evaluate_abstract_proposition_admission(
            "SELF_APPRAISAL_AND_EMPATHY",
            "VERA_CURRENT_STANCE_SELF_REPORT",
            "VERA",
            [SimpleNamespace(evidence_class="vera_current_self_report")],
            CONTRACT,
        )
        self.assertEqual(decision.status, "ADMITTED")

    def test_direct_runtime_public_admission_accepts_current_bound_envelope(self):
        decision = runtime.evaluate_proposition_admission(
            "SELF_APPRAISAL_AND_EMPATHY",
            "VERA_CURRENT_STANCE_SELF_REPORT",
            "VERA",
            [envelope()],
            CONTRACT,
        )
        self.assertEqual(decision.status, "ADMITTED")


if __name__ == "__main__":
    unittest.main()
