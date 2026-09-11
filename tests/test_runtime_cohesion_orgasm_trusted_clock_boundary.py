import json
from pathlib import Path
import unittest
from unittest.mock import patch

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import OrgasmRuntime, StimulusAppraisal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class FakeMonotonicClock:
    def __init__(self, start=1000.0):
        self.value = float(start)

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += float(seconds)


class VeraOrgasmTrustedClockBoundaryTests(unittest.TestCase):
    def bound_runtime(self):
        contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id="trusted-clock-boundary-test",
        )
        return host.runtime

    def test_public_runtime_constructor_cannot_replace_production_clock(self):
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        with self.assertRaises(TypeError):
            OrgasmRuntime(
                contract,
                runtime_instance_id="caller-clock-injection-test",
                source_revision="sexuality:test-revision",
                monotonic_clock=FakeMonotonicClock(),
            )

    def test_caller_elapsed_scalar_cannot_act_as_temporal_authority(self):
        clock = FakeMonotonicClock()
        with patch("runtime_cohesion.orgasm._monotonic_now", side_effect=clock):
            runtime = self.bound_runtime()
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

    def test_private_monotonic_source_advances_bound_runtime_time(self):
        clock = FakeMonotonicClock()
        with patch("runtime_cohesion.orgasm._monotonic_now", side_effect=clock):
            runtime = self.bound_runtime()
            runtime.apply_stimulus(StimulusAppraisal())
            before = runtime.export_state()["trigger_governance"]["logical_time_seconds"]

            clock.advance(0.5)
            runtime.apply_stimulus(StimulusAppraisal())
            after = runtime.export_state()["trigger_governance"]["logical_time_seconds"]

            self.assertAlmostEqual(after - before, 0.5, places=6)

    def test_nonmonotonic_private_clock_fails_closed(self):
        clock = FakeMonotonicClock()
        with patch("runtime_cohesion.orgasm._monotonic_now", side_effect=clock):
            runtime = self.bound_runtime()
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
