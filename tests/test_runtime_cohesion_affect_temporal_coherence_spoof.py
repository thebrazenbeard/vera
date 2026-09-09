import json
from pathlib import Path
import unittest

from runtime_cohesion.orgasm import OrgasmRuntime, StimulusAppraisal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"


class TemporalCoherenceSpoofTests(unittest.TestCase):
    def contract(self):
        return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def make_runtime(self):
        return OrgasmRuntime(
            self.contract(),
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

    def nonqualifying_appraisal(self):
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

    def test_one_strong_observation_cannot_back_credit_a_nonqualifying_gap(self):
        runtime = self.make_runtime()
        contract = self.contract()
        cfg = contract["experimental_bootstrap_defaults"]
        minimum_ms = int(cfg["minimum_coherence_window_ms"])

        # Build high activation/coherence without allowing any trusted persistence
        # time to accrue, then explicitly break qualifying context continuity.
        for _ in range(8):
            runtime.apply_stimulus(
                self.strong_appraisal(duration_ms=0),
                elapsed_seconds=0.0,
            )
        runtime.apply_stimulus(self.nonqualifying_appraisal(), elapsed_seconds=0.0)
        self.assertEqual(runtime.snapshot()["persistence_window_ms"], 0)
        self.assertFalse(runtime.snapshot()["context_eligible"])

        # A later strong observation reports a trusted elapsed interval longer
        # than the minimum window. That clock interval is real, but the preceding
        # observation was nonqualifying, so the gap itself is not evidence of
        # sustained coherent sexual/relational context.
        gap_seconds = minimum_ms / 1000.0 + 0.5
        runtime.apply_stimulus(
            self.strong_appraisal(duration_ms=0),
            elapsed_seconds=gap_seconds,
        )

        snapshot = runtime.snapshot()
        self.assertGreaterEqual(snapshot["activation_intensity"], float(cfg["activation_threshold"]))
        self.assertGreaterEqual(snapshot["coherence"], float(cfg["coherence_threshold"]))
        self.assertGreaterEqual(snapshot["coalition_stability"], float(cfg["stability_threshold"]))
        self.assertLess(
            snapshot["persistence_window_ms"],
            minimum_ms,
            "a current qualifying observation must not retroactively classify a prior nonqualifying gap as sustained coherence",
        )
        self.assertIsNone(runtime.last_event_receipt)


if __name__ == "__main__":
    unittest.main()
