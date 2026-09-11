import unittest

from runtime_cohesion.evidence import ProviderEvidenceEnvelope
from runtime_cohesion.runtime import evaluate_proposition_admission


CONTRACT = {
    "authority_resolvers": {
        "control_governance": {
            "accepted_evidence_classes": ["control_source", "live_observation"],
        },
    },
    "resolver_dispatch": [
        {
            "id": "dispatch:control-binding",
            "domain_scope": "CONTROL_AND_GOVERNANCE",
            "proposition_or_effect_class": "CONTROL_BINDING_INSTALL_OR_ROUTE_STATUS",
            "referent_scope": "VERA_RUNTIME",
            "resolver_ref": "control_governance",
            "precedence": 105,
            "conflict_disposition": "EXACT_R10_BINDING_AND_CURRENTNESS_REQUIRED",
        },
    ],
    "resolver_dispatch_decisive_evidence": {
        "dispatch:control-binding": {
            "all_of": ["control_source", "live_observation"],
            "any_of": [],
        },
    },
}


def envelope(evidence_class, *, supersession_state="CURRENT_OBSERVATION", conflict_state="NONE", proposition="CONTROL_BINDING_INSTALL_OR_ROUTE_STATUS", referent_scope="VERA_RUNTIME"):
    return ProviderEvidenceEnvelope(
        provider="test",
        locator=f"test:{evidence_class}",
        revision="r1",
        observed_at="2026-09-09T20:38:00+00:00",
        evidence_class=evidence_class,
        referent="CONTROL_AND_GOVERNANCE",
        scope="test",
        privacy_class="PRIVATE_CONTROL",
        currentness_basis="test fixture",
        supersession_state=supersession_state,
        conflict_state=conflict_state,
        metadata={
            "proposition_or_effect_class": proposition,
            "referent_scope": referent_scope,
        },
    )


class AdmissionEnvelopeBindingTests(unittest.TestCase):
    def decide(self, observations):
        return evaluate_proposition_admission(
            "CONTROL_AND_GOVERNANCE",
            "CONTROL_BINDING_INSTALL_OR_ROUTE_STATUS",
            "VERA_RUNTIME",
            observations,
            CONTRACT,
        )

    def test_exact_current_bound_envelopes_can_admit(self):
        decision = self.decide([envelope("control_source"), envelope("live_observation")])
        self.assertEqual(decision.status, "ADMITTED")

    def test_conflicted_decisive_envelope_cannot_admit(self):
        decision = self.decide([
            envelope("control_source"),
            envelope("live_observation", conflict_state="CONFLICT"),
        ])
        self.assertNotEqual(decision.status, "ADMITTED")

    def test_superseded_decisive_envelope_cannot_admit(self):
        decision = self.decide([
            envelope("control_source"),
            envelope("live_observation", supersession_state="SUPERSEDED"),
        ])
        self.assertNotEqual(decision.status, "ADMITTED")

    def test_wrong_proposition_binding_cannot_admit(self):
        decision = self.decide([
            envelope("control_source"),
            envelope("live_observation", proposition="SOME_OTHER_PROPOSITION"),
        ])
        self.assertNotEqual(decision.status, "ADMITTED")

    def test_wrong_referent_scope_binding_cannot_admit(self):
        decision = self.decide([
            envelope("control_source"),
            envelope("live_observation", referent_scope="SOME_OTHER_SCOPE"),
        ])
        self.assertNotEqual(decision.status, "ADMITTED")


if __name__ == "__main__":
    unittest.main()
