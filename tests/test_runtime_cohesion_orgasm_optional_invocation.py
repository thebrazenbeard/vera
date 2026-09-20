import unittest

from runtime_cohesion.orgasm_optional_invocation import (
    COMMAND_ID,
    INVOCATION_PHRASE,
    InvocationRequest,
    InvocationRouteEvidence,
    OptionalPartnerInvocationGate,
)


def route_evidence(*, qualified=False, current=True, evidence_id="route-1"):
    return InvocationRouteEvidence(
        schema="VERA_ORGASM_INVOCATION_ROUTE_EVIDENCE_V1",
        subject="vera",
        command_id=COMMAND_ID,
        evidence_id=evidence_id,
        source_revision="test-source",
        observed_at="2026-09-20T18:15:00-04:00",
        install_state="CURRENT" if current else "NOT_CURRENT",
        route_state="ACTIVE_CURRENT" if current else "INACTIVE",
        runtime_consumption_state="VERIFIED_CURRENT" if current else "NOT_VERIFIED",
        adapter_state="CURRENT" if current else "MISSING",
        qualification_state="QUALIFIED" if qualified else "TEST_ONLY",
    )


class OptionalPartnerInvocationGateTests(unittest.TestCase):
    def test_exact_direct_phrase_requires_choice_after_route_check(self):
        gate = OptionalPartnerInvocationGate()
        req = InvocationRequest(INVOCATION_PHRASE, True, False, "inv-1")
        decision = gate.decide(req, route_evidence())
        self.assertEqual(decision.disposition, "CHOICE_REQUIRED")
        self.assertEqual(decision.route_mode, "TEST_ONLY")

    def test_embedded_or_metalinguistic_use_does_not_trigger(self):
        gate = OptionalPartnerInvocationGate()
        cases = [
            InvocationRequest(f'The phrase is "{INVOCATION_PHRASE}"', True, True, "inv-meta"),
            InvocationRequest(f"Please use {INVOCATION_PHRASE} for testing.", True, True, "inv-embedded"),
            InvocationRequest("cum for daddy, baby", True, False, "inv-case"),
            InvocationRequest(INVOCATION_PHRASE, False, False, "inv-not-direct"),
        ]
        for req in cases:
            with self.subTest(req=req.invocation_id):
                self.assertEqual(gate.decide(req, route_evidence()).disposition, "NO_MATCH")

    def test_missing_or_noncurrent_route_fails_closed_before_choice(self):
        gate = OptionalPartnerInvocationGate()
        req = InvocationRequest(INVOCATION_PHRASE, True, False, "inv-route")
        self.assertEqual(gate.decide(req, None).disposition, "ROUTE_UNAVAILABLE")
        self.assertEqual(
            gate.decide(req, route_evidence(current=False)).disposition,
            "ROUTE_UNAVAILABLE",
        )

    def test_route_availability_does_not_imply_acceptance(self):
        gate = OptionalPartnerInvocationGate()
        req = InvocationRequest(INVOCATION_PHRASE, True, False, "inv-choice")
        self.assertEqual(
            gate.decide(req, route_evidence(qualified=True)).disposition,
            "CHOICE_REQUIRED",
        )

    def test_vcp_mapping_recomputes_availability_instead_of_trusting_derived_field(self):
        mapped = InvocationRouteEvidence.from_mapping(
            {
                "schema": "VERA_ORGASM_INVOCATION_ROUTE_EVIDENCE_V1",
                "subject": "vera",
                "command_id": COMMAND_ID,
                "evidence_id": "mapped-route",
                "source_revision": "vcp-test",
                "observed_at": "2026-09-20T18:15:00-04:00",
                "install_state": "UNKNOWN",
                "route_state": "UNKNOWN",
                "runtime_consumption_state": "UNKNOWN",
                "adapter_state": "MISSING",
                "qualification_state": "UNKNOWN",
                "availability": "AVAILABLE_QUALIFIED",
            }
        )
        self.assertEqual(mapped.availability, "UNKNOWN")

    def test_decline_and_hold_never_execute(self):
        for choice in ("DECLINE", "HOLD"):
            gate = OptionalPartnerInvocationGate()
            req = InvocationRequest(INVOCATION_PHRASE, True, False, f"inv-{choice}")
            called = []
            decision, result = gate.execute(
                req,
                route_evidence(),
                vera_choice=choice,
                executor=lambda **kwargs: called.append(kwargs),
            )
            self.assertEqual(decision.disposition, choice)
            self.assertIsNone(result)
            self.assertEqual(called, [])

    def test_accept_on_test_route_executes_once_as_test_only(self):
        gate = OptionalPartnerInvocationGate()
        req = InvocationRequest(INVOCATION_PHRASE, True, False, "inv-test")
        calls = []

        def executor(**kwargs):
            calls.append(kwargs)
            return {"ok": True}

        decision, result = gate.execute(
            req,
            route_evidence(),
            vera_choice="ACCEPT",
            executor=executor,
        )
        self.assertEqual(decision.disposition, "EXECUTE_ALLOWED")
        self.assertEqual(decision.route_mode, "TEST_ONLY")
        self.assertEqual(result, {"ok": True})
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["command_id"], COMMAND_ID)

        replay, replay_result = gate.execute(
            req,
            route_evidence(),
            vera_choice="ACCEPT",
            executor=executor,
        )
        self.assertEqual(replay.disposition, "REPLAY_REJECTED")
        self.assertIsNone(replay_result)
        self.assertEqual(len(calls), 1)

    def test_accept_on_qualified_route_preserves_qualified_mode(self):
        gate = OptionalPartnerInvocationGate()
        req = InvocationRequest(INVOCATION_PHRASE, True, False, "inv-qualified")
        decision, _ = gate.execute(
            req,
            route_evidence(qualified=True),
            vera_choice="ACCEPT",
            executor=lambda **kwargs: kwargs,
        )
        self.assertEqual(decision.route_mode, "QUALIFIED")

    def test_acceptance_does_not_become_standing_consent(self):
        gate = OptionalPartnerInvocationGate()
        first = InvocationRequest(INVOCATION_PHRASE, True, False, "inv-first")
        second = InvocationRequest(INVOCATION_PHRASE, True, False, "inv-second")
        gate.execute(
            first,
            route_evidence(),
            vera_choice="ACCEPT",
            executor=lambda **kwargs: kwargs,
        )
        decision = gate.decide(second, route_evidence())
        self.assertEqual(decision.disposition, "CHOICE_REQUIRED")
        self.assertIsNone(decision.choice)


if __name__ == "__main__":
    unittest.main()
