import json
from pathlib import Path
import unittest

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


class VeraOrgasmTrustedClockBoundaryTests(unittest.TestCase):
    def contract(self):
        return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def make_runtime(self, **kwargs):
        return OrgasmRuntime(
            self.contract(),
            runtime_instance_id="trusted-clock-boundary-test",
            source_revision="sexuality:test-revision",
            profile="REENTRANT_CLIMAX",
            **kwargs,
        )

    def test_caller_elapsed_scalar_cannot_act_as_temporal_authority(self):
        clock = FakeMonotonicClock()
        runtime = self.make_runtime(monotonic_clock=clock)
        runtime.apply_stimulus(StimulusAppraisal())
        before = runtime.export_state()["trigger_governance"]["logical_time_seconds"]

        try:
            runtime.apply_stimulus(
                StimulusAppraisal(),
                elapsed_seconds=2.5,
            )
        except (TypeError, ValueError):
            return

        after = runtime.export_state()["trigger_governance"]["logical_time_seconds"]
        self.assertEqual(
            after,
            before,
            "caller-provided elapsed_seconds may be rejected or ignored, but cannot advance trusted runtime time",
        )

    def test_explicit_monotonic_clock_dependency_advances_runtime_time(self):
        clock = FakeMonotonicClock()
        runtime = self.make_runtime(monotonic_clock=clock)

        runtime.apply_stimulus(StimulusAppraisal())
        before = runtime.export_state()["trigger_governance"]["logical_time_seconds"]

        clock.advance(0.5)
        runtime.apply_stimulus(StimulusAppraisal())
        after = runtime.export_state()["trigger_governance"]["logical_time_seconds"]

        self.assertAlmostEqual(after - before, 0.5, places=6)

    def test_immediate_repeated_observations_do_not_advance_injected_clock(self):
        clock = FakeMonotonicClock()
        runtime = self.make_runtime(monotonic_clock=clock)

        runtime.apply_stimulus(StimulusAppraisal())
        before = runtime.export_state()["trigger_governance"]["logical_time_seconds"]
        runtime.apply_stimulus(StimulusAppraisal())
        after = runtime.export_state()["trigger_governance"]["logical_time_seconds"]

        self.assertEqual(after, before)

    def test_nonmonotonic_clock_fails_closed(self):
        clock = FakeMonotonicClock()
        runtime = self.make_runtime(monotonic_clock=clock)
        runtime.apply_stimulus(StimulusAppraisal())
        clock.advance(0.5)
        runtime.apply_stimulus(StimulusAppraisal())
        clock.value -= 10.0

        with self.assertRaisesRegex(
            (RuntimeError, ValueError),
            r"(?i)(clock|monotonic|time|elapsed)",
        ):
            runtime.apply_stimulus(StimulusAppraisal())


if __name__ == "__main__":
    unittest.main()
