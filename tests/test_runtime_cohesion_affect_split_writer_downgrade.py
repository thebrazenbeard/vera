import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import StimulusAppraisal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class AffectiveSplitWriterDowngradeTests(unittest.TestCase):
    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="vera-split-writer-review",
        )

    def assert_split_writer_rejected(self, **writers):
        with self.assertRaisesRegex(ValueError, r"(?i)(atomic|split|durab)"):
            VeraAffectiveCycle(
                self.make_host(),
                host_scope="TEST_HOST",
                **writers,
            )

    def test_state_writer_without_atomic_writer_is_not_a_silent_durable_mode(self):
        self.assert_split_writer_rejected(state_writer=lambda row: None)

    def test_event_writer_without_atomic_writer_is_not_a_silent_durable_mode(self):
        self.assert_split_writer_rejected(event_writer=lambda row: None)

    def test_split_state_and_event_writers_cannot_replace_atomic_commit_writer(self):
        self.assert_split_writer_rejected(
            state_writer=lambda row: None,
            event_writer=lambda row: None,
        )

    def test_arbitrary_atomic_writer_is_not_production_durable(self):
        with self.assertRaisesRegex(ValueError, r"(?i)(provider|writer|durab|test)"):
            VeraAffectiveCycle(
                self.make_host(),
                host_scope="TEST_HOST",
                atomic_commit_writer=lambda request: None,
            )

    def test_explicit_nonqualifying_atomic_test_mode_is_distinguishable(self):
        cycle = VeraAffectiveCycle(
            self.make_host(),
            host_scope="TEST_HOST",
            atomic_commit_writer=lambda request: {
                "state_version": request["state_version"],
                "checkpoint_sha256": request["checkpoint_sha256"],
                "event_count": len(request["event_rows"]),
            },
            non_qualifying_atomic_test_mode=True,
        )
        self.assertEqual(cycle.durability_mode, "NON_QUALIFYING_ATOMIC_TEST")

    def test_explicit_non_atomic_test_mode_is_distinguishable(self):
        cycle = VeraAffectiveCycle(
            self.make_host(),
            host_scope="TEST_HOST",
            state_writer=lambda row: None,
            non_atomic_test_mode=True,
        )
        self.assertTrue(cycle.non_atomic_test_mode)
        self.assertEqual(cycle.durability_mode, "NON_ATOMIC_TEST")

    def test_non_atomic_test_result_cannot_emit_provider_qualified_frontier_artifacts(self):
        cycle = VeraAffectiveCycle(
            self.make_host(),
            host_scope="TEST_HOST",
            state_writer=lambda row: None,
            non_atomic_test_mode=True,
        )
        result = cycle.process_turn(
            StimulusAppraisal(),
            planning_state={},
            elapsed_seconds=0.0,
        )

        self.assertFalse(result.atomic_commit_used)
        self.assertEqual(result.durability_mode, "NON_ATOMIC_TEST")
        self.assertEqual(result.state_row["lifecycle_status"], "HISTORICAL")
        self.assertIsNone(result.resume_token)
        self.assertIsNone(result.commit_request)

    def test_atomic_writer_cannot_be_mixed_with_split_callbacks(self):
        with self.assertRaisesRegex(ValueError, r"(?i)(atomic|split|durab)"):
            VeraAffectiveCycle(
                self.make_host(),
                host_scope="TEST_HOST",
                state_writer=lambda row: None,
                atomic_commit_writer=lambda request: None,
            )


if __name__ == "__main__":
    unittest.main()
