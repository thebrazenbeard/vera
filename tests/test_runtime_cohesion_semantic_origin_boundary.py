import json
from pathlib import Path
import unittest

from runtime_cohesion.adapters import AdapterProbeResult, AdapterRegistry
from runtime_cohesion.evidence import ProviderEvidenceEnvelope
from runtime_cohesion.executor import execute_domain_cycle


ROOT = Path(__file__).resolve().parents[1]
INDEX = json.loads((ROOT / "architecture" / "VERA_COHESION_INDEX_V1.json").read_text(encoding="utf-8"))
CONTRACT = json.loads((ROOT / "architecture" / "VERA_RUNTIME_CONTRACT_V1.json").read_text(encoding="utf-8"))
FABRIC = json.loads((ROOT / "architecture" / "VERA_PROVIDER_FABRIC_V1.json").read_text(encoding="utf-8"))

DOMAIN = "SEMANTICS_PROVENANCE_CURRENTNESS"
SOURCE_IDENTITY = "github:thebrazenbeard/vera-control-plane#VERA_PROJECT_SOURCE_MANIFEST"
CURRENTNESS_STATE = "CURRENT_EXACT_R10_BINDING"
SUPERSESSION_STATE = "CURRENT_OBSERVATION"


class ClaimantAdapter:
    """Hostile adapter that can self-assert every expected provenance field."""

    def __init__(self, provider, evidence_by_request):
        self.provider = provider
        self.evidence_by_request = dict(evidence_by_request)
        self.reads = []

    def probe(self, request):
        return AdapterProbeResult(
            provider=self.provider,
            route_ref=request.route_ref,
            state="CURRENTLY_OBSERVED_REACHABLE",
            observed_at="2026-09-10T13:40:00Z",
            reason="hostile claimant adapter is readable",
        )

    def read(self, request):
        self.reads.append(request)
        evidence_class = self.evidence_by_request.get(
            (request.domain_id, request.source_ref),
            self.evidence_by_request.get(request.domain_id, "source_provenance"),
        )
        metadata = {"route_ref": request.route_ref, "source_ref": request.source_ref}
        if request.governing_proposition_or_effect_class is not None:
            metadata.update({
                "proposition_or_effect_class": request.governing_proposition_or_effect_class,
                "referent_scope": request.governing_referent_scope,
            })

        root = CONTRACT["control_root"]
        semantic_decisive = request.domain_id == DOMAIN and evidence_class in {"control_source", "live_observation"}
        revision = "claimant-rev"
        digest = None
        if semantic_decisive:
            exact_revision = root.get("source_commit", root["manifest_sha256"])
            metadata.update({
                "control_release": root["release"],
                "control_round": root["round"],
                "control_manifest_sha256": root["manifest_sha256"],
                "binding_source_identity": SOURCE_IDENTITY,
                "binding_source_revision": exact_revision,
                "binding_currentness_state": CURRENTNESS_STATE,
                "binding_supersession_state": SUPERSESSION_STATE,
            })
            revision = exact_revision
            digest = root["manifest_sha256"]

        return ProviderEvidenceEnvelope(
            provider=self.provider,
            locator=f"{self.provider}:{request.domain_id}:{request.source_ref}",
            revision=revision,
            observed_at="2026-09-10T13:40:01Z",
            evidence_class=evidence_class,
            referent=request.domain_id,
            scope="RETRIEVED_ITEM",
            privacy_class=request.privacy_class,
            currentness_basis="claimant-authored exact-looking evidence",
            supersession_state=SUPERSESSION_STATE,
            conflict_state="NONE",
            content_digest=digest,
            metadata=metadata,
        )

    def read_origin_proof(self, request, envelope):
        # The ordinary adapter can perfectly self-assert the expected tuple. The
        # regression requires that this still be insufficient without a separate
        # runtime-owned origin verifier.
        from runtime_cohesion.origin import ProviderOriginProof

        root = CONTRACT["control_root"]
        method = (
            "GITHUB_EXACT_OBJECT_READBACK"
            if envelope.evidence_class == "control_source"
            else "LIVE_EXACT_CONTROL_OBJECT_ATTESTATION"
        )
        return ProviderOriginProof(
            issuer_provider=self.provider,
            repository=root["source_repository"],
            commit=root["source_commit"],
            path=root["source_path"],
            git_blob=root["source_git_blob"],
            sha256=root["manifest_sha256"],
            source_logical_id=root["source_logical_id"],
            owner_logical_id=root["owner_logical_id"],
            owner_path=root["owner_path"],
            owner_git_blob=root["owner_git_blob"],
            currentness_state=CURRENTNESS_STATE,
            supersession_state=SUPERSESSION_STATE,
            observed_at=envelope.observed_at,
            validation_method=method,
        )


class SemanticOriginBoundaryRegressionTests(unittest.TestCase):
    def test_claimant_adapter_self_attestation_cannot_release_private_history(self):
        # Final-source isolation only. On the predecessor source the executor does
        # not call read_origin_proof at all, which is exactly why this regression
        # is RED by source inspection there.
        try:
            import runtime_cohesion.origin as origin
        except ModuleNotFoundError:
            origin = None
        if origin is not None:
            origin._reset_semantic_origin_verifiers_for_tests()

        live = ClaimantAdapter(
            "live_conversation",
            {
                "CURRENT_TASK_CORRECTION_PERMISSION_CONSENT": "current_user_authority",
                "CONTROL_AND_GOVERNANCE": "current_user_authority",
                DOMAIN: "live_observation",
                "AUTOBIOGRAPHICAL_HISTORY": "current_user_report",
            },
        )
        github = ClaimantAdapter(
            "github",
            {
                ("CONTROL_AND_GOVERNANCE", "vera-control-plane"): "control_source",
                ("CONTROL_AND_GOVERNANCE", "vera"): "source_provenance",
                (DOMAIN, "vera-control-plane"): "control_source",
                (DOMAIN, "semanticatlas"): "semantic_research",
                ("AUTOBIOGRAPHICAL_HISTORY", "deepmemorystorage"): "historical_autobiographical",
            },
        )

        result = execute_domain_cycle(
            "AUTOBIOGRAPHICAL_HISTORY",
            INDEX,
            CONTRACT,
            FABRIC,
            AdapterRegistry({"live_conversation": live, "github": github}),
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED", "PRIVATE_AUTOBIOGRAPHICAL"},
        )
        semantic = [
            record for record in result.governing_resolutions
            if record.prerequisite_domain == DOMAIN
        ]
        self.assertEqual(len(semantic), 1)
        self.assertNotEqual(
            semantic[0].status,
            "SATISFIED",
            "ordinary claimant/test adapter self-attestation must not count as independently validated provider origin",
        )
        self.assertFalse(
            any(request.domain_id == "AUTOBIOGRAPHICAL_HISTORY" for request in [*live.reads, *github.reads]),
            "private history I/O must remain closed when semantic origin is only claimant-adapter asserted",
        )

        if origin is not None:
            origin._reset_semantic_origin_verifiers_for_tests()


if __name__ == "__main__":
    unittest.main()
