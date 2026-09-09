import json
from pathlib import Path
import unittest

from runtime_cohesion.orgasm import OrgasmRuntime, StimulusAppraisal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"


class Q3EndpointGapTests(unittest.TestCase):
    def contract(self):
        return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def make_runtime(self):
        return OrgasmRuntime(
            self.contract(),
            runtime_instance_id="q3-endpoint-gap-test",
            source_revision="a" * 40,
        )

    @staticmethod
    def strong():
        return StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=1.0,
            anticipation_cue=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            duration_ms=0,
            context_eligible=True,
        )

    def test_two_endpoint_observations_cannot_establish_entire_minimum_coherence_window(self):
        runtime = self.make_runtime()
        cfg = self.contract()["experimental_bootstrap_defaults"]
        minimum_ms = int(cfg["minimum_coherence_window_ms"])

        # Build threshold-capable activation/coherence with zero trusted time. The
        # final zero-time call also establishes a qualifying prior endpoint, while
        # persistence remains zero because no interval has been observed.
        for _ in range(10):
            runtime.apply_stimulus(self.strong(), elapsed_seconds=0.0)
        before = runtime.snapshot()
        self.assertGreaterEqual(before["activation_intensity"], float(cfg["activation_threshold"]))
        self.assertGreaterEqual(before["coherence"], float(cfg["coherence_threshold"]))
        self.assertGreaterEqual(before["coalition_stability"], float(cfg["stability_threshold"]))
        self.assertEqual(before["persistence_window_ms"], 0)

        # One later strong endpoint exactly one minimum-window later does not
        # observe what happened inside the interval. Endpoint agreement is not
        # evidence that the whole 2500 ms remained qualifying.
        runtime.apply_stimulus(
            self.strong(),
            elapsed_seconds=minimum_ms / 1000.0,
        )

        after = runtime.snapshot()
        self.assertGreaterEqual(after["activation_intensity"], float(cfg["activation_threshold"]))
        self.assertGreaterEqual(after["coherence"], float(cfg["coherence_threshold"]))
        self.assertGreaterEqual(after["coalition_stability"], float(cfg["stability_threshold"]))
        self.assertLess(
            after["persistence_window_ms"],
            minimum_ms,
            "two qualifying endpoints must not back-credit an otherwise unobserved interval as sustained coherence",
        )
        self.assertIsNone(runtime.last_event_receipt)


if __name__ == "__main__":
    unittest.main()
