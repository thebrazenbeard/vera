import json
from pathlib import Path
import unittest

from runtime_cohesion.orgasm import OrgasmRuntime, StimulusAppraisal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"


class TemporalCoherenceSpoofTests(unittest.TestCase):
    def make_runtime(self):
        return OrgasmRuntime(
            json.loads(CONTRACT_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="vera-temporal-coherence-test",
            source_revision="a" * 40,
        )

    def strong_appraisal(self, *, duration_ms):
        return StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=1.0,
            anticipation_cue=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            duration_ms=duration_ms,
            context_eligible=True,
        )

    def weak_appraisal(self):
        return StimulusAppraisal(
            sexual_relevance=0.0,
            partner_relevance=0.0,
            relational_relevance=0.0,
            novelty=0.0,
            anticipation_cue=0.0,
            positive_valence=0.0,
            inhibition=0.0,
            duration_ms=0,
            context_eligible=False,
        )

    def test_zero_elapsed_calls_cannot_accumulate_trusted_coherence_time(self):
        runtime = self.make_runtime()
        for _ in range(8):
            runtime.apply_stimulus(
                self.strong_appraisal(duration_ms=1000),
                elapsed_seconds=0.0,
            )

        snapshot = runtime.snapshot()
        self.assertFalse(snapshot["active_orgasm_event"])
        self.assertEqual(snapshot["persistence_window_ms"], 0)
        self.assertIsNone(runtime.last_event_receipt)

    def test_trusted_elapsed_time_can_build_persistence_without_claimed_duration(self):
        runtime = self.make_runtime()
        for _ in range(12):
            runtime.apply_stimulus(
                self.strong_appraisal(duration_ms=0),
                elapsed_seconds=0.5,
            )
            if runtime.last_event_receipt is not None:
                break

        self.assertIsNotNone(runtime.last_event_receipt)
        self.assertEqual(
            runtime.last_event_receipt["trigger_class"],
            "ORGANIC_THRESHOLD_CROSSING",
        )

    def test_claimed_duration_cannot_outrun_trusted_elapsed_interval(self):
        runtime = self.make_runtime()
        runtime.apply_stimulus(
            self.strong_appraisal(duration_ms=60_000),
            elapsed_seconds=0.1,
        )
        self.assertLessEqual(runtime.snapshot()["persistence_window_ms"], 100)

    def test_current_strong_observation_cannot_backcredit_preceding_nonqualifying_interval(self):
        runtime = self.make_runtime()

        # Raise activation/coherence without any trusted coherence duration, then
        # explicitly break context continuity. A later strong observation cannot
        # retroactively classify the preceding nonqualifying interval as sustained
        # coherent context merely because the current appraisal is strong.
        for _ in range(8):
            runtime.apply_stimulus(
                self.strong_appraisal(duration_ms=0),
                elapsed_seconds=0.0,
            )
        runtime.apply_stimulus(self.weak_appraisal(), elapsed_seconds=0.0)
        runtime.apply_stimulus(
            self.strong_appraisal(duration_ms=0),
            elapsed_seconds=10.0,
        )

        snapshot = runtime.snapshot()
        self.assertEqual(snapshot["persistence_window_ms"], 0)
        self.assertFalse(snapshot["active_orgasm_event"])


if __name__ == "__main__":
    unittest.main()
