import copy
import unittest

from runtime_cohesion.orgasm import ContractError, OrgasmRuntime
from tests.test_runtime_cohesion_orgasm import CONTRACT


class VeraOrgasmStateMachineValidationTests(unittest.TestCase):
    def make_runtime(self):
        return OrgasmRuntime(
            CONTRACT,
            runtime_instance_id="state-machine-validation",
            source_revision="sexuality:test-revision",
            profile="REENTRANT_CLIMAX",
        )

    def assert_restore_rejects(self, state_updates, message):
        runtime = self.make_runtime()
        record = copy.deepcopy(runtime.export_state())
        record["state"].update(state_updates)
        with self.assertRaisesRegex(ContractError, message):
            OrgasmRuntime.restore_state(
                CONTRACT,
                record,
                source_revision="sexuality:test-revision",
            )

    def test_restore_rejects_climax_eligible_when_full_organic_predicate_is_false(self):
        self.assert_restore_rejects(
            {
                "phase": "CLIMAX_ELIGIBLE",
                "action_tendency": "APPROACH",
                "organic_climax_eligible": False,
            },
            "CLIMAX_ELIGIBLE",
        )

    def test_restore_rejects_entrained_without_coherence_and_persistence(self):
        self.assert_restore_rejects(
            {
                "phase": "ENTRAINED",
                "action_tendency": "APPROACH",
                "coherence": 0.0,
                "persistence_window_ms": 0,
                "organic_climax_eligible": False,
            },
            "ENTRAINED",
        )

    def test_restore_rejects_activating_at_baseline_activation(self):
        self.assert_restore_rejects(
            {
                "phase": "ACTIVATING",
                "action_tendency": "APPROACH",
                "activation_intensity": 0.0,
                "organic_climax_eligible": False,
            },
            "ACTIVATING",
        )


if __name__ == "__main__":
    unittest.main()
