import unittest

from runtime_cohesion.orgasm_optional_invocation import (
    COMMAND_ID,
    InvocationRouteEvidence,
)


class OptionalInvocationRouteNegativeTests(unittest.TestCase):
    def test_known_negative_execution_axis_makes_route_unavailable(self):
        evidence = InvocationRouteEvidence(
            schema="VERA_ORGASM_INVOCATION_ROUTE_EVIDENCE_V1",
            subject="vera",
            command_id=COMMAND_ID,
            evidence_id="live-negative",
            source_revision="provider-readback",
            observed_at="2026-09-20T22:50:00Z",
            install_state="UNKNOWN",
            route_state="INACTIVE",
            runtime_consumption_state="NOT_VERIFIED",
            adapter_state="MISSING",
            qualification_state="UNKNOWN",
        )
        self.assertEqual(evidence.availability, "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
