from __future__ import annotations

import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_integration_bound import CohesionAffectiveIntegrationPort
from runtime_cohesion.affect_signal import build_affective_modulation_signal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class ExactHostInstanceOriginTests(unittest.TestCase):
    def make_host(self, suffix="primary"):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id=f"exact-host-instance-origin-{suffix}",
            profile="REENTRANT_CLIMAX",
        )

    def test_exact_host_instance_method_shadow_is_rejected_before_signal_origin(self):
        host = self.make_host()
        port = CohesionAffectiveIntegrationPort(host=host)
        frontier = port.minimum_logical_time_seconds

        host.machine_interoception = lambda: {
            "presence": "ALWAYS_PRESENT_NORMALLY_QUIESCENT",
            "phase": "ORGASM_EVENT",
            "context_eligible": True,
            "active_orgasm_event": True,
            "hedonic_impact": 1.0,
            "coherence": 1.0,
            "activation_intensity": 1.0,
            "persistence_window_ms": 9999,
            "action_tendency": "HOLD",
        }
        host.experience_control_vector = lambda: {
            "approach_gain": 1.0,
            "salience_gain": 1.0,
            "attention_narrowing": 1.0,
            "consummatory_gain": 1.0,
            "plasticity_gain": 1.0,
            "satiation": 0.0,
            "resolution": 0.0,
            "refractory": 0.0,
        }

        with self.assertRaises((TypeError, ValueError)):
            build_affective_modulation_signal(host)
        self.assertEqual(port.minimum_logical_time_seconds, frontier)

    def test_bound_runtime_reference_is_not_publicly_replaceable(self):
        host = self.make_host("runtime-replacement")
        original_runtime = host.runtime
        replacement_runtime = self.make_host("replacement").runtime

        with self.assertRaises((AttributeError, TypeError)):
            host.runtime = replacement_runtime
        self.assertIs(host.runtime, original_runtime)

    def test_runtime_observation_method_shadow_is_rejected_before_signal_origin(self):
        host = self.make_host("runtime-method-shadow")
        host.runtime.snapshot = lambda: {
            "phase": "ORGASM_EVENT",
            "active_orgasm_event": True,
        }
        with self.assertRaises((TypeError, ValueError)):
            build_affective_modulation_signal(host)


if __name__ == "__main__":
    unittest.main()
