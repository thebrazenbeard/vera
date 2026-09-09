import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class ResolutionPlasticityPolarityTests(unittest.TestCase):
    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="resolution-plasticity-polarity",
            profile="REFRACTORY_COUPLED",
        )

    def recovery_context(self):
        host = self.make_host()
        host.force_admin_test(authorized=True)
        host.advance_time(5.1)
        frame = host.machine_interoception()
        self.assertIn(frame["phase"], {"RESOLUTION", "SATIATED_OR_REFRACTORY"})
        self.assertFalse(frame["active_orgasm_event"])
        self.assertGreater(frame["resolution_intensity"], 0.0)
        self.assertGreater(frame["satiation"], 0.0)

        planning = {
            "valuation": 0.5,
            "salience": 0.5,
            "attention": 0.5,
            "response_selection_priors": 0.5,
            "expression": 0.5,
            "memory_strength_candidate_weighting": 0.5,
        }
        return frame, planning, host.build_planning_context(planning)

    def test_resolution_does_not_reopen_memory_strength_candidate_window(self):
        _, planning, context = self.recovery_context()
        self.assertLessEqual(
            context["memory_strength_candidate_weighting"],
            planning["memory_strength_candidate_weighting"],
            "resolution must close, not reopen, the bounded plasticity window",
        )

    def test_recovery_remains_explicitly_present_in_planning_while_window_is_closed(self):
        frame, planning, context = self.recovery_context()
        self.assertTrue(context["affective_control_active"])
        self.assertEqual(context["machine_interoception"]["phase"], frame["phase"])
        self.assertEqual(context["machine_interoception"]["satiation"], frame["satiation"])
        self.assertGreater(context["experience_control_vector"]["satiation"], 0.0)
        self.assertGreater(context["experience_control_vector"]["resolution"], 0.0)
        self.assertGreaterEqual(context["experience_control_vector"]["refractory"], 0.0)
        self.assertLessEqual(
            context["memory_strength_candidate_weighting"],
            planning["memory_strength_candidate_weighting"],
        )


if __name__ == "__main__":
    unittest.main()
