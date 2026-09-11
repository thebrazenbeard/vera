import json
from pathlib import Path
from threading import Event, Thread
import time
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_integration_bound import CohesionAffectiveIntegrationPort
from runtime_cohesion.orgasm import OrgasmRuntime, TriggerRejected


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
            except BaseException as exc:
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
        self.assertEqual(application_result[0].application.logical_time_seconds, 0.0)
        self.assertEqual(self.host.runtime.export_state()["trigger_governance"]["logical_time_seconds"], 1.0)
        self.assertEqual(application_result[0].application.planning_state["truth"], "DO_NOT_TOUCH")

    def test_generic_planning_mutation_is_cohesion_only(self):
        planning = self.planning_state()
        with self.assertRaisesRegex(TriggerRejected, "Cohesion"):
            self.host.runtime.modulate_planning(planning)
        with self.assertRaisesRegex(TriggerRejected, "Cohesion"):
            self.host.build_planning_context(planning)
        self.assertEqual(planning, self.planning_state())

    def test_cycle_mutation_and_evidence_capture_are_one_generation(self):
        cycle = VeraAffectiveCycle(self.host, host_scope="ATOMIC_CYCLE_TEST")
        capture_entered = Event()
        allow_capture_to_finish = Event()
        mutation_finished = Event()
        cycle_results = []
        errors = []

        original_capture = VeraAffectiveRuntimeHost._capture_cycle_observation

        def blocking_capture(host):
            observation = original_capture(host)
            capture_entered.set()
            if not allow_capture_to_finish.wait(timeout=5.0):
                raise RuntimeError("test timed out waiting to release cycle capture")
            return observation

        def run_cycle():
            try:
                cycle_results.append(cycle.advance_time(1.0, planning_state=self.planning_state()))
            except BaseException as exc:
                errors.append(exc)

        def mutate_after_capture():
            try:
                self.host.advance_time(1.0)
            except BaseException as exc:
                errors.append(exc)
            finally:
                mutation_finished.set()

        VeraAffectiveRuntimeHost._capture_cycle_observation = blocking_capture
        try:
            cycle_thread = Thread(target=run_cycle)
            cycle_thread.start()
            self.assertTrue(capture_entered.wait(timeout=5.0))

            mutation_thread = Thread(target=mutate_after_capture)
            mutation_thread.start()
            time.sleep(0.05)
            self.assertFalse(mutation_finished.is_set())

            allow_capture_to_finish.set()
            cycle_thread.join(timeout=5.0)
            mutation_thread.join(timeout=5.0)
        finally:
            VeraAffectiveRuntimeHost._capture_cycle_observation = original_capture
            allow_capture_to_finish.set()

        self.assertFalse(cycle_thread.is_alive())
        self.assertFalse(mutation_thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(len(cycle_results), 1)

        result = cycle_results[0]
        checkpoint_time = result.checkpoint["runtime_state"]["trigger_governance"]["logical_time_seconds"]
        signal_time = result.affective_modulation_signal["temporal_scope"]["logical_time_seconds"]
        self.assertEqual(checkpoint_time, 1.0)
        self.assertEqual(signal_time, checkpoint_time)
        self.assertEqual(result.machine_interoception, result.checkpoint["machine_interoception"])
        self.assertEqual(self.host.runtime.export_state()["trigger_governance"]["logical_time_seconds"], 2.0)


if __name__ == "__main__":
    unittest.main()
