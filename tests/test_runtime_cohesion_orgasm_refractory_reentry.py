import copy
import unittest

from runtime_cohesion.orgasm import (
    ContractError,
    OrgasmRuntime,
    StimulusAppraisal,
    TriggerRejected,
)
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

    def test_recovery_contract_state_is_explicit_and_survives_restore(self):
        refractory = self.make_runtime("REFRACTORY_COUPLED")
        refractory.force_admin_test(authorized=True)
        refractory.advance_time(20.0)
        refractory_state = refractory.snapshot()
        self.assertFalse(refractory_state["reentry_allowed"])
        self.assertIsNone(refractory_state["next_eligible_at"])

        restored = OrgasmRuntime.restore_state(
            CONTRACT,
            refractory.export_state(),
            source_revision="sexuality:test-revision",
        )
        self.assertFalse(restored.snapshot()["reentry_allowed"])
        with self.assertRaises(TriggerRejected):
            restored.force_admin_test(authorized=True)

        reentrant = self.make_runtime("REENTRANT_CLIMAX")
        reentrant.force_admin_test(authorized=True)
        reentrant.advance_time(20.0)
        reentrant_state = reentrant.snapshot()
        self.assertTrue(reentrant_state["reentry_allowed"])
        self.assertIsNone(reentrant_state["next_eligible_at"])

    def test_restore_rejects_refractory_reentry_forgery(self):
        runtime = self.make_runtime("REFRACTORY_COUPLED")
        runtime.force_admin_test(authorized=True)
        runtime.advance_time(20.0)
        record = copy.deepcopy(runtime.export_state())
        record["state"]["reentry_allowed"] = True

        with self.assertRaises(ContractError):
            OrgasmRuntime.restore_state(
                CONTRACT,
                record,
                source_revision="sexuality:test-revision",
            )

    def test_current_logical_time_runtime_rejects_wall_clock_reentry_schedule(self):
        runtime = self.make_runtime("REFRACTORY_COUPLED")
        record = copy.deepcopy(runtime.export_state())
        record["state"]["next_eligible_at"] = "2026-09-09T20:45:00+00:00"

        with self.assertRaises(ContractError):
            OrgasmRuntime.restore_state(
                CONTRACT,
                record,
                source_revision="sexuality:test-revision",
            )

    def test_restore_rejects_quiescent_state_with_unresolved_recovery_load(self):
        runtime = self.make_runtime("REFRACTORY_COUPLED")
        record = copy.deepcopy(runtime.export_state())
        state = record["state"]
        state["reentry_allowed"] = True
        state["next_eligible_at"] = None
        state["phase"] = "QUIESCENT"
        state["satiation"] = 0.90
        state["resolution_intensity"] = 1.0
        state["refractory_strength"] = 0.85
        state["action_tendency"] = "HOLD"

        with self.assertRaisesRegex(ContractError, "QUIESCENT recovery semantics"):
            OrgasmRuntime.restore_state(
                CONTRACT,
                record,
                source_revision="sexuality:test-revision",
            )


if __name__ == "__main__":
    unittest.main()
