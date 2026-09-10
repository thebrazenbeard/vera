import copy
import unittest
from unittest.mock import patch

from runtime_cohesion.orgasm import ContractError, OrgasmRuntime, StimulusAppraisal
from tests.test_runtime_cohesion_orgasm import CONTRACT


class FakeMonotonicClock:
    def __init__(self, start=1000.0):
        self.value = float(start)

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += float(seconds)


class VeraOrgasmStateMachineValidationTests(unittest.TestCase):
    def make_runtime(self):
        return OrgasmRuntime(
            CONTRACT,
            runtime_instance_id="state-machine-validation",
            source_revision="sexuality:test-revision",
            profile="REENTRANT_CLIMAX",
        )

    @staticmethod
    def strong_appraisal():
        return StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=0.7,
            anticipation_cue=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            duration_ms=0,
            context_eligible=True,
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

    def test_runtime_generated_entrained_state_with_zero_persistence_can_restore(self):
        clock = FakeMonotonicClock()
        with patch("runtime_cohesion.orgasm._monotonic_now", side_effect=clock):
            runtime = self.make_runtime()
            runtime.apply_stimulus(self.strong_appraisal())
            clock.advance(0.5)
            runtime.apply_stimulus(self.strong_appraisal())
            self.assertEqual(runtime.snapshot()["phase"], "ENTRAINED")
            self.assertGreater(runtime.snapshot()["persistence_window_ms"], 0)

            # Standalone time advance is an explicitly unobserved interval. It
            # clears coherence-continuity persistence, but the executable state
            # machine does not demote ENTRAINED solely for that reason.
            runtime.advance_time(1.0)
            snapshot = runtime.snapshot()
            self.assertEqual(snapshot["phase"], "ENTRAINED")
            self.assertEqual(snapshot["persistence_window_ms"], 0)
            self.assertGreaterEqual(snapshot["coherence"], 0.45)

            record = copy.deepcopy(runtime.export_state())
            restored = OrgasmRuntime.restore_state(
                CONTRACT,
                record,
                source_revision="sexuality:test-revision",
            )
            self.assertEqual(restored.snapshot()["phase"], "ENTRAINED")
            self.assertEqual(restored.snapshot()["persistence_window_ms"], 0)

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
