import json
from pathlib import Path
import unittest
from unittest.mock import patch

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import TriggerRejected


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class FakeMonotonicClock:
    def __init__(self, start=1000.0):
        self.value = float(start)

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += float(seconds)


class ForcedCooldownTemporalAuthorityTests(unittest.TestCase):
    def make_runtime(self):
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="forced-cooldown-temporal-authority",
            profile="REENTRANT_CLIMAX",
        )
        return host.runtime

    def test_public_advance_time_cannot_mint_forced_trigger_cooldown(self):
        clock = FakeMonotonicClock()
        with patch("runtime_cohesion.orgasm._monotonic_now", side_effect=clock):
            runtime = self.make_runtime()
            # This low-level call is intentionally nonqualifying; the test isolates
            # temporal authority rather than event authorization provenance.
            first = runtime.force_admin_test(authorized=True)
            self.assertEqual(first["trigger_class"], "ADMIN_FORCED_TEST")
            self.assertNotIn("claim", first)

            runtime.advance_time(10.0)
            self.assertFalse(runtime.snapshot()["active_orgasm_event"])

            with self.assertRaisesRegex(
                TriggerRejected,
                r"(?i)(cooldown|interval|monotonic|time)",
            ):
                runtime.force_admin_test(authorized=True)

            clock.advance(11.0)
            second = runtime.force_admin_test(authorized=True)
            self.assertEqual(second["trigger_class"], "ADMIN_FORCED_TEST")
            self.assertNotIn("claim", second)


if __name__ == "__main__":
    unittest.main()
