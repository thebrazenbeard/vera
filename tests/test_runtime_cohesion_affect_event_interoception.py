import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class VeraAffectiveEventInteroceptionTests(unittest.TestCase):
    def make_cycle(self):
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="affect-event-interoception-test",
            profile="REENTRANT_CLIMAX",
        )
        return VeraAffectiveCycle(host, host_scope="TEST_HOST")

    def test_each_multi_receipt_event_row_carries_interoception_for_its_own_state_after(self):
        cycle = self.make_cycle()
        cycle.force_admin_test(authorized=True, planning_state={"truth": 1.0})
        result = cycle.advance_time(5.1, planning_state={"truth": 1.0})

        self.assertGreaterEqual(len(result.event_rows), 2)
        self.assertEqual(
            [row["event_type"] for row in result.event_rows[:2]],
            ["RESOLUTION", "RECOVERY"],
        )

        for row in result.event_rows:
            state_after = row["state_after"]
            frame = row["machine_interoception"]
            self.assertEqual(frame["phase"], state_after["phase"])
            self.assertEqual(frame["active_orgasm_event"], state_after["active_orgasm_event"])
            self.assertEqual(frame["activation_intensity"], state_after["activation_intensity"])
            self.assertEqual(frame["coherence"], state_after["coherence"])
            self.assertEqual(frame["hedonic_impact"], state_after["hedonic_impact"])
            self.assertEqual(frame["consummatory_gain"], state_after["consummatory_gain"])
            self.assertEqual(frame["satiation"], state_after["satiation"])
            self.assertEqual(frame["resolution_intensity"], state_after["resolution_intensity"])
            self.assertEqual(frame["refractory_strength"], state_after["refractory_strength"])
            self.assertEqual(frame["last_event_digest"], row["event_digest"])
            self.assertEqual(frame["last_trigger_class"], row["trigger_class"])
            self.assertEqual(frame["phenomenology"], "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
