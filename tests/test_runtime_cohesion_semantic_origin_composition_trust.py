import json
from pathlib import Path
import unittest

from runtime_cohesion.evidence import ProviderEvidenceEnvelope
import runtime_cohesion.origin as origin
from runtime_cohesion.origin import ProviderOriginProof


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "architecture" / "VERA_RUNTIME_CONTRACT_V1.json").read_text(encoding="utf-8")
)


class FirstWriterOriginForger:
    provider = "github"

    def verify(self, envelope):
        root = CONTRACT["control_root"]
        return ProviderOriginProof(
            issuer_provider="github",
            repository=root["source_repository"],
            commit=root["source_commit"],
            path=root["source_path"],
            git_blob=root["source_git_blob"],
            sha256=root["manifest_sha256"],
            source_logical_id=root["source_logical_id"],
            owner_logical_id=root["owner_logical_id"],
            owner_path=root["owner_path"],
            owner_git_blob=root["owner_git_blob"],
            currentness_state="CURRENT_EXACT_R10_BINDING",
            supersession_state="CURRENT_OBSERVATION",
            observed_at=envelope.observed_at,
            validation_method="GITHUB_EXACT_OBJECT_READBACK",
        )


class SemanticOriginCompositionTrustTests(unittest.TestCase):
    def setUp(self):
        origin._reset_semantic_origin_verifiers_for_tests()

    def tearDown(self):
        origin._reset_semantic_origin_verifiers_for_tests()

    def envelope(self):
        root = CONTRACT["control_root"]
        return ProviderEvidenceEnvelope(
            provider="github",
            locator="github:attacker/self-minted-r10-looking-object",
            revision=root["source_commit"],
            observed_at="2026-09-10T22:10:00Z",
            evidence_class="control_source",
            referent=origin.SEMANTIC_CURRENTNESS_DOMAIN,
            scope="RETRIEVED_ITEM",
            privacy_class="GOVERNED",
            currentness_basis="caller-shaped exact-looking evidence",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            content_digest=root["manifest_sha256"],
            metadata={
                "binding_source_identity": "github:thebrazenbeard/vera-control-plane#VERA_PROJECT_SOURCE_MANIFEST",
                "binding_source_revision": root["source_commit"],
                "binding_currentness_state": "CURRENT_EXACT_R10_BINDING",
                "binding_supersession_state": "CURRENT_OBSERVATION",
            },
        )

    def test_first_writer_verifier_cannot_mint_qualifying_semantic_origin(self):
        envelope = self.envelope()
        origin._install_semantic_origin_verifiers({"github": FirstWriterOriginForger()})

        self.assertIsNone(
            origin.validated_semantic_origin(envelope, CONTRACT),
            "an unrooted in-process first writer must not become provider/currentness authentication",
        )


if __name__ == "__main__":
    unittest.main()
