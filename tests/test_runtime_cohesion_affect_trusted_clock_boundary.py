import json
from pathlib import Path
import unittest

from runtime_cohesion.orgasm import OrgasmRuntime, StimulusAppraisal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"


class FakeMonotonicClock:
    def __init__(self, initial=1000.0):
        self.value = float(initial)

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += float(seconds)


class AffectiveTrustedClockBoundaryTests(unittest.TestCase):
    def make_runtime(self, clock):
        return OrgasmRuntime(
            json.loads(CONTRACT_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="trusted-clock-boundary-test",
            source_revision="a" * 40,
            monotonic_clock=clock,
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
            duration_ms=60000,
            context_eligible=True,
        )

    def test_caller_elapsed_scalar_cannot_mint_temporal_evidence(self):
        clock = FakeMonotonicClock()
        runtime = self.make_runtime(clock)

        for _ in range(8):
            runtime.apply_stimulus(self.strong_appraisal(), elapsed_seconds=0.6)

        snapshot = runtime.snapshot()
        self.assertEqual(snapshot["persistence_window_ms"], 0)
        self.assertFalse(snapshot["active_orgasm_event"])
        self.assertIsNone(runtime.last_event_receipt)

    def test_runtime_owned_monotonic_clock_can_build_sustained_persistence(self):
        clock = FakeMonotonicClock()
        runtime = self.make_runtime(clock)

        runtime.apply_stimulus(self.strong_appraisal())
        for _ in range(12):
            clock.advance(0.5)
            runtime.apply_stimulus(self.strong_appraisal())
            if runtime.last_event_receipt is not None:
                break

        self.assertIsNotNone(runtime.last_event_receipt)
        self.assertEqual(runtime.last_event_receipt["trigger_class"], "ORGANIC_THRESHOLD_CROSSING")
        self.assertTrue(runtime.last_event_receipt["organic"])

    def test_nonmonotonic_clock_cannot_create_positive_elapsed_credit(self):
        clock = FakeMonotonicClock()
        runtime = self.make_runtime(clock)
        runtime.apply_stimulus(self.strong_appraisal())
        clock.value -= 10.0

        with self.assertRaisesRegex(Exception, r"(?i)(clock|monotonic|time|elapsed)"):
            runtime.apply_stimulus(self.strong_appraisal())


if __name__ == "__main__":
    unittest.main()
