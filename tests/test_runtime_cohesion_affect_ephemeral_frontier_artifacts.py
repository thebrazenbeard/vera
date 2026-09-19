import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import StimulusAppraisal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class AffectiveEphemeralFrontierArtifactTests(unittest.TestCase):
    def make_host(self, runtime_instance_id):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id=runtime_instance_id,
        )

    def test_ephemeral_result_cannot_emit_provider_qualified_frontier_artifacts(self):
        cycle = VeraAffectiveCycle(
            self.make_host("ephemeral-frontier-artifact-test"),
            host_scope="TEST_HOST",
        )
        result = cycle.process_turn(
            StimulusAppraisal(),
            planning_state={},
            elapsed_seconds=0.0,
        )

        self.assertFalse(result.atomic_commit_used)
        self.assertEqual(result.durability_mode, "EPHEMERAL")
        self.assertEqual(result.state_row["lifecycle_status"], "HISTORICAL")
        self.assertIsNone(result.commit_request)
        self.assertIsNone(result.resume_token)

    def test_explicit_atomic_test_result_cannot_emit_production_frontier_artifacts(self):
        captured = []

        def writer(request):
            captured.append(dict(request))
            return {
                "state_version": request["state_version"],
                "checkpoint_sha256": request["checkpoint_sha256"],
                "event_count": len(request["event_rows"]),
            }

        cycle = VeraAffectiveCycle(
            self.make_host("atomic-frontier-artifact-control"),
            host_scope="TEST_HOST",
            atomic_commit_writer=writer,
            non_qualifying_atomic_test_mode=True,
        )
        result = cycle.process_turn(
            StimulusAppraisal(),
            planning_state={},
            elapsed_seconds=0.0,
        )

        self.assertTrue(result.atomic_commit_used)
        self.assertEqual(result.durability_mode, "NON_QUALIFYING_ATOMIC_TEST")
        self.assertEqual(result.state_row["lifecycle_status"], "HISTORICAL")
        self.assertEqual(result.commit_request["schema"], "VERA_AFFECTIVE_RUNTIME_ATOMIC_COMMIT_TEST_V1")
        self.assertIsNone(result.resume_token)
        self.assertEqual(len(captured), 1)


if __name__ == "__main__":
    unittest.main()
