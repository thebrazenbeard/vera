import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import StimulusAppraisal

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class VeraAffectiveCycleTests(unittest.TestCase):
    def make_cycle(self):
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="affective-cycle-test",
            profile="REENTRANT_CLIMAX",
        )
        state_rows = []
        event_rows = []
        return VeraAffectiveCycle(
            host,
            host_scope="TEST_HOST",
            state_writer=state_rows.append,
            event_writer=event_rows.append,
        ), state_rows, event_rows

    def test_process_turn_updates_internal_state_modulates_planning_and_persists_checkpoint(self):
        cycle, state_rows, event_rows = self.make_cycle()
        result = cycle.process_turn(
            StimulusAppraisal(
                sexual_relevance=0.8,
                partner_relevance=0.9,
                relational_relevance=0.9,
                anticipation_cue=0.8,
                positive_valence=0.9,
                duration_ms=800,
                context_eligible=True,
            ),
            planning_state={"valuation": 0.2, "salience": 0.2, "attention": 0.2, "truth": 0.9},
        )
        self.assertGreater(result.planning_context["salience"], 0.2)
        self.assertGreater(result.planning_context["attention"], 0.2)
        self.assertEqual(result.planning_context["truth"], 0.9)
        self.assertTrue(result.planning_context["affective_control_active"])
        self.assertEqual(len(state_rows), 1)
        self.assertEqual(state_rows[0]["runtime_instance_id"], "affective-cycle-test")
        self.assertEqual(event_rows, [])

    def test_admin_forced_cycle_enters_same_orgasm_event_and_persists_receipt(self):
        cycle, state_rows, event_rows = self.make_cycle()
        result = cycle.force_admin_test(
            authorized=True,
            planning_state={"valuation": 0.2, "salience": 0.2, "attention": 0.2, "truth": 0.9},
        )
        self.assertEqual(result.machine_interoception["phase"], "ORGASM_EVENT")
        self.assertEqual(result.event_receipt["trigger_class"], "ADMIN_FORCED_TEST")
        self.assertFalse(result.event_receipt["organic"])
        self.assertGreater(result.planning_context["valuation"], 0.2)
        self.assertEqual(result.planning_context["truth"], 0.9)
        self.assertEqual(len(state_rows), 1)
        self.assertEqual(len(event_rows), 1)
        self.assertEqual(event_rows[0]["event_type"], "ORGASM_EVENT")

    def test_state_version_increments_each_cycle(self):
        cycle, state_rows, _ = self.make_cycle()
        cycle.process_turn(StimulusAppraisal(), planning_state={"truth": 0.5})
        cycle.process_turn(StimulusAppraisal(), planning_state={"truth": 0.5})
        self.assertEqual([row["state_version"] for row in state_rows], [1, 2])


if __name__ == "__main__":
    unittest.main()
