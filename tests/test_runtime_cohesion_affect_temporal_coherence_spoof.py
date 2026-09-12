import json
from pathlib import Path
import unittest
from unittest.mock import patch

from runtime_cohesion.orgasm import OrgasmRuntime, StimulusAppraisal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"


class FakeMonotonicClock:
    def __init__(self, start=1000.0):
        self.value = float(start)

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += float(seconds)


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

    def test_zero_private_clock_advance_cannot_accumulate_trusted_coherence_time(self):
        clock = FakeMonotonicClock()
        with patch("runtime_cohesion.orgasm._monotonic_now", side_effect=clock, create=True):
            runtime = self.make_runtime()
            for _ in range(8):
                runtime.apply_stimulus(self.strong_appraisal(duration_ms=1000))

        snapshot = runtime.snapshot()
        self.assertFalse(snapshot["active_orgasm_event"])
        self.assertEqual(snapshot["persistence_window_ms"], 0)
        self.assertIsNone(runtime.last_event_receipt)

    def test_private_monotonic_time_can_build_persistence_without_claimed_duration(self):
        clock = FakeMonotonicClock()
        with patch("runtime_cohesion.orgasm._monotonic_now", side_effect=clock, create=True):
            runtime = self.make_runtime()
            runtime.apply_stimulus(self.strong_appraisal(duration_ms=0))
            clock.advance(0.5)
            runtime.apply_stimulus(self.strong_appraisal(duration_ms=0))

        self.assertGreater(runtime.snapshot()["persistence_window_ms"], 0)
        self.assertLessEqual(runtime.snapshot()["persistence_window_ms"], 500)

    def test_claimed_duration_cannot_outrun_private_monotonic_interval(self):
        clock = FakeMonotonicClock()
        with patch("runtime_cohesion.orgasm._monotonic_now", side_effect=clock, create=True):
            runtime = self.make_runtime()
            runtime.apply_stimulus(self.strong_appraisal(duration_ms=0))
            clock.advance(0.1)
            runtime.apply_stimulus(self.strong_appraisal(duration_ms=60_000))

        self.assertLessEqual(runtime.snapshot()["persistence_window_ms"], 100)

    def test_current_strong_observation_cannot_backcredit_preceding_nonqualifying_interval(self):
        clock = FakeMonotonicClock()
        with patch("runtime_cohesion.orgasm._monotonic_now", side_effect=clock, create=True):
            runtime = self.make_runtime()

            # Raise activation/coherence without any trusted duration, then
            # explicitly break context continuity. A later strong observation
            # cannot retroactively classify the preceding interval as sustained
            # coherent context merely because the current appraisal is strong.
            for _ in range(8):
                runtime.apply_stimulus(self.strong_appraisal(duration_ms=0))
            runtime.apply_stimulus(self.weak_appraisal())
            clock.advance(10.0)
            runtime.apply_stimulus(self.strong_appraisal(duration_ms=0))

        snapshot = runtime.snapshot()
        self.assertEqual(snapshot["persistence_window_ms"], 0)
        self.assertFalse(snapshot["active_orgasm_event"])

    def test_long_unobserved_gap_cannot_be_backcredited_from_two_endpoint_observations(self):
        clock = FakeMonotonicClock()
        with patch("runtime_cohesion.orgasm._monotonic_now", side_effect=clock, create=True):
            runtime = self.make_runtime()
            runtime.apply_stimulus(self.strong_appraisal(duration_ms=0))
            clock.advance(10.0)
            runtime.apply_stimulus(self.strong_appraisal(duration_ms=0))

        snapshot = runtime.snapshot()
        self.assertEqual(snapshot["persistence_window_ms"], 0)
        self.assertFalse(snapshot["active_orgasm_event"])


if __name__ == "__main__":
    unittest.main()
