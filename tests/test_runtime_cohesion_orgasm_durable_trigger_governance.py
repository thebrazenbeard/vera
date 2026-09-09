import copy
import unittest

from runtime_cohesion.orgasm import ContractError, OrgasmRuntime, TriggerRejected
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

    def test_restore_preserves_self_qualification_event_limit(self):
        runtime = self.make_runtime()
        runtime.force_self_qualification(authorized=True)
        runtime.advance_time(20.0)
        runtime.force_self_qualification(authorized=True)
        runtime.advance_time(20.0)

        restored = self.restore(runtime.export_state())

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

    def test_restore_rejects_incomplete_or_unknown_state_shape(self):
        record = self.make_runtime().export_state()

        missing = copy.deepcopy(record)
        del missing["state"]["activation_intensity"]
        with self.assertRaises(ContractError):
            self.restore(missing)

        extra = copy.deepcopy(record)
        extra["state"]["invented_hidden_feeling"] = 0.9
        with self.assertRaises(ContractError):
            self.restore(extra)

    def test_restore_rejects_out_of_range_and_phase_active_inconsistency(self):
        record = self.make_runtime().export_state()

        out_of_range = copy.deepcopy(record)
        out_of_range["state"]["activation_intensity"] = 1.5
        with self.assertRaises(ContractError):
            self.restore(out_of_range)

        impossible_phase = copy.deepcopy(record)
        impossible_phase["state"]["phase"] = "ORGASM_EVENT"
        impossible_phase["state"]["active_orgasm_event"] = False
        with self.assertRaises(ContractError):
            self.restore(impossible_phase)

    def test_restore_rejects_tampered_derived_organic_eligibility(self):
        record = self.make_runtime().export_state()
        self.assertFalse(record["state"]["organic_climax_eligible"])
        tampered = copy.deepcopy(record)
        tampered["state"]["organic_climax_eligible"] = True
        with self.assertRaises(ContractError):
            self.restore(tampered)

    def test_restore_elapsed_validation_uses_restore_contract_error(self):
        record = self.make_runtime().export_state()
        invalid_values = (True, "1", float("nan"), -0.1)
        for invalid in invalid_values:
            with self.subTest(elapsed_seconds=invalid):
                with self.assertRaises(ContractError):
                    self.restore(record, elapsed_seconds=invalid)


if __name__ == "__main__":
    unittest.main()
