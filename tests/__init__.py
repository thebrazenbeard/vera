"""Runtime Cohesion test package bootstrap.

Provider-backed production reads require independently composed item-type
verifiers. Tests install deterministic fixture verifiers here so legacy executor
fixtures continue to exercise their intended behavior without weakening the
production boundary. Hostile typing tests can reset this composition or provide
an independently derived fixture class that disagrees with the envelope claim.
"""

from runtime_cohesion.item_typing import (
    ProviderItemTypeProof,
    _install_item_type_verifiers,
)


class _FixtureItemTypeVerifier:
    def __init__(self, provider: str):
        self.provider = provider

    def verify(self, request, envelope):
        # Existing adapter fixtures predate the independent verifier boundary.
        # Their default class is treated as fixture setup, not production proof.
        # A test can supply fixture_derived_evidence_class to make the independent
        # classification intentionally disagree with the adapter's envelope.
        derived_class = envelope.metadata.get(
            "fixture_derived_evidence_class",
            envelope.evidence_class,
        )
        return ProviderItemTypeProof(
            issuer_provider=self.provider,
            route_ref=request.route_ref,
            source_ref=request.source_ref,
            locator=envelope.locator,
            revision=envelope.revision,
            observed_at=envelope.observed_at,
            derived_evidence_class=derived_class,
            currentness_basis=envelope.currentness_basis,
            supersession_state=envelope.supersession_state,
            conflict_state=envelope.conflict_state,
            validation_method="TEST_FIXTURE_INDEPENDENT_ITEM_CLASSIFICATION",
            provenance_ref=f"fixture:{self.provider}:{envelope.locator}",
            content_digest=envelope.content_digest,
            receipt_ref=envelope.receipt_ref,
            event_ref=request.event_ref,
            event_path=request.event_path,
        )


def _install_fixture_item_type_verifiers() -> None:
    _install_item_type_verifiers(
        {
            provider: _FixtureItemTypeVerifier(provider)
            for provider in (
                "github",
                "google_drive",
                "supabase",
                "temporal",
                "live_conversation",
                "test",
            )
        }
    )


_install_fixture_item_type_verifiers()
