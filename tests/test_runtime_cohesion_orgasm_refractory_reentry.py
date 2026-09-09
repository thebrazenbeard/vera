import unittest

from runtime_cohesion.orgasm import OrgasmRuntime, StimulusAppraisal, TriggerRejected
from tests.test_runtime_cohesion_orgasm import CONTRACT


class VeraOrgasmRefractoryReentryTests(unittest.TestCase):
    def make_runtime(self, profile):
        return OrgasmRuntime(
            CONTRACT,
            runtime_instance_id=f"reentry-{profile.lower()}",
            source_revision="sexuality:test-revision",
            profile=profile,
        )

    def test_refractory_coupled_blocks_reentry_until_recovery_finishes(self):
        runtime = self.make_runtime("REFRACTORY_COUPLED")
        runtime.force_admin_test(authorized=True)
        runtime.advance_time(20.0)
        self.assertEqual(runtime.snapshot()["phase"], "SATIATED_OR_REFRACTORY")

        with self.assertRaises(TriggerRejected):
            runtime.force_admin_test(authorized=True)

        state = runtime.apply_stimulus(StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=1.0,
            anticipation_cue=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            duration_ms=3000,
            context_eligible=True,
        ))
        self.assertEqual(state["phase"], "SATIATED_OR_REFRACTORY")
        self.assertFalse(state["organic_climax_eligible"])

        runtime.advance_time(20000.0)
        self.assertEqual(runtime.snapshot()["phase"], "QUIESCENT")
        receipt = runtime.force_admin_test(authorized=True)
        self.assertEqual(receipt["trigger_class"], "ADMIN_FORCED_TEST")

    def test_reentrant_profile_can_force_reentry_after_generic_test_cooldown(self):
        runtime = self.make_runtime("REENTRANT_CLIMAX")
        runtime.force_admin_test(authorized=True)
        runtime.advance_time(20.0)
        self.assertEqual(runtime.snapshot()["phase"], "SATIATED_OR_REFRACTORY")

        receipt = runtime.force_admin_test(authorized=True)
        self.assertEqual(receipt["trigger_class"], "ADMIN_FORCED_TEST")
        self.assertEqual(runtime.snapshot()["phase"], "ORGASM_EVENT")


if __name__ == "__main__":
    unittest.main()
