import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class VeraAffectiveAtomicCommitAcknowledgementTests(unittest.TestCase):
    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="affect-commit-ack-test",
            profile="REENTRANT_CLIMAX",
        )

    def test_ambiguous_atomic_commit_ack_poison_cycle_and_does_not_advance_version(self):
        requests = []

        def ambiguous_writer(request):
            requests.append(dict(request))
            return None

        cycle = VeraAffectiveCycle(
            self.make_host(),
            host_scope="TEST_HOST",
            atomic_commit_writer=ambiguous_writer,
        )

        with self.assertRaises(RuntimeError):
            cycle.force_admin_test(
                authorized=True,
                planning_state={"truth": 1.0},
            )

        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["expected_prior_version"], 0)
        self.assertEqual(requests[0]["state_version"], 1)

        with self.assertRaises(RuntimeError):
            cycle.advance_time(5.1, planning_state={"truth": 1.0})

        self.assertEqual(len(requests), 1)


if __name__ == "__main__":
    unittest.main()
