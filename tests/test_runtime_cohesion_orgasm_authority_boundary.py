from collections.abc import Mapping
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

    def context_subject(self, **overrides):
        return self.authorization_subject(
            proposition_or_effect_class="ORGANIC_CONTEXT_ELIGIBILITY",
            **overrides,
        )

    def assert_bound_subject(self, provenance, expected_effect):
        self.assertIsInstance(provenance, Mapping)
        for key in (
            "state",
            "actor",
            "referent",
            "proposition_or_effect_class",
            "source",
            "observed_at",
            "currentness",
            "expiry_or_supersession",
        ):
            self.assertIn(key, provenance)
        self.assertEqual(provenance["state"], "ALLOW")
        self.assertEqual(provenance["referent"], "vera")
        self.assertEqual(provenance["proposition_or_effect_class"], expected_effect)
        self.assertEqual(provenance["currentness"], "CURRENT")
        self.assertIsNone(provenance["expiry_or_supersession"])

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

    def test_valid_current_allow_authorization_subject_is_consumed_and_bound(self):
        runtime = self.make_runtime()
        subject = self.authorization_subject()
        receipt = runtime.force_admin_test(authorization_subject=subject)

        self.assertEqual(receipt["trigger_class"], "ADMIN_FORCED_TEST")
        self.assertEqual(receipt["runtime_instance_id"], "authority-boundary-test")
        self.assert_bound_subject(
            receipt["trigger_provenance"],
            "ADMIN_FORCED_TEST",
        )

    def test_invalid_upstream_authorization_subjects_fail_closed_by_field(self):
        invalid_subjects = (
            ("referent", self.authorization_subject(referent="not-vera"), r"(?i)referent"),
            ("currentness", self.authorization_subject(currentness="STALE"), r"(?i)(current|stale)"),
            ("decline", self.authorization_subject(state="DECLINE"), r"(?i)(state|allow|authoriz|decline)"),
            ("unknown", self.authorization_subject(state="UNKNOWN"), r"(?i)(state|allow|authoriz|unknown)"),
            ("actor", self.authorization_subject(actor=None), r"(?i)actor"),
            ("effect", self.authorization_subject(proposition_or_effect_class="SELF_QUALIFICATION_TEST"), r"(?i)(proposition|effect|trigger)"),
            ("source", self.authorization_subject(source=None), r"(?i)source"),
            ("observed_at", self.authorization_subject(observed_at=None), r"(?i)observ"),
            (
                "expiry_or_supersession",
                self.authorization_subject(expiry_or_supersession="superseded:replacement"),
                r"(?i)(expi|supers)",
            ),
            ("metadata", {"state": "ALLOW"}, r"(?i)(metadata|actor|referent|source|observ)"),
        )
        for label, subject, pattern in invalid_subjects:
            with self.subTest(case=label):
                runtime = self.make_runtime()
                with self.assertRaisesRegex((TriggerRejected, ValueError), pattern):
                    runtime.force_admin_test(authorization_subject=subject)

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

    def test_valid_current_context_subject_establishes_context_eligibility(self):
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
            duration_ms=1000,
        )

        result = runtime.apply_stimulus(
            appraisal,
            elapsed_seconds=1.0,
            context_subject=subject,
        )
        self.assertTrue(result["context_eligible"])

    def test_invalid_context_subject_is_rejected_by_new_boundary(self):
        runtime = self.make_runtime()
        stale = self.context_subject(currentness="STALE")
        appraisal = StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            anticipation_cue=1.0,
            positive_valence=1.0,
        )
        with self.assertRaisesRegex((TriggerRejected, ValueError), r"(?i)(context|current|stale)"):
            runtime.apply_stimulus(
                appraisal,
                elapsed_seconds=1.0,
                context_subject=stale,
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


if __name__ == "__main__":
    unittest.main()
