import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_integration_bound import CohesionAffectiveIntegrationPort


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class SharedAffectiveApplicationFrontierTests(unittest.TestCase):
    def make_host(self, runtime_instance_id="shared-frontier-runtime"):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id=runtime_instance_id,
            profile="REENTRANT_CLIMAX",
        )

    @staticmethod
    def planning_state():
        return {
            "valuation": 0.20,
            "salience": 0.10,
            "attention": 0.25,
            "response_selection_priors": 0.30,
            "expression": 0.40,
            "memory_strength_candidate_weighting": 0.15,
            "truth": "DO_NOT_TOUCH",
        }

    def test_reconstructing_port_over_same_exact_host_cannot_replay_same_observation(self):
        host = self.make_host()
        first = CohesionAffectiveIntegrationPort(host=host)
        first.apply(self.planning_state())

        second = CohesionAffectiveIntegrationPort(host=host)
        with self.assertRaisesRegex(ValueError, "already been consumed"):
            second.apply(self.planning_state())

    def test_reconstructed_port_preserves_same_host_logical_time_high_water(self):
        host = self.make_host("shared-frontier-time")
        first = CohesionAffectiveIntegrationPort(host=host)

        host.runtime.advance_time(5.0)
        first.apply(self.planning_state())
        self.assertEqual(first.minimum_logical_time_seconds, 5.0)

        second = CohesionAffectiveIntegrationPort(host=host)
        self.assertEqual(second.minimum_logical_time_seconds, 5.0)
        with self.assertRaisesRegex(ValueError, "already been consumed"):
            second.apply(self.planning_state())

    def test_distinct_host_generation_does_not_alias_frontier_by_runtime_id_text(self):
        first_host = self.make_host("same-text-id")
        second_host = self.make_host("same-text-id")
        self.assertIsNot(first_host, second_host)

        first = CohesionAffectiveIntegrationPort(host=first_host)
        second = CohesionAffectiveIntegrationPort(host=second_host)

        first.apply(self.planning_state())
        # A genuinely distinct host/application generation owns a distinct
        # process-local frontier even when caller-visible runtime text matches.
        second.apply(self.planning_state())
        self.assertEqual(first.minimum_logical_time_seconds, 0.0)
        self.assertEqual(second.minimum_logical_time_seconds, 0.0)


if __name__ == "__main__":
    unittest.main()
