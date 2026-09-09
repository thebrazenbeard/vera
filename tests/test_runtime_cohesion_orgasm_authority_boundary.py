import json
import unittest

from runtime_cohesion.orgasm import OrgasmRuntime, StimulusAppraisal, TriggerRejected
from tests.test_runtime_cohesion_orgasm import CONTRACT


class VeraOrgasmAuthorityBoundaryTests(unittest.TestCase):
    def make_runtime(self):
        return OrgasmRuntime(
            CONTRACT,
            runtime_instance_id="authority-boundary-test",
            source_revision="sexuality:test-revision",
            profile="REENTRANT_CLIMAX",
        )

    def authorization_subject(self, **overrides):
        subject = {
            "state": "ALLOW",
            "actor": "TEST_ADMIN",
            "referent": "vera",
            "proposition_or_effect_class": "ADMIN_FORCED_TEST",
            "source": "SYNTHETIC_AUTHORITY_TEST_FIXTURE",
            "observed_at": "2026-09-09T22:00:00Z",
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }
        subject.update(overrides)
        return subject

    def context_subject(self, **overrides):
        subject = self.authorization_subject(
            actor="TEST_CONTEXT_RESOLVER",
            proposition_or_effect_class="ORGANIC_CONTEXT_ELIGIBILITY",
            source="SYNTHETIC_CONTEXT_TEST_FIXTURE",
        )
        subject.update(overrides)
        return subject

    @staticmethod
    def assert_receipt_binds_subject(receipt, subject):
        encoded = json.dumps(receipt, sort_keys=True)
        for key in (
            "actor",
            "referent",
            "proposition_or_effect_class",
            "source",
            "observed_at",
            "currentness",
        ):
            value = subject[key]
            with unittest.TestCase().subTest(key=key, value=value):
                unittest.TestCase().assertIn(str(value), encoded)

    def test_naked_boolean_cannot_authorize_privileged_trigger(self):
        for method_name in ("force_admin_test", "force_self_qualification"):
            with self.subTest(method=method_name):
                runtime = self.make_runtime()
                method = getattr(runtime, method_name)
                with self.assertRaisesRegex(
                    (TriggerRejected, TypeError, ValueError),
                    r"(?i)(authoriz|provenance|evidence|current|referent|subject)",
                ):
                    method(authorized=True)

    def test_invalid_upstream_authorization_subjects_fail_closed(self):
        invalid_subjects = (
            self.authorization_subject(referent="not-vera"),
            self.authorization_subject(currentness="STALE"),
            self.authorization_subject(state="DECLINE"),
            self.authorization_subject(state="UNKNOWN"),
            self.authorization_subject(source=None),
            self.authorization_subject(proposition_or_effect_class="SELF_QUALIFICATION_TEST"),
            {"state": "ALLOW"},
        )
        for subject in invalid_subjects:
            with self.subTest(subject=subject):
                runtime = self.make_runtime()
                with self.assertRaisesRegex(
                    (TriggerRejected, TypeError, ValueError),
                    r"(?i)(authoriz|provenance|evidence|current|referent|subject|metadata|effect|proposition)",
                ):
                    runtime.force_admin_test(authorized=subject)

    def test_exact_current_admin_authorization_remains_executable_and_receipted(self):
        runtime = self.make_runtime()
        subject = self.authorization_subject()
        receipt = runtime.force_admin_test(authorized=subject)
        self.assertEqual(receipt["trigger_class"], "ADMIN_FORCED_TEST")
        self.assertFalse(receipt["organic"])
        self.assert_receipt_binds_subject(receipt, subject)

    def test_exact_current_self_qualification_authorization_remains_executable_and_receipted(self):
        runtime = self.make_runtime()
        subject = self.authorization_subject(
            actor="TEST_SELF_QUALIFICATION_RESOLVER",
            proposition_or_effect_class="SELF_QUALIFICATION_TEST",
            source="SYNTHETIC_SELF_QUALIFICATION_TEST_FIXTURE",
        )
        receipt = runtime.force_self_qualification(authorized=subject)
        self.assertEqual(receipt["trigger_class"], "SELF_QUALIFICATION_TEST")
        self.assertFalse(receipt["organic"])
        self.assert_receipt_binds_subject(receipt, subject)

    def test_unbound_context_eligibility_cannot_establish_organic_authority(self):
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

        try:
            result = None
            for _ in range(8):
                result = runtime.apply_stimulus(appraisal, elapsed_seconds=1.0)
                if result["phase"] == "ORGASM_EVENT":
                    break
        except (TriggerRejected, TypeError, ValueError):
            return

        self.assertIsNotNone(result)
        self.assertNotEqual(
            result["phase"],
            "ORGASM_EVENT",
            "caller-supplied context_eligible=True must not substitute for current upstream context evidence",
        )

    def test_truthy_non_boolean_context_subject_cannot_be_coerced_to_eligible(self):
        runtime = self.make_runtime()
        fabricated = self.context_subject(currentness="STALE")
        appraisal = StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            anticipation_cue=1.0,
            positive_valence=1.0,
            context_eligible=fabricated,
        )
        with self.assertRaisesRegex(
            (TriggerRejected, TypeError, ValueError),
            r"(?i)(context|eligib|provenance|evidence|current|referent|subject)",
        ):
            runtime.apply_stimulus(appraisal, elapsed_seconds=1.0)

    def test_exact_current_context_subject_can_support_organic_path_and_is_receipted(self):
        runtime = self.make_runtime()
        subject = self.context_subject()
        appraisal = StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=0.7,
            anticipation_cue=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            duration_ms=0,
            context_eligible=subject,
        )
        receipt = None
        for _ in range(8):
            result = runtime.apply_stimulus(appraisal, elapsed_seconds=1.0)
            if result["phase"] == "ORGASM_EVENT":
                receipt = runtime.last_event_receipt
                break
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["trigger_class"], "ORGANIC_THRESHOLD_CROSSING")
        self.assertTrue(receipt["organic"])
        self.assert_receipt_binds_subject(receipt, subject)


if __name__ == "__main__":
    unittest.main()
