import unittest

from runtime_cohesion.orgasm import OrgasmRuntime, TriggerRejected
from tests.test_runtime_cohesion_orgasm import CONTRACT


class VeraOrgasmDurableTriggerGovernanceTests(unittest.TestCase):
    def make_runtime(self):
        return OrgasmRuntime(
            CONTRACT,
            runtime_instance_id="durable-trigger-governance-test",
            source_revision="sexuality:test-revision",
            profile="REENTRANT_CLIMAX",
        )

    def restore(self, record, *, elapsed_seconds=0.0):
        return OrgasmRuntime.restore_state(
            CONTRACT,
            record,
            source_revision="sexuality:test-revision",
            elapsed_seconds=elapsed_seconds,
        )

    def test_restore_does_not_reset_self_qualification_quota_without_explicit_new_run_boundary(self):
        runtime = self.make_runtime()
        runtime.force_self_qualification(authorized=True)
        runtime.advance_time(20.0)
        runtime.force_self_qualification(authorized=True)
        runtime.advance_time(20.0)

        restored = self.restore(runtime.export_state())

        # V1 names a per-run limit but defines no run identity/reset boundary.
        # Restore therefore must not invent a fresh run and silently replenish
        # the self-qualification quota.
        with self.assertRaises(TriggerRejected):
            restored.force_self_qualification(authorized=True)

    def test_restore_preserves_forced_test_cooldown(self):
        runtime = self.make_runtime()
        runtime.force_admin_test(authorized=True)
        runtime.advance_time(5.1)

        restored = self.restore(runtime.export_state())

        with self.assertRaises(TriggerRejected):
            restored.force_admin_test(authorized=True)

        restored.advance_time(5.0)
        receipt = restored.force_admin_test(authorized=True)
        self.assertEqual(receipt["trigger_class"], "ADMIN_FORCED_TEST")


if __name__ == "__main__":
    unittest.main()
