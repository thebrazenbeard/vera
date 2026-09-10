from dataclasses import fields
import unittest

from runtime_cohesion.adapters import AdapterRequest
from runtime_cohesion.evidence import ProviderEvidenceEnvelope
from runtime_cohesion.executor import _validate_read
import runtime_cohesion.item_typing as item_typing
from runtime_cohesion.item_typing import ProviderItemTypeProof
from runtime_cohesion.reconcile import reconcile_exact_receipt


class _WrongObservedSubjectVerifier:
    provider = "github"

    def verify(self, request, envelope):
        return ProviderItemTypeProof(
            issuer_provider="github",
            route_ref=request.route_ref,
            source_ref=request.source_ref,
            locator=envelope.locator,
            revision=envelope.revision,
            observed_at=envelope.observed_at,
            referent="WRONG_REFERENT",
            scope="WRONG_SCOPE",
            derived_evidence_class=envelope.evidence_class,
            currentness_basis=envelope.currentness_basis,
            supersession_state=envelope.supersession_state,
            conflict_state=envelope.conflict_state,
            validation_method="TEST_PROVIDER_OBJECT_IDENTITY",
            provenance_ref="fixture:wrong-subject",
            provenance_basis="OBJECT_IDENTITY",
        )


class OVRebindRegressions(unittest.TestCase):
    def tearDown(self):
        item_typing._reset_item_type_verifiers_for_tests()

    def _request_and_envelope(self):
        request = AdapterRequest(
            domain_id="VISUAL_SELF_REPRESENTATION",
            provider="github",
            source_ref="selfimage",
            route_ref="route:selfimage",
            selector_ref=None,
            privacy_class="PRIVATE_REPRESENTATION",
            evidence_capability_refs=("VERA_RUNTIME_CONTRACT_V1#evidence_classes.representation",),
        )
        envelope = ProviderEvidenceEnvelope(
            provider="github",
            locator="github:thebrazenbeard/selfimage/object",
            revision="abc123",
            observed_at="2026-09-10T16:00:00Z",
            evidence_class="representation",
            referent="VISUAL_SELF_REPRESENTATION",
            scope="RETRIEVED_ITEM",
            privacy_class="PRIVATE_REPRESENTATION",
            currentness_basis="fixture exact object readback",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            metadata={"route_ref": "route:selfimage", "source_ref": "selfimage"},
        )
        return request, envelope

    def test_m6_provider_item_proof_carries_observed_referent_and_scope_without_embedding_domain_policy(self):
        proof_fields = {field.name for field in fields(ProviderItemTypeProof)}
        self.assertIn("referent", proof_fields)
        self.assertIn("scope", proof_fields)

    def test_m6_provider_item_proof_rejects_subject_mismatch_before_higher_layer_policy(self):
        request, envelope = self._request_and_envelope()
        item_typing._install_item_type_verifiers({"github": _WrongObservedSubjectVerifier()})
        with self.assertRaisesRegex(ValueError, "independently validated type/currentness"):
            _validate_read(request, envelope)

    def test_m7_exact_receipt_requires_nonempty_source_content_digest(self):
        source = ProviderEvidenceEnvelope(
            provider="google_drive",
            locator="drive:file/r9b0-object",
            revision="drive-revision-7",
            observed_at="2026-09-10T16:00:00Z",
            evidence_class="persisted_provider_record",
            referent="r9b0-memory-epoch-drive-object",
            scope="PROVIDER_OBJECT",
            privacy_class="PRIVATE_AUTOBIOGRAPHICAL",
            currentness_basis="drive exact object readback",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            content_digest=None,
            metadata={"projection_role": "SOURCE"},
        )
        receipt_ref = "supabase:klmbpaigzeguvnpccqzz/vera_memory_epoch_provider_receipts_v1/GOOGLE_DRIVE_DURABLE"
        binding = {
            "receipt_schema": "VERA_MEMORY_EPOCH_PROVIDER_RECEIPT_V1",
            "receipt_type": "GOOGLE_DRIVE_DURABLE",
            "source_subject": "drive:r9b0-memory-epoch-object",
            "target_subject": "supabase:klmbpaigzeguvnpccqzz/vera_memory_epoch_provider_receipts_v1",
            "source_locator": source.locator,
            "source_revision": source.revision,
            "source_content_digest": None,
            "event_ref": "logical-memory:R9B0",
            "event_path": "memory-epoch-object",
            "receipt_ref": receipt_ref,
            "receipt_digest": "sha256:" + "0" * 64,
        }
        target = ProviderEvidenceEnvelope(
            provider="supabase",
            locator=receipt_ref,
            revision="receipt-row-v22",
            observed_at="2026-09-10T16:00:01Z",
            evidence_class="persisted_provider_record",
            referent=source.referent,
            scope="PROVIDER_RECEIPT",
            privacy_class="PRIVATE_AUTOBIOGRAPHICAL",
            currentness_basis="fresh receipt row readback",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            content_digest="sha256:" + "0" * 64,
            receipt_ref=receipt_ref,
            metadata={"receipt_binding": binding},
        )
        policy = {
            "metadata_field": "receipt_binding",
            "target_scope": "PROVIDER_RECEIPT",
            "required_fields": list(binding),
            "receipt_schema": "VERA_MEMORY_EPOCH_PROVIDER_RECEIPT_V1",
            "receipt_type": "GOOGLE_DRIVE_DURABLE",
            "digest_algorithm": "SHA256_CANONICAL_JSON_EXCLUDING_RECEIPT_DIGEST",
        }
        result = reconcile_exact_receipt(
            "projection:r9b0-drive-supabase-provider-receipt",
            source,
            target,
            source_subject="drive:r9b0-memory-epoch-object",
            target_subject="supabase:klmbpaigzeguvnpccqzz/vera_memory_epoch_provider_receipts_v1",
            event_ref="logical-memory:R9B0",
            event_path="memory-epoch-object",
            receipt_policy=policy,
        )
        self.assertEqual(result.status, "UNRESOLVED")
        self.assertIn("source", result.reason.lower())
        self.assertIn("digest", result.reason.lower())


if __name__ == "__main__":
    unittest.main()
