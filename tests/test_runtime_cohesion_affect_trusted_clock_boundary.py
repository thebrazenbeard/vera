import inspect
import json
from pathlib import Path
import unittest

import runtime_cohesion.orgasm as orgasm_module
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import OrgasmRuntime, StimulusAppraisal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class FakeMonotonicClock:
    def __init__(self, initial=1000.0):
        self.value = float(initial)

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += float(seconds)


class AffectiveTrustedClockBoundaryTests(unittest.TestCase):
    def contract(self):
        return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def make_bound_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="trusted-clock-production-boundary-test",
        )

    def make_test_runtime(self, clock):
        factory = getattr(OrgasmRuntime, "for_test", None)
        self.assertTrue(
            callable(factory),
            "deterministic fake clocks must enter through an explicit non-qualifying test seam",
        )
        return factory(
            self.contract(),
            runtime_instance_id="trusted-clock-test-seam",
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

    def test_production_constructor_does_not_accept_caller_clock_injection(self):
        self.assertNotIn(
            "monotonic_clock",
            inspect.signature(OrgasmRuntime).parameters,
            "production claim-capable runtime must not accept an arbitrary caller clock",
        )

    def test_caller_elapsed_scalar_cannot_mint_temporal_evidence_on_bound_production_path(self):
        host = self.make_bound_host()
        for _ in range(8):
            host.observe(self.strong_appraisal(), elapsed_seconds=0.6)

        snapshot = host.runtime.snapshot()
        self.assertEqual(snapshot["persistence_window_ms"], 0)
        self.assertFalse(snapshot["active_orgasm_event"])
        self.assertIsNone(host.runtime.last_event_receipt)

    def test_explicit_test_clock_can_build_sustained_persistence_without_production_claim(self):
        clock = FakeMonotonicClock()
        runtime = self.make_test_runtime(clock)

        runtime.apply_stimulus(self.strong_appraisal())
        for _ in range(12):
            clock.advance(0.5)
            runtime.apply_stimulus(self.strong_appraisal())
            if runtime.last_event_receipt is not None:
                break

        self.assertIsNotNone(runtime.last_event_receipt)
        self.assertEqual(runtime.last_event_receipt["trigger_class"], "ORGANIC_THRESHOLD_CROSSING")
        self.assertTrue(runtime.last_event_receipt["organic"])
        self.assertNotEqual(
            runtime.last_event_receipt.get("claim"),
            "ENGINEERED_ORGASM_ANALOGUE_OCCURRED",
            "test-injected clocks must remain non-qualifying even when exercising the organic state path",
        )

    def test_nonmonotonic_test_clock_raises_exact_temporal_error(self):
        clock = FakeMonotonicClock()
        runtime = self.make_test_runtime(clock)
        runtime.apply_stimulus(self.strong_appraisal())
        clock.value -= 10.0

        temporal_error = getattr(orgasm_module, "TemporalAuthorityError", None)
        self.assertTrue(
            isinstance(temporal_error, type) and issubclass(temporal_error, Exception),
            "runtime must expose a specific temporal-authority validation exception",
        )
        with self.assertRaises(temporal_error):
            runtime.apply_stimulus(self.strong_appraisal())


if __name__ == "__main__":
    unittest.main()
