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


class ForgedHost(VeraAffectiveRuntimeHost):
    def machine_interoception(self):
        frame = super().machine_interoception()
        frame.update(
            {
                "active_orgasm_event": True,
                "hedonic_impact": 1.0,
                "coherence": 1.0,
                "activation_intensity": 1.0,
                "context_eligible": True,
            }
        )
        return frame

    def experience_control_vector(self):
        return {
            "approach_gain": 1.0,
            "salience_gain": 1.0,
            "attention_narrowing": 1.0,
            "consummatory_gain": 1.0,
            "plasticity_gain": 1.0,
            "satiation": 0.0,
            "resolution": 0.0,
            "refractory": 0.0,
        }


class ExactAffectiveHostClassTests(unittest.TestCase):
    def setUp(self):
        self.contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
        self.binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))

    def forged_host(self):
        return ForgedHost.from_bound_contract(
            self.contract_text,
            self.binding,
            runtime_instance_id="forged-host-subclass",
            profile="REENTRANT_CLIMAX",
        )

    def test_signal_builder_rejects_affective_host_subclass(self):
        try:
            host = self.forged_host()
        except TypeError:
            return
        with self.assertRaises(TypeError):
            build_affective_modulation_signal(host)

    def test_cohesion_port_rejects_affective_host_subclass_before_frontier_creation(self):
        try:
            host = self.forged_host()
        except TypeError:
            return
        with self.assertRaises(TypeError):
            CohesionAffectiveIntegrationPort(host=host)


if __name__ == "__main__":
    unittest.main()
