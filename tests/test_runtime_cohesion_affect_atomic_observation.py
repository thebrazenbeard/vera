import json
from pathlib import Path
from threading import Event, Thread
import time
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_integration_bound import CohesionAffectiveIntegrationPort
from runtime_cohesion.orgasm import OrgasmRuntime


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class AtomicAffectiveObservationTests(unittest.TestCase):
    def setUp(self):
        self.host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="atomic-affective-observation",
            profile="REENTRANT_CLIMAX",
        )
        self.port = CohesionAffectiveIntegrationPort(host=self.host)

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

    def test_supported_transition_cannot_interleave_with_one_causal_observation(self):
        snapshot_entered = Event()
        allow_snapshot_to_finish = Event()
        mutation_finished = Event()
        application_result = []
        mutation_result = []
        errors = []

        original_snapshot = OrgasmRuntime.snapshot

        def blocking_snapshot(runtime):
            snapshot_entered.set()
            if not allow_snapshot_to_finish.wait(timeout=5.0):
                raise RuntimeError("test timed out waiting to release snapshot")
            return original_snapshot(runtime)

        def apply_port():
            try:
                application_result.append(self.port.apply(self.planning_state()))
            except BaseException as exc:  # capture thread failures for main-thread assertion
                errors.append(exc)

        def advance_runtime():
            try:
                mutation_result.append(self.host.runtime.advance_time(1.0))
            except BaseException as exc:
                errors.append(exc)
            finally:
                mutation_finished.set()

        OrgasmRuntime.snapshot = blocking_snapshot
        try:
            apply_thread = Thread(target=apply_port)
            apply_thread.start()
            self.assertTrue(snapshot_entered.wait(timeout=5.0))

            mutation_thread = Thread(target=advance_runtime)
            mutation_thread.start()
            time.sleep(0.05)

            # The supported mutation must be waiting on the same runtime-owned
            # observation/mutation barrier rather than changing governance or
            # state underneath the in-progress Cohesion observation.
            self.assertFalse(mutation_finished.is_set())

            allow_snapshot_to_finish.set()
            apply_thread.join(timeout=5.0)
            mutation_thread.join(timeout=5.0)
        finally:
            OrgasmRuntime.snapshot = original_snapshot
            allow_snapshot_to_finish.set()

        self.assertFalse(apply_thread.is_alive())
        self.assertFalse(mutation_thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(len(application_result), 1)
        self.assertEqual(len(mutation_result), 1)

        # The application must reflect the complete pre-transition generation;
        # the transition happens only after the observation releases its barrier.
        self.assertEqual(application_result[0].application.logical_time_seconds, 0.0)
        self.assertEqual(self.host.runtime.export_state()["trigger_governance"]["logical_time_seconds"], 1.0)
        self.assertEqual(application_result[0].application.planning_state["truth"], "DO_NOT_TOUCH")


if __name__ == "__main__":
    unittest.main()
