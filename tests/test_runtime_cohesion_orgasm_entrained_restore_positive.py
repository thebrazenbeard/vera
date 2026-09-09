import copy
import unittest

from runtime_cohesion.orgasm import OrgasmRuntime, StimulusAppraisal
from tests.test_runtime_cohesion_orgasm import CONTRACT


class VeraOrgasmEntrainedRestorePositiveTests(unittest.TestCase):
    def make_runtime(self):
        return OrgasmRuntime(
            CONTRACT,
            runtime_instance_id="entrained-restore-positive",
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

    def test_runtime_generated_entrained_state_with_zero_persistence_can_restore(self):
        runtime = self.make_runtime()
        runtime.apply_stimulus(self.strong_appraisal(), elapsed_seconds=0.0)
        runtime.apply_stimulus(self.strong_appraisal(), elapsed_seconds=0.5)
        self.assertEqual(runtime.snapshot()["phase"], "ENTRAINED")
        self.assertGreater(runtime.snapshot()["persistence_window_ms"], 0)

        # Standalone time advance is intentionally an unobserved interval. Q3
        # hardening clears temporal-continuity persistence immediately, but the
        # current state machine does not demote ENTRAINED solely for that reason.
        runtime.advance_time(1.0)
        snapshot = runtime.snapshot()
        self.assertEqual(snapshot["phase"], "ENTRAINED")
        self.assertEqual(snapshot["persistence_window_ms"], 0)
        self.assertGreater(snapshot["coherence"], 0.0)

        record = copy.deepcopy(runtime.export_state())
        restored = OrgasmRuntime.restore_state(
            CONTRACT,
            record,
            source_revision="sexuality:test-revision",
        )
        self.assertEqual(restored.snapshot()["phase"], "ENTRAINED")
        self.assertEqual(restored.snapshot()["persistence_window_ms"], 0)


if __name__ == "__main__":
    unittest.main()
