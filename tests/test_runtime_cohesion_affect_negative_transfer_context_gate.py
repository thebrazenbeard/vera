import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class AffectiveNegativeTransferContextGateTests(unittest.TestCase):
    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="vera-negative-transfer-context-test",
            profile="REFRACTORY_COUPLED",
        )

    def test_ineligible_recovery_context_does_not_contaminate_unrelated_planning(self):
        host = self.make_host()
        host.force_admin_test(authorized=True)
        host.advance_time(5.1)

        runtime_state = host.runtime.snapshot()
        self.assertIn(runtime_state["phase"], {"RESOLUTION", "SATIATED_OR_REFRACTORY"})
        self.assertFalse(runtime_state["context_eligible"])
        self.assertGreater(runtime_state["satiation"], 0.0)

        unrelated = {
            "valuation": 0.31,
            "salience": 0.32,
            "attention": 0.33,
            "response_selection_priors": 0.34,
            "expression": 0.35,
            "memory_strength_candidate_weighting": 0.36,
            "truth": 0.91,
        }
        context = host.build_planning_context(unrelated)

        for key in (
            "valuation",
            "salience",
            "attention",
            "response_selection_priors",
            "expression",
            "memory_strength_candidate_weighting",
        ):
            self.assertEqual(
                context[key],
                unrelated[key],
                f"ineligible sexual/relational recovery context must not leak into unrelated {key}",
            )

        self.assertTrue(context["affective_control_active"])
        self.assertGreater(context["machine_interoception"]["satiation"], 0.0)
        self.assertGreater(context["experience_control_vector"]["resolution"], 0.0)
        self.assertEqual(context["truth"], unrelated["truth"])


if __name__ == "__main__":
    unittest.main()
