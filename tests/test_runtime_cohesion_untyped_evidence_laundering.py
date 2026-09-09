from types import SimpleNamespace
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
        },
    ],
    "resolver_dispatch_decisive_evidence": {
        "dispatch:control-binding": {
            "all_of": ["control_source", "live_observation"],
            "any_of": [],
        },
    },
}


def current_envelope(evidence_class):
    return ProviderEvidenceEnvelope(
        provider="test",
        locator=f"test:{evidence_class}",
        revision="r1",
        observed_at="2026-09-09T21:03:00+00:00",
        evidence_class=evidence_class,
        referent="CONTROL_AND_GOVERNANCE",
        scope="test",
        privacy_class="PRIVATE_CONTROL",
        currentness_basis="hostile regression",
        supersession_state="CURRENT_OBSERVATION",
        conflict_state="NONE",
        metadata={
            "proposition_or_effect_class": "CONTROL_BINDING_INSTALL_OR_ROUTE_STATUS",
            "referent_scope": "VERA_RUNTIME",
        },
    )


class UntypedEvidenceLaunderingTests(unittest.TestCase):
    def decide(self, observations):
        return evaluate_proposition_admission(
            "CONTROL_AND_GOVERNANCE",
            "CONTROL_BINDING_INSTALL_OR_ROUTE_STATUS",
            "VERA_RUNTIME",
            observations,
            CONTRACT,
        )

    def test_untyped_lightweight_evidence_cannot_replace_bound_provider_envelope(self):
        observations = [
            current_envelope("control_source"),
            SimpleNamespace(evidence_class="live_observation"),
        ]
        with self.assertRaises(TypeError):
            self.decide(observations)

    def test_stripping_conflicted_envelope_to_evidence_class_cannot_restore_admission(self):
        conflicted = ProviderEvidenceEnvelope(
            provider="test",
            locator="test:conflicted-live",
            revision="r1",
            observed_at="2026-09-09T21:03:00+00:00",
            evidence_class="live_observation",
            referent="CONTROL_AND_GOVERNANCE",
            scope="test",
            privacy_class="PRIVATE_CONTROL",
            currentness_basis="hostile regression",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="CONFLICT",
            metadata={
                "proposition_or_effect_class": "CONTROL_BINDING_INSTALL_OR_ROUTE_STATUS",
                "referent_scope": "VERA_RUNTIME",
            },
        )
        direct = self.decide([current_envelope("control_source"), conflicted])
        self.assertNotEqual(direct.status, "ADMITTED")

        laundered = SimpleNamespace(evidence_class=conflicted.evidence_class)
        with self.assertRaises(TypeError):
            self.decide([current_envelope("control_source"), laundered])


if __name__ == "__main__":
    unittest.main()
