from collections.abc import Mapping
import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_integration_bound import CohesionAffectiveIntegrationPort
from runtime_cohesion.affect_signal import build_affective_modulation_signal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class TwoFacedSignal(Mapping):
    """A caller object that would expose different values across repeated reads."""

    def __init__(self, first, second):
        self._first = dict(first)
        self._second = dict(second)
        self._reads = 0

    def __iter__(self):
        return iter(self._first)

    def __len__(self):
        return len(self._first)

    def __getitem__(self, key):
        source = self._first if self._reads < len(self._first) else self._second
        self._reads += 1
        return source[key]


class AffectiveSignalMappingSnapshotTests(unittest.TestCase):
    def setUp(self):
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        self.host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            binding,
            runtime_instance_id="signal-mapping-snapshot-test",
            profile="REENTRANT_CLIMAX",
        )
        self.port = CohesionAffectiveIntegrationPort(host=self.host)

    def test_two_faced_mapping_cannot_enter_supported_causal_port(self):
        legitimate = build_affective_modulation_signal(self.host)
        forged = json.loads(json.dumps(legitimate))
        forged["target_modulation_strength"]["attention"] = 1.0
        forged["temporal_scope"]["logical_time_seconds"] = 1_000_000.0
        signal = TwoFacedSignal(legitimate, forged)
        planning = {"attention": 0.20}

        with self.assertRaises(TypeError):
            self.port.apply(planning, signal)

        self.assertEqual(signal._reads, 0)
        self.assertEqual(planning, {"attention": 0.20})
        self.assertEqual(self.port.minimum_logical_time_seconds, 0.0)


if __name__ == "__main__":
    unittest.main()
