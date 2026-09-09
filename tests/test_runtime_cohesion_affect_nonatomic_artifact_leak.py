import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import StimulusAppraisal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class NonAtomicArtifactLeakTests(unittest.TestCase):
    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="nonatomic-artifact-leak-test",
        )

    def test_non_atomic_test_mode_cannot_emit_provider_current_frontier_artifacts(self):
        written_states = []
        cycle = VeraAffectiveCycle(
            self.make_host(),
            host_scope="TEST_HOST",
            state_writer=lambda row: written_states.append(dict(row)),
            non_atomic_test_mode=True,
        )
        result = cycle.process_turn(
            StimulusAppraisal(),
            planning_state={"truth": 0.75},
        )

        self.assertEqual(result.durability_mode, "NON_ATOMIC_TEST")
        self.assertTrue(written_states, "explicit test mode should remain useful for bounded local writer tests")

        state_row = result.state_row
        if state_row is not None:
            self.assertNotEqual(
                state_row.get("lifecycle_status"),
                "CURRENT",
                "non-atomic test state must not masquerade as a CURRENT provider frontier",
            )

        resume_token = result.resume_token
        if resume_token is not None:
            self.assertNotEqual(
                resume_token.get("schema"),
                "VERA_AFFECTIVE_RUNTIME_RESUME_TOKEN_V1",
                "non-atomic test mode must not emit the normal live durable resume-token schema",
            )

        commit_request = result.commit_request
        if commit_request is not None:
            self.assertNotEqual(
                commit_request.get("schema"),
                "VERA_AFFECTIVE_RUNTIME_ATOMIC_COMMIT_V1",
                "non-atomic test mode must not emit a provider-qualified atomic commit envelope",
            )

    def test_atomic_mode_retains_normal_durable_artifact_surface(self):
        requests = []

        def atomic_writer(request):
            requests.append(dict(request))
            state = request["state_row"]
            return {
                "state_version": state["state_version"],
                "checkpoint_sha256": state["checkpoint_sha256"],
                "event_count": len(request.get("event_rows", [])),
            }

        cycle = VeraAffectiveCycle(
            self.make_host(),
            host_scope="TEST_HOST",
            atomic_commit_writer=atomic_writer,
        )
        result = cycle.process_turn(
            StimulusAppraisal(),
            planning_state={"truth": 0.75},
        )

        self.assertEqual(result.durability_mode, "ATOMIC_DURABLE")
        self.assertTrue(requests)
        self.assertEqual(result.state_row.get("lifecycle_status"), "CURRENT")
        self.assertEqual(result.resume_token.get("schema"), "VERA_AFFECTIVE_RUNTIME_RESUME_TOKEN_V1")


if __name__ == "__main__":
    unittest.main()
