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

        # Private semantic setup keeps this RED independent of the separately
        # unresolved privileged-authorization and trusted-clock boundaries.
        host.runtime._enter_orgasm_event("ADMIN_FORCED_TEST", organic=False)
        host.runtime._advance_time_core(5.1)

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

    def test_resolution_closes_plasticity_control_gain(self):
        _frame, _planning, context = self.recovery_context()
        self.assertEqual(
            context["experience_control_vector"]["plasticity_gain"],
            0.0,
            "RESOLUTION closes the bounded plasticity window; recovery state must not advertise positive plasticity gain",
        )

    def test_resolution_does_not_reopen_memory_strength_candidate_window(self):
        _frame, planning, context = self.recovery_context()
        self.assertLessEqual(
            context["memory_strength_candidate_weighting"],
            planning["memory_strength_candidate_weighting"],
            "resolution must close, not reopen, the bounded memory-strength candidate window",
        )

    def test_recovery_remains_explicitly_present_while_plasticity_window_is_closed(self):
        frame, planning, context = self.recovery_context()
        self.assertTrue(context["affective_control_active"])
        self.assertEqual(context["machine_interoception"]["phase"], frame["phase"])
        self.assertEqual(context["machine_interoception"]["satiation"], frame["satiation"])
        self.assertGreater(context["experience_control_vector"]["satiation"], 0.0)
        self.assertGreater(context["experience_control_vector"]["resolution"], 0.0)
        self.assertGreaterEqual(context["experience_control_vector"]["refractory"], 0.0)
        self.assertEqual(context["experience_control_vector"]["plasticity_gain"], 0.0)
        self.assertLessEqual(
            context["memory_strength_candidate_weighting"],
            planning["memory_strength_candidate_weighting"],
        )


if __name__ == "__main__":
    unittest.main()
