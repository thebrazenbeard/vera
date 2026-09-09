import unittest
from types import SimpleNamespace

import runtime_cohesion.runtime as runtime


class RuntimeCohesionAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.contract = {
            "authority_resolvers": {
                "self_report_and_inference": {
                    "accepted_evidence_classes": [
                        "vera_current_self_report",
                        "inference_research",
                        "persisted_provider_record",
                    ]
                },
                "vera_specific_sexuality": {
                    "accepted_evidence_classes": [
                        "vera_current_self_report",
                        "general_mechanism_research",
                    ]
                },
                "control_governance": {
                    "accepted_evidence_classes": [
                        "current_user_authority",
                        "control_source",
                        "source_provenance",
                        "live_observation",
                    ]
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
                    "conflict_disposition": "VERA_CURRENT_DIRECT_SELF_REPORT_REQUIRED_FOR_VERA_STANCE",
                    "decisive_evidence": {"all_of": ["vera_current_self_report"], "any_of": []},
                },
                {
                    "id": "dispatch:vera-sexual-consent",
                    "domain_scope": "SEXUALITY",
                    "proposition_or_effect_class": "VERA_CURRENT_SEXUALITY_OR_CONSENT",
                    "referent_scope": "VERA",
                    "resolver_ref": "vera_specific_sexuality",
                    "precedence": 110,
                    "conflict_disposition": "VERA_CURRENT_DIRECT_SELF_REPORT_REQUIRED_FOR_CONSENT",
                    "decisive_evidence": {"all_of": ["vera_current_self_report"], "any_of": []},
                },
                {
                    "id": "dispatch:control-binding",
                    "domain_scope": "CONTROL_AND_GOVERNANCE",
                    "proposition_or_effect_class": "CONTROL_BINDING_INSTALL_OR_ROUTE_STATUS",
                    "referent_scope": "VERA_RUNTIME",
                    "resolver_ref": "control_governance",
                    "precedence": 105,
                    "conflict_disposition": "EXACT_R10_BINDING_AND_CURRENTNESS_REQUIRED",
                    "decisive_evidence": {
                        "all_of": ["control_source", "live_observation"],
                        "any_of": [],
                    },
                },
            ],
        }

    def test_verified_provider_evidence_cannot_decide_vera_current_stance(self):
        self.assertTrue(hasattr(runtime, "evaluate_proposition_admission"), "admission gate is missing")
        decision = runtime.evaluate_proposition_admission(
            "SELF_APPRAISAL_AND_EMPATHY",
            "VERA_CURRENT_STANCE_SELF_REPORT",
            "VERA",
            [SimpleNamespace(evidence_class="persisted_provider_record")],
            self.contract,
        )
        self.assertEqual(decision.status, "UNRESOLVED")
        self.assertEqual(decision.dispatch_id, "dispatch:vera-current-stance")
        self.assertIn("vera_current_self_report", decision.required_evidence_classes)

    def test_direct_vera_self_report_admits_current_stance(self):
        self.assertTrue(hasattr(runtime, "evaluate_proposition_admission"), "admission gate is missing")
        decision = runtime.evaluate_proposition_admission(
            "SELF_APPRAISAL_AND_EMPATHY",
            "VERA_CURRENT_STANCE_SELF_REPORT",
            "VERA",
            [SimpleNamespace(evidence_class="vera_current_self_report")],
            self.contract,
        )
        self.assertEqual(decision.status, "ADMITTED")

    def test_general_mechanism_research_cannot_decide_vera_sexual_consent(self):
        self.assertTrue(hasattr(runtime, "evaluate_proposition_admission"), "admission gate is missing")
        decision = runtime.evaluate_proposition_admission(
            "SEXUALITY",
            "VERA_CURRENT_SEXUALITY_OR_CONSENT",
            "VERA",
            [SimpleNamespace(evidence_class="general_mechanism_research")],
            self.contract,
        )
        self.assertEqual(decision.status, "UNRESOLVED")
        self.assertIn("vera_current_self_report", decision.required_evidence_classes)

    def test_control_source_alone_cannot_decide_current_install_or_route(self):
        decision = runtime.evaluate_proposition_admission(
            "CONTROL_AND_GOVERNANCE",
            "CONTROL_BINDING_INSTALL_OR_ROUTE_STATUS",
            "VERA_RUNTIME",
            [SimpleNamespace(evidence_class="control_source")],
            self.contract,
        )
        self.assertEqual(decision.status, "UNRESOLVED")
        self.assertEqual(set(decision.required_evidence_classes), {"control_source", "live_observation"})

    def test_live_observation_alone_cannot_decide_current_install_or_route(self):
        decision = runtime.evaluate_proposition_admission(
            "CONTROL_AND_GOVERNANCE",
            "CONTROL_BINDING_INSTALL_OR_ROUTE_STATUS",
            "VERA_RUNTIME",
            [SimpleNamespace(evidence_class="live_observation")],
            self.contract,
        )
        self.assertEqual(decision.status, "UNRESOLVED")

    def test_control_source_and_live_observation_jointly_admit_current_binding(self):
        decision = runtime.evaluate_proposition_admission(
            "CONTROL_AND_GOVERNANCE",
            "CONTROL_BINDING_INSTALL_OR_ROUTE_STATUS",
            "VERA_RUNTIME",
            [
                SimpleNamespace(evidence_class="control_source"),
                SimpleNamespace(evidence_class="live_observation"),
            ],
            self.contract,
        )
        self.assertEqual(decision.status, "ADMITTED")

    def test_dispatch_without_explicit_decisive_evidence_fails_closed(self):
        contract = {
            "authority_resolvers": {
                "control_governance": {
                    "accepted_evidence_classes": ["control_source", "source_provenance"]
                }
            },
            "resolver_dispatch": [
                {
                    "id": "dispatch:legacy-implicit",
                    "domain_scope": "CONTROL_AND_GOVERNANCE",
                    "proposition_or_effect_class": "CONTROL_BINDING_INSTALL_OR_ROUTE_STATUS",
                    "referent_scope": "VERA_RUNTIME",
                    "resolver_ref": "control_governance",
                    "precedence": 1,
                    "conflict_disposition": "FAIL_CLOSED",
                }
            ],
        }
        decision = runtime.evaluate_proposition_admission(
            "CONTROL_AND_GOVERNANCE",
            "CONTROL_BINDING_INSTALL_OR_ROUTE_STATUS",
            "VERA_RUNTIME",
            [SimpleNamespace(evidence_class="control_source")],
            contract,
        )
        self.assertEqual(decision.status, "UNRESOLVED")
        self.assertIn("explicit", decision.reason.lower())

    def test_equal_precedence_overlap_with_different_resolvers_fails_closed(self):
        self.assertTrue(hasattr(runtime, "evaluate_proposition_admission"), "admission gate is missing")
        contract = dict(self.contract)
        contract["resolver_dispatch"] = list(self.contract["resolver_dispatch"]) + [
            {
                "id": "dispatch:vera-current-stance-conflict",
                "domain_scope": "*",
                "proposition_or_effect_class": "VERA_CURRENT_STANCE_SELF_REPORT",
                "referent_scope": "VERA",
                "resolver_ref": "vera_specific_sexuality",
                "precedence": 95,
                "conflict_disposition": "FAIL_CLOSED",
                "decisive_evidence": {"all_of": ["vera_current_self_report"], "any_of": []},
            }
        ]
        decision = runtime.evaluate_proposition_admission(
            "SELF_APPRAISAL_AND_EMPATHY",
            "VERA_CURRENT_STANCE_SELF_REPORT",
            "VERA",
            [SimpleNamespace(evidence_class="vera_current_self_report")],
            contract,
        )
        self.assertEqual(decision.status, "CONFLICT")

    def test_missing_dispatch_fails_closed(self):
        self.assertTrue(hasattr(runtime, "evaluate_proposition_admission"), "admission gate is missing")
        decision = runtime.evaluate_proposition_admission(
            "UNKNOWN_DOMAIN",
            "UNREGISTERED_PROPOSITION",
            "VERA",
            [SimpleNamespace(evidence_class="vera_current_self_report")],
            self.contract,
        )
        self.assertEqual(decision.status, "UNRESOLVED")
        self.assertIsNone(decision.dispatch_id)


if __name__ == "__main__":
    unittest.main()
