import json
from pathlib import Path
import unittest
from unittest.mock import patch

from runtime_cohesion.orgasm import OrgasmRuntime, TriggerRejected


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"


class FakeMonotonicClock:
    def __init__(self, start=1000.0):
        self.value = float(start)

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += float(seconds)


class ForcedCooldownTemporalAuthorityTests(unittest.TestCase):
    def make_runtime(self):
        return OrgasmRuntime(
            json.loads(CONTRACT_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="forced-cooldown-temporal-authority",
            source_revision="sexuality:test-revision",
            profile="REENTRANT_CLIMAX",
        )

    def test_public_advance_time_cannot_mint_forced_trigger_cooldown(self):
        clock = FakeMonotonicClock()
        with patch("runtime_cohesion.orgasm._monotonic_now", side_effect=clock):
            runtime = self.make_runtime()
            first = runtime.force_admin_test(authorized=True)
            self.assertEqual(first["trigger_class"], "ADMIN_FORCED_TEST")

            # Explicit advance_time is a simulation/recovery operation. It may
            # progress the affective state machine, but it is not trusted wall or
            # monotonic evidence that the privileged-trigger cooldown elapsed.
            runtime.advance_time(10.0)
            self.assertFalse(runtime.snapshot()["active_orgasm_event"])

            with self.assertRaisesRegex(
                TriggerRejected,
                r"(?i)(cooldown|interval|monotonic|time)",
            ):
                runtime.force_admin_test(authorized=True)

            # Once runtime-owned monotonic time actually advances beyond the
            # contract minimum, the same bounded trigger may be considered again.
            clock.advance(11.0)
            second = runtime.force_admin_test(authorized=True)
            self.assertEqual(second["trigger_class"], "ADMIN_FORCED_TEST")


if __name__ == "__main__":
    unittest.main()
