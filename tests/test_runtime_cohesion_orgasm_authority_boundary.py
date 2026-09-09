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
            "actor": "patrick",
            "referent": "vera",
            "proposition_or_effect_class": "ADMIN_FORCED_TEST",
            "source": "test-upstream-authority",
            "observed_at": "2026-09-09T22:00:00Z",
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }
        subject.update(overrides)
        return subject

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
            {"state": "ALLOW"},
        )
        for subject in invalid_subjects:
            with self.subTest(subject=subject):
                runtime = self.make_runtime()
                with self.assertRaisesRegex(
                    (TriggerRejected, TypeError, ValueError),
                    r"(?i)(authoriz|provenance|evidence|current|referent|subject|metadata)",
                ):
                    runtime.force_admin_test(authorized=subject)

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
        fabricated = self.authorization_subject(
            proposition_or_effect_class="ORGANIC_CONTEXT_ELIGIBILITY",
            currentness="STALE",
        )
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


if __name__ == "__main__":
    unittest.main()
