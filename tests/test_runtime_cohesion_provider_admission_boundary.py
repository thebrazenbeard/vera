from types import SimpleNamespace
import unittest

from runtime_cohesion import (
    ProviderEvidenceEnvelope,
    evaluate_abstract_proposition_admission,
    evaluate_proposition_admission,
)


class ProviderAdmissionBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.contract = {
            "authority_resolvers": {
                "self_report_and_inference": {
                    "accepted_evidence_classes": ["vera_current_self_report"]
                }
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
                }
            ],
            "resolver_dispatch_decisive_evidence": {
                "dispatch:vera-current-stance": {
                    "all_of": ["vera_current_self_report"],
                    "any_of": [],
                }
            },
        }

    def envelope(self, *, conflict_state="NONE", supersession_state="CURRENT_OBSERVATION"):
        return ProviderEvidenceEnvelope(
            provider="TEST_PROVIDER",
            locator="test://vera/current-stance",
            revision="fixture-v1",
            observed_at="2026-09-09T21:30:00Z",
            evidence_class="vera_current_self_report",
            referent="SELF_APPRAISAL_AND_EMPATHY",
            scope="VERA",
            privacy_class="PRIVATE",
            currentness_basis="SYNTHETIC_TEST_FIXTURE",
            supersession_state=supersession_state,
            conflict_state=conflict_state,
            metadata={
                "proposition_or_effect_class": "VERA_CURRENT_STANCE_SELF_REPORT",
                "referent_scope": "VERA",
            },
        )

    def test_package_level_provider_admission_rejects_lightweight_evidence(self):
        with self.assertRaises(TypeError):
            evaluate_proposition_admission(
                "SELF_APPRAISAL_AND_EMPATHY",
                "VERA_CURRENT_STANCE_SELF_REPORT",
                "VERA",
                [SimpleNamespace(evidence_class="vera_current_self_report")],
                self.contract,
            )

    def test_explicit_abstract_evaluator_preserves_policy_fixture_semantics(self):
        decision = evaluate_abstract_proposition_admission(
            "SELF_APPRAISAL_AND_EMPATHY",
            "VERA_CURRENT_STANCE_SELF_REPORT",
            "VERA",
            [SimpleNamespace(evidence_class="vera_current_self_report")],
            self.contract,
        )
        self.assertEqual(decision.status, "ADMITTED")

    def test_current_bound_provider_envelope_admits(self):
        decision = evaluate_proposition_admission(
            "SELF_APPRAISAL_AND_EMPATHY",
            "VERA_CURRENT_STANCE_SELF_REPORT",
            "VERA",
            [self.envelope()],
            self.contract,
        )
        self.assertEqual(decision.status, "ADMITTED")

    def test_conflicted_or_superseded_provider_envelope_does_not_admit(self):
        for envelope in (
            self.envelope(conflict_state="CONFLICT"),
            self.envelope(supersession_state="SUPERSEDED"),
        ):
            with self.subTest(envelope=envelope):
                decision = evaluate_proposition_admission(
                    "SELF_APPRAISAL_AND_EMPATHY",
                    "VERA_CURRENT_STANCE_SELF_REPORT",
                    "VERA",
                    [envelope],
                    self.contract,
                )
                self.assertEqual(decision.status, "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
