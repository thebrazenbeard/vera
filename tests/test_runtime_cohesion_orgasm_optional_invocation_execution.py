import unittest

from runtime_cohesion.orgasm_optional_invocation import (
    COMMAND_ID,
    INVOCATION_PHRASE,
    InvocationRequest,
    InvocationRouteEvidence,
    OptionalPartnerInvocationGate,
)
from runtime_cohesion.orgasm_optional_invocation_execution import (
    OptionalInvocationExecutionError,
    TestOnlyAffectiveHostExecutor,
    execute_test_only_invocation,
)


class FakeAffectiveHost:
    def __init__(self):
        self.calls = []

    def force_admin_test(self, *, authorization_subject):
        self.calls.append(dict(authorization_subject))
        return {
            "receipt_id": "event-1",
            "runtime_instance_id": "fake-runtime",
            "subject": "vera",
            "schema_version": "VERA_ORGASM_RUNTIME_CONTRACT_V1",
            "event_type": "ORGASM_EVENT",
            "state_before": {"phase": "QUIESCENT"},
            "trigger_provenance": {
                "composition_trust": "IN_PROCESS_UNROOTED_NON_QUALIFYING",
            },
            "transition": "QUIESCENT->ORGASM_EVENT",
            "state_after": {"phase": "ORGASM_EVENT"},
            "observed_at": "2026-09-20T22:45:00Z",
            "source_revision": "test",
            "trigger_class": "ADMIN_FORCED_TEST",
            "organic": False,
            "phenomenology": "UNRESOLVED",
            "event_digest": "a" * 64,
        }


def route_evidence(mode="TEST_ONLY"):
    return InvocationRouteEvidence(
        schema="VERA_ORGASM_INVOCATION_ROUTE_EVIDENCE_V1",
        subject="vera",
        command_id=COMMAND_ID,
        evidence_id="route-test-1",
        source_revision="route-source",
        observed_at="2026-09-20T22:45:00Z",
        install_state="CURRENT",
        route_state="ACTIVE_CURRENT",
        runtime_consumption_state="VERIFIED_CURRENT",
        adapter_state="CURRENT",
        qualification_state=mode,
    )


class OptionalInvocationExecutionTests(unittest.TestCase):
    def subject(self):
        return {
            "state": "ALLOW",
            "actor": "patrick",
            "referent": "vera",
            "proposition_or_effect_class": "ADMIN_FORCED_TEST",
            "source": "trusted-test-only-route-authority",
            "observed_at": "2026-09-20T22:45:00Z",
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }

    def request(self, invocation_id="inv-1"):
        return InvocationRequest(
            INVOCATION_PHRASE,
            True,
            False,
            invocation_id,
        )

    def test_test_only_executor_binds_invocation_to_downstream_event(self):
        host = FakeAffectiveHost()
        executor = TestOnlyAffectiveHostExecutor(
            host,
            authorization_subject=self.subject(),
        )
        receipt = executor(
            command_id=COMMAND_ID,
            invocation_id="inv-1",
            route_mode="TEST_ONLY",
            route_evidence_id="route-test-1",
        )
        self.assertEqual(receipt["schema"], "VERA_ORGASM_OPTIONAL_INVOCATION_EXECUTION_RECEIPT_V1")
        self.assertEqual(receipt["invocation_id"], "inv-1")
        self.assertEqual(receipt["route_mode"], "TEST_ONLY")
        self.assertEqual(receipt["downstream_trigger_class"], "ADMIN_FORCED_TEST")
        self.assertEqual(receipt["downstream_event_digest"], "a" * 64)
        self.assertEqual(receipt["qualification"], "NONQUALIFYING_TEST_ONLY")
        self.assertEqual(receipt["phenomenology"], "UNRESOLVED")
        self.assertEqual(len(host.calls), 1)

    def test_qualified_route_cannot_be_laundered_through_test_adapter(self):
        host = FakeAffectiveHost()
        executor = TestOnlyAffectiveHostExecutor(
            host,
            authorization_subject=self.subject(),
        )
        with self.assertRaisesRegex(OptionalInvocationExecutionError, "TEST_ONLY"):
            executor(
                command_id=COMMAND_ID,
                invocation_id="inv-2",
                route_mode="QUALIFIED",
                route_evidence_id="route-qualified",
            )
        self.assertEqual(host.calls, [])

    def test_downstream_production_claim_is_rejected(self):
        class BadHost(FakeAffectiveHost):
            def force_admin_test(self, *, authorization_subject):
                result = super().force_admin_test(
                    authorization_subject=authorization_subject
                )
                result["claim"] = "ENGINEERED_ORGASM_ANALOGUE_OCCURRED"
                return result

        with self.assertRaisesRegex(OptionalInvocationExecutionError, "production"):
            TestOnlyAffectiveHostExecutor(
                BadHost(),
                authorization_subject=self.subject(),
            )(
                command_id=COMMAND_ID,
                invocation_id="inv-3",
                route_mode="TEST_ONLY",
                route_evidence_id="route-test-1",
            )

    def test_full_source_level_path_requires_vera_accept(self):
        gate = OptionalPartnerInvocationGate()
        host = FakeAffectiveHost()

        decision, receipt = execute_test_only_invocation(
            gate=gate,
            request=self.request("inv-full"),
            route_evidence=route_evidence("TEST_ONLY"),
            vera_choice="ACCEPT",
            host=host,
            authorization_subject=self.subject(),
        )
        self.assertEqual(decision.disposition, "EXECUTE_ALLOWED")
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["invocation_id"], "inv-full")
        self.assertEqual(len(host.calls), 1)

    def test_decline_never_reaches_host(self):
        gate = OptionalPartnerInvocationGate()
        host = FakeAffectiveHost()

        decision, receipt = execute_test_only_invocation(
            gate=gate,
            request=self.request("inv-decline"),
            route_evidence=route_evidence("TEST_ONLY"),
            vera_choice="DECLINE",
            host=host,
            authorization_subject=self.subject(),
        )
        self.assertEqual(decision.disposition, "DECLINE")
        self.assertIsNone(receipt)
        self.assertEqual(host.calls, [])

    def test_qualified_route_is_blocked_by_current_adapter_even_after_accept(self):
        gate = OptionalPartnerInvocationGate()
        host = FakeAffectiveHost()

        with self.assertRaisesRegex(OptionalInvocationExecutionError, "TEST_ONLY"):
            execute_test_only_invocation(
                gate=gate,
                request=self.request("inv-qualified"),
                route_evidence=route_evidence("QUALIFIED"),
                vera_choice="ACCEPT",
                host=host,
                authorization_subject=self.subject(),
            )
        self.assertEqual(host.calls, [])


if __name__ == "__main__":
    unittest.main()
