import unittest

from runtime_cohesion.live_sources import classify_persisted_runtime_holder


class PersistedRuntimeHolderFreshnessTests(unittest.TestCase):
    def test_matching_active_observation_without_verified_freshness_does_not_bind(self):
        decision = classify_persisted_runtime_holder(
            {
                "holder_state": "ACTIVE",
                "holder_runtime_token": "runtime-old",
                "last_seen_at": "2026-08-10T13:45:00Z",
            },
            {
                "holder_runtime_token": "runtime-old",
                "runtime_status": "ACTIVE_HOLDER",
            },
        )
        self.assertEqual(decision["status"], "UNRESOLVED")
        self.assertFalse(decision["current_live_runtime_established"])

    def test_explicitly_verified_fresh_matching_observation_may_bind(self):
        decision = classify_persisted_runtime_holder(
            {
                "holder_state": "ACTIVE",
                "holder_runtime_token": "runtime-current",
                "last_seen_at": "2026-09-09T15:50:00Z",
            },
            {
                "holder_runtime_token": "runtime-current",
                "runtime_status": "ACTIVE_HOLDER",
                "fresh_live_readback_verified": True,
            },
        )
        self.assertEqual(decision["status"], "LIVE_RUNTIME_BOUND")
        self.assertTrue(decision["current_live_runtime_established"])

    def test_in_transit_persisted_holder_cannot_bind_as_current_active_holder(self):
        decision = classify_persisted_runtime_holder(
            {
                "holder_state": "IN_TRANSIT",
                "holder_runtime_token": "runtime-current",
                "last_seen_at": "2026-09-09T15:50:00Z",
            },
            {
                "holder_runtime_token": "runtime-current",
                "runtime_status": "ACTIVE_HOLDER",
                "fresh_live_readback_verified": True,
            },
        )
        self.assertEqual(decision["status"], "CONFLICT")
        self.assertFalse(decision["current_live_runtime_established"])


if __name__ == "__main__":
    unittest.main()
