from __future__ import annotations

import json
from pathlib import Path
import unittest

from runtime_cohesion.evidence import ProviderEvidenceEnvelope
import runtime_cohesion.origin as origin


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "architecture" / "VERA_RUNTIME_CONTRACT_V1.json").read_text(encoding="utf-8"))
DOMAIN = "SEMANTICS_PROVENANCE_CURRENTNESS"
SOURCE_IDENTITY = "github:thebrazenbeard/vera-control-plane#VERA_PROJECT_SOURCE_MANIFEST"
CURRENTNESS_STATE = "CURRENT_EXACT_R10_BINDING"
SUPERSESSION_STATE = "CURRENT_OBSERVATION"


class SelfMintingVerifier:
    provider = "github"

    def verify(self, envelope):
        root = CONTRACT["control_root"]
        return origin.ProviderOriginProof(
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
            validation_method="GITHUB_EXACT_OBJECT_READBACK",
        )


class SemanticOriginUnrootedTests(unittest.TestCase):
    def setUp(self):
        origin._reset_semantic_origin_verifiers_for_tests()

    def tearDown(self):
        origin._reset_semantic_origin_verifiers_for_tests()

    def envelope(self):
        root = CONTRACT["control_root"]
        return ProviderEvidenceEnvelope(
            provider="github",
            locator="github:vera-control-plane:r10-manifest",
            revision=root["source_commit"],
            observed_at="2026-09-10T22:15:00-04:00",
            evidence_class="control_source",
            referent=DOMAIN,
            scope="RETRIEVED_ITEM",
            privacy_class="GOVERNED",
            currentness_basis="hostile in-process verifier proof",
            supersession_state=SUPERSESSION_STATE,
            conflict_state="NONE",
            content_digest=root["manifest_sha256"],
            metadata={
                "binding_source_identity": SOURCE_IDENTITY,
                "binding_source_revision": root["source_commit"],
                "binding_currentness_state": CURRENTNESS_STATE,
                "binding_supersession_state": SUPERSESSION_STATE,
            },
        )

    def test_self_consistent_in_process_first_writer_cannot_register_provider_origin(self):
        envelope = self.envelope()
        origin._install_semantic_origin_verifiers({"github": SelfMintingVerifier()})

        self.assertEqual(
            origin.semantic_origin_composition_trust(),
            "IN_PROCESS_UNROOTED_NON_QUALIFYING",
        )
        self.assertFalse(origin.validate_and_register_semantic_origin(envelope, CONTRACT))
        self.assertIsNone(origin.validated_semantic_origin(envelope, CONTRACT))

    def test_unrooted_verifier_reinstallation_does_not_create_a_qualifying_registry_entry(self):
        envelope = self.envelope()
        verifier = SelfMintingVerifier()
        origin._install_semantic_origin_verifiers({"github": verifier})
        origin._install_semantic_origin_verifiers({"github": verifier})

        self.assertFalse(origin.validate_and_register_semantic_origin(envelope, CONTRACT))
        self.assertIsNone(origin.validated_semantic_origin(envelope, CONTRACT))


if __name__ == "__main__":
    unittest.main()
