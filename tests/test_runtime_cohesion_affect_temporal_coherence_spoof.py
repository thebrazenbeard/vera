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

    def strong_appraisal(self):
        return StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=1.0,
            anticipation_cue=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            duration_ms=1000,
            context_eligible=True,
        )

    def test_zero_elapsed_calls_cannot_accumulate_trusted_coherence_time(self):
        runtime = self.make_runtime()
        for _ in range(8):
            runtime.apply_stimulus(self.strong_appraisal(), elapsed_seconds=0.0)

        snapshot = runtime.snapshot()
        self.assertFalse(snapshot["active_orgasm_event"])
        self.assertEqual(snapshot["persistence_window_ms"], 0)
        self.assertIsNone(runtime.last_event_receipt)


if __name__ == "__main__":
    unittest.main()
