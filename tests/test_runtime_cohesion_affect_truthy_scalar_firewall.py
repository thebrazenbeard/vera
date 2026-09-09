import unittest

from runtime_cohesion.orgasm import ContractError, OrgasmRuntime, StimulusAppraisal, TriggerRejected
from tests.test_runtime_cohesion_orgasm import CONTRACT


class AffectiveTruthyScalarFirewallTests(unittest.TestCase):
    def make_runtime(self):
        return OrgasmRuntime(
            CONTRACT,
            runtime_instance_id="truthy-scalar-firewall",
            source_revision="sexuality:test-revision",
        )

    @staticmethod
    def appraisal(*, context_eligible):
        return StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=1.0,
            anticipation_cue=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            duration_ms=1000,
            context_eligible=context_eligible,
        )

    def test_context_eligible_must_be_real_boolean_not_truthy_scalar(self):
        runtime = self.make_runtime()
        for invalid in ("false", "true", 1, 0, [], {}):
            with self.subTest(context_eligible=invalid):
                with self.assertRaisesRegex(ContractError, r"(?i)(context|eligible|boolean)"):
                    runtime.apply_stimulus(self.appraisal(context_eligible=invalid))

    def test_admin_authorization_must_be_real_boolean_not_truthy_scalar(self):
        runtime = self.make_runtime()
        for invalid in ("false", "true", 1, [], {}):
            with self.subTest(authorized=invalid):
                with self.assertRaisesRegex(TriggerRejected, r"(?i)(authoriz|boolean|provenance)"):
                    runtime.force_admin_test(authorized=invalid)

    def test_self_qualification_authorization_must_be_real_boolean_not_truthy_scalar(self):
        runtime = self.make_runtime()
        for invalid in ("false", "true", 1, [], {}):
            with self.subTest(authorized=invalid):
                with self.assertRaisesRegex(TriggerRejected, r"(?i)(authoriz|boolean|provenance)"):
                    runtime.force_self_qualification(authorized=invalid)

    def test_real_false_still_rejects_and_real_true_remains_only_legacy_scalar_gate(self):
        runtime = self.make_runtime()
        with self.assertRaises(TriggerRejected):
            runtime.force_admin_test(authorized=False)

        receipt = runtime.force_admin_test(authorized=True)
        self.assertEqual(receipt["trigger_class"], "ADMIN_FORCED_TEST")
        self.assertFalse(receipt["organic"])


if __name__ == "__main__":
    unittest.main()
