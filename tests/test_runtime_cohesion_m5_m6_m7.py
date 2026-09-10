import hashlib
import json
from pathlib import Path
import unittest

from runtime_cohesion.adapters import AdapterRequest
from runtime_cohesion.audit import audit_registered_projections
from runtime_cohesion.evidence import ProviderEvidenceEnvelope
from runtime_cohesion.executor import _validate_read
import runtime_cohesion.item_typing as item_typing
from runtime_cohesion.item_typing import ProviderItemTypeProof
from runtime_cohesion.reconcile import reconcile_exact_receipt
from tests import _install_fixture_item_type_verifiers


ROOT = Path(__file__).resolve().parents[1]
FABRIC = json.loads((ROOT / "architecture" / "VERA_PROVIDER_FABRIC_V1.json").read_text(encoding="utf-8"))
FIXTURE = json.loads(
    (ROOT / "tests" / "fixtures" / "runtime_cohesion" / "provider-observations-v1.json").read_text(encoding="utf-8")
)
RECEIPT_PROJECTION = next(
    row for row in FABRIC["projections"]
    if row["id"] == "projection:r9b0-drive-supabase-provider-receipt"
)
RECEIPT_REF = "supabase:klmbpaigzeguvnpccqzz/vera_memory_epoch_provider_receipts_v1/GOOGLE_DRIVE_DURABLE"


def env(row):
    return ProviderEvidenceEnvelope(**row)


def receipt_source(*, revision="drive-revision-7", digest="sha256:object-7", receipt_ref=None):
    return ProviderEvidenceEnvelope(
        provider="google_drive",
        locator="drive:file/r9b0-object",
        revision=revision,
        observed_at="2026-09-10T16:00:00Z",
        evidence_class="persisted_provider_record",
        referent="r9b0-memory-epoch-drive-object",
        scope="PROVIDER_OBJECT",
        privacy_class="PRIVATE_AUTOBIOGRAPHICAL",
        currentness_basis="drive exact object readback",
        supersession_state="CURRENT_OBSERVATION",
        conflict_state="NONE",
        content_digest=digest,
        receipt_ref=receipt_ref,
        metadata={"projection_role": "SOURCE"},
    )


def _binding_digest(binding):
    core = dict(binding)
    core.pop("receipt_digest", None)
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def receipt_target(
    source,
    *,
    target_revision="receipt-row-v22",
    event_ref="logical-memory:R9B0",
    event_path="memory-epoch-object",
    include_binding=True,
    receipt_schema="VERA_MEMORY_EPOCH_PROVIDER_RECEIPT_V1",
    receipt_type="GOOGLE_DRIVE_DURABLE",
    corrupt_receipt_digest=False,
):
    metadata = {"projection_role": "TARGET"}
    receipt_digest = None
    if include_binding:
        binding = {
            "receipt_schema": receipt_schema,
            "receipt_type": receipt_type,
            "source_subject": "drive:r9b0-memory-epoch-object",
            "target_subject": "supabase:klmbpaigzeguvnpccqzz/vera_memory_epoch_provider_receipts_v1",
            "source_locator": source.locator,
            "source_revision": source.revision,
            "source_content_digest": source.content_digest,
            "event_ref": event_ref,
            "event_path": event_path,
            "receipt_ref": RECEIPT_REF,
        }
        receipt_digest = _binding_digest(binding)
        binding["receipt_digest"] = (
            "sha256:" + "f" * 64 if corrupt_receipt_digest else receipt_digest
        )
        metadata["receipt_binding"] = binding
    return ProviderEvidenceEnvelope(
        provider="supabase",
        locator=RECEIPT_REF,
        revision=target_revision,
        observed_at="2026-09-10T16:00:01Z",
        evidence_class="persisted_provider_record",
        referent=source.referent,
        scope="PROVIDER_RECEIPT",
        privacy_class="PRIVATE_AUTOBIOGRAPHICAL",
        currentness_basis="fresh receipt row readback",
        supersession_state="CURRENT_OBSERVATION",
        conflict_state="NONE",
        content_digest=receipt_digest,
        receipt_ref=RECEIPT_REF,
        metadata=metadata,
    )


def reconcile_receipt(source, target):
    return reconcile_exact_receipt(
        RECEIPT_PROJECTION["id"],
        source,
        target,
        source_subject=RECEIPT_PROJECTION["source_subject"],
        target_subject=RECEIPT_PROJECTION["target_subject"],
        event_ref="logical-memory:R9B0",
        event_path="memory-epoch-object",
        receipt_policy=RECEIPT_PROJECTION["receipt_binding"],
    )


class _IndependentMismatchVerifier:
    provider = "github"

    def verify(self, request, envelope):
        return ProviderItemTypeProof(
            issuer_provider="github",
            route_ref=request.route_ref,
            source_ref=request.source_ref,
            locator=envelope.locator,
            revision=envelope.revision,
            observed_at=envelope.observed_at,
            derived_evidence_class="source_provenance",
            currentness_basis=envelope.currentness_basis,
            supersession_state=envelope.supersession_state,
            conflict_state=envelope.conflict_state,
            validation_method="TEST_INDEPENDENT_MISMATCH",
            provenance_ref="fixture:independent-mismatch",
            content_digest=envelope.content_digest,
            receipt_ref=envelope.receipt_ref,
            event_ref=request.event_ref,
            event_path=request.event_path,
        )


