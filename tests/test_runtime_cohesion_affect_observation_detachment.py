from __future__ import annotations

import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_bound_runtime import BoundVeraOrgasmRuntime


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"


class AffectiveObservationDetachmentTests(unittest.TestCase):
    def test_causal_observation_detaches_nested_receipt_before_lock_release(self):
        runtime = BoundVeraOrgasmRuntime(
            json.loads(CONTRACT_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="detached-observation-runtime",
            source_revision="test-source",
            profile="REENTRANT_CLIMAX",
        )
        runtime.last_event_receipt = {
            "receipt_id": "receipt-before",
            "nested": {"generation": 1},
        }

        observed = runtime._capture_causal_observation()
        runtime.last_event_receipt["nested"]["generation"] = 2

        self.assertEqual(observed["last_event_receipt"]["nested"]["generation"], 1)


if __name__ == "__main__":
    unittest.main()