class RuntimeCohesionM5M6M7RegressionTests(unittest.TestCase):
    def tearDown(self):
        item_typing._reset_item_type_verifiers_for_tests()
        _install_fixture_item_type_verifiers()

    def test_m5_public_supplied_observation_audit_cannot_mint_verified_exact(self):
        rows = FIXTURE["observations"]
        result = audit_registered_projections(
            FABRIC,
            {
                "projection:semanticatlas-github-to-supabase": {
                    "source": env(rows["semanticatlas_github"]),
                    "target": env(rows["semanticatlas_supabase"]),
                    "source_ref": "refs/heads/research/cee-always-active-v0.2",
                    "source_path": "runtime-manifest/current.json",
                }
            },
        )[0]
        self.assertEqual(result.status, "UNRESOLVED")
        self.assertIn("cannot mint verified_exact", result.reason.lower())

    def _typing_request_and_envelope(self):
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

    def test_m6_capability_and_adapter_claim_cannot_replace_missing_independent_verifier(self):
        request, envelope = self._typing_request_and_envelope()
        item_typing._reset_item_type_verifiers_for_tests()
        with self.assertRaisesRegex(ValueError, "independently validated type/currentness"):
            _validate_read(request, envelope)

    def test_m6_permitted_adapter_claim_fails_when_independent_type_derivation_disagrees(self):
        request, envelope = self._typing_request_and_envelope()
        item_typing._reset_item_type_verifiers_for_tests()
        item_typing._install_item_type_verifiers({"github": _IndependentMismatchVerifier()})
        with self.assertRaisesRegex(ValueError, "independently derived"):
            _validate_read(request, envelope)

    def test_m6_receipt_sensitive_classification_cannot_omit_receipt_or_digest_provenance(self):
        base = dict(
            issuer_provider="supabase",
            route_ref="route:supabase",
            source_ref="receipt-table",
            locator="supabase:receipt/1",
            revision="row-v1",
            observed_at="2026-09-10T16:00:00Z",
            derived_evidence_class="persisted_provider_record",
            currentness_basis="receipt readback",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            validation_method="PROVIDER_RECEIPT_CONTENT_VALIDATION",
            provenance_ref="supabase:receipt/1",
        )
        with self.assertRaisesRegex(ValueError, "content_digest"):
            ProviderItemTypeProof(**base, provenance_basis="CONTENT_AND_RECEIPT")
        with self.assertRaisesRegex(ValueError, "receipt_ref"):
            ProviderItemTypeProof(
                **base,
                provenance_basis="CONTENT_AND_RECEIPT",
                content_digest="sha256:abc",
            )

    def test_m6_reusable_verifier_does_not_embed_domain_referent_equality(self):
        text = (ROOT / "runtime_cohesion" / "item_typing.py").read_text(encoding="utf-8")
        self.assertNotIn("request.domain_id", text)
        self.assertNotIn("envelope.referent", text)

    def test_m7_same_revision_without_receipt_object_binding_cannot_verify(self):
        source = receipt_source(revision="same-revision")
        target = receipt_target(source, target_revision="same-revision", include_binding=False)
        result = reconcile_receipt(source, target)
        self.assertEqual(result.status, "UNRESOLVED")
        self.assertNotEqual(result.status, "VERIFIED_EXACT")

    def test_m7_target_receipt_proves_source_without_source_knowing_downstream_receipt(self):
        source = receipt_source(receipt_ref=None)
        target = receipt_target(source, target_revision="provider-receipt-row-version-22")
        result = reconcile_receipt(source, target)
        self.assertEqual(result.status, "VERIFIED_EXACT")
        self.assertIsNone(source.receipt_ref)
        self.assertIn("source receipt_ref was not required", result.reason.lower())

    def test_m7_optional_source_receipt_ref_is_cross_checked_if_present(self):
        source = receipt_source(receipt_ref="supabase:wrong-receipt")
        target = receipt_target(source)
        result = reconcile_receipt(source, target)
        self.assertEqual(result.status, "CONFLICT")
        self.assertIn("source", result.reason.lower())
        self.assertIn("receipt_ref", result.reason)

    def test_m7_valid_receipt_can_verify_without_target_revision_equality(self):
        source = receipt_source(revision="drive-revision-7")
        target = receipt_target(source, target_revision="provider-receipt-row-version-22")
        result = reconcile_receipt(source, target)
        self.assertEqual(result.status, "VERIFIED_EXACT")
        self.assertNotEqual(source.revision, target.revision)
        self.assertIn("target revision equality was not used", result.reason.lower())

    def test_m7_wrong_event_receipt_binding_is_conflict(self):
        source = receipt_source()
        target = receipt_target(source, event_path="different-object")
        result = reconcile_receipt(source, target)
        self.assertEqual(result.status, "CONFLICT")
        self.assertIn("event_path", result.reason)

    def test_m7_wrong_receipt_schema_or_type_is_conflict(self):
        source = receipt_source()
        for target in (
            receipt_target(source, receipt_schema="WRONG_SCHEMA"),
            receipt_target(source, receipt_type="WRONG_TYPE"),
        ):
            self.assertEqual(reconcile_receipt(source, target).status, "CONFLICT")

    def test_m7_corrupt_receipt_digest_is_conflict(self):
        source = receipt_source()
        target = receipt_target(source, corrupt_receipt_digest=True)
        result = reconcile_receipt(source, target)
        self.assertEqual(result.status, "CONFLICT")
        self.assertIn("digest", result.reason.lower())


if __name__ == "__main__":
    unittest.main()
