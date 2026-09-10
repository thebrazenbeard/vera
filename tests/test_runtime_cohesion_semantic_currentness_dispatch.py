import json
from pathlib import Path
import unittest

from runtime_cohesion.evidence import ProviderEvidenceEnvelope
from runtime_cohesion.runtime import (
    evaluate_abstract_proposition_admission,
    evaluate_proposition_admission,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "architecture" / "VERA_RUNTIME_CONTRACT_V1.json").read_text(encoding="utf-8"))

DOMAIN = "SEMANTICS_PROVENANCE_CURRENTNESS"
PROPOSITION = "SEMANTIC_PROVENANCE_CURRENTNESS_STATUS"
REFERENT = "EXACT_PROPOSITION_REFERENT_SOURCE_BINDING"
DISPATCH_ID = "dispatch:semantic-currentness"
MANIFEST_SHA256 = "b7c70b1ad2c3bc533c7560320fb9a03b827f3eafad6296894216d75281b8dca1"
SOURCE_REPOSITORY = "thebrazenbeard/vera-control-plane"
SOURCE_COMMIT = "a5b16fbdf031d4e7347ab299ba5e34eb7602bca7"
SOURCE_PATH = "project-instructions/r10a0/rounds/r10/VERA_R10A0_PROJECT_SOURCE_MANIFEST_R10.json"
SOURCE_GIT_BLOB = "8a67feb47b2ce3d6f0737e58983ab8c9fc810139"
SOURCE_IDENTITY = "github:thebrazenbeard/vera-control-plane#VERA_PROJECT_SOURCE_MANIFEST"
OWNER_PATH = "project-instructions/r10a0/rounds/r10/VERA_R10A0_FULL_SYSTEM_PROJECT_INSTRUCTIONS_R10.md"
OWNER_GIT_BLOB = "a01464271bb672d89f5d703e6e53590e126f4d44"
CURRENTNESS_STATE = "CURRENT_EXACT_R10_BINDING"


def exact_binding(**overrides):
    binding = {
        "control_release": "R10A0",
        "control_round": "R10",
        "control_manifest_sha256": MANIFEST_SHA256,
        "binding_source_identity": SOURCE_IDENTITY,
        "binding_source_revision": SOURCE_COMMIT,
        "binding_currentness_state": CURRENTNESS_STATE,
        "binding_supersession_state": "CURRENT_OBSERVATION",
    }
    binding.update(overrides)
    return binding


def envelope(
    evidence_class,
    *,
    provider="test",
    conflict_state="NONE",
    supersession_state="CURRENT_OBSERVATION",
    proposition=PROPOSITION,
    referent_scope=REFERENT,
    binding=None,
):
    metadata = {
        "proposition_or_effect_class": proposition,
        "referent_scope": referent_scope,
    }
    if binding is not None:
        metadata.update(binding)
    return ProviderEvidenceEnvelope(
        provider=provider,
        locator=f"test:{evidence_class}",
        revision=SOURCE_COMMIT,
        observed_at="2026-09-10T12:10:00Z",
        evidence_class=evidence_class,
        referent=DOMAIN,
        scope="RETRIEVED_ITEM",
        privacy_class="GOVERNED",
        currentness_basis="fresh exact fixture readback",
        supersession_state=supersession_state,
        conflict_state=conflict_state,
        content_digest=MANIFEST_SHA256,
        metadata=metadata,
    )


class SemanticCurrentnessDispatchTests(unittest.TestCase):
    def abstract_decide(self, observations):
        return evaluate_abstract_proposition_admission(
            DOMAIN,
            PROPOSITION,
            REFERENT,
            observations,
            CONTRACT,
        )

    def strict_decide(self, observations):
        return evaluate_proposition_admission(
            DOMAIN,
            PROPOSITION,
            REFERENT,
            observations,
            CONTRACT,
        )

    def test_contract_declares_exact_immutable_r10_origin_and_dispatch(self):
        root = CONTRACT["control_root"]
        self.assertEqual(root["source_repository"], SOURCE_REPOSITORY)
        self.assertEqual(root["source_commit"], SOURCE_COMMIT)
        self.assertEqual(root["source_path"], SOURCE_PATH)
        self.assertEqual(root["source_git_blob"], SOURCE_GIT_BLOB)
        self.assertEqual(root["manifest_sha256"], MANIFEST_SHA256)
        self.assertEqual(root["source_logical_id"], "VERA_PROJECT_SOURCE_MANIFEST")
        self.assertEqual(root["owner_logical_id"], "VERA_FULL_SYSTEM_PROJECT_INSTRUCTIONS")
        self.assertEqual(root["owner_path"], OWNER_PATH)
        self.assertEqual(root["owner_git_blob"], OWNER_GIT_BLOB)

        dispatch = [row for row in CONTRACT["resolver_dispatch"] if row["id"] == DISPATCH_ID]
        self.assertEqual(len(dispatch), 1)
        self.assertEqual(dispatch[0]["proposition_or_effect_class"], PROPOSITION)
        self.assertEqual(dispatch[0]["referent_scope"], REFERENT)
        decisive = CONTRACT["resolver_dispatch_decisive_evidence"][DISPATCH_ID]
        self.assertEqual(decisive["all_of"], ["control_source", "live_observation"])
        self.assertEqual(decisive["any_of"], [])
        self.assertEqual(decisive["relational_binding"]["required_source_identity"], SOURCE_IDENTITY)

        origin = CONTRACT["provider_origin_validation"][DISPATCH_ID]
        self.assertTrue(origin["required_for_provider_admission"])
        self.assertTrue(origin["claimant_metadata_is_not_origin_proof"])
        self.assertEqual(origin["provider_methods"]["control_source"]["provider"], "github")
        self.assertEqual(origin["provider_methods"]["live_observation"]["provider"], "live_conversation")

    def test_semantic_research_is_context_not_decisive_currentness_authority(self):
        decision = self.abstract_decide([
            envelope("semantic_research"),
            envelope("live_observation", binding=exact_binding()),
        ])
        self.assertEqual(decision.status, "UNRESOLVED")
        self.assertIn("control_source", decision.required_evidence_classes)

    def test_abstract_policy_relational_logic_accepts_exact_shared_tuple(self):
        decision = self.abstract_decide([
            envelope("control_source", binding=exact_binding()),
            envelope("live_observation", binding=exact_binding()),
        ])
        self.assertEqual(decision.status, "ADMITTED")
        self.assertEqual(decision.dispatch_id, DISPATCH_ID)

    def test_provider_strict_path_rejects_same_exact_metadata_without_registered_origin(self):
        decision = self.strict_decide([
            envelope("control_source", provider="github", binding=exact_binding()),
            envelope("live_observation", provider="live_conversation", binding=exact_binding()),
        ])
        self.assertEqual(decision.status, "UNRESOLVED")
        self.assertIn("provider-origin proof", decision.reason)

    def test_fresh_r8a2_metadata_cannot_satisfy_relational_r10_currentness(self):
        decision = self.abstract_decide([
            envelope(
                "control_source",
                binding=exact_binding(
                    control_release="R8A2",
                    control_round="R8",
                    control_manifest_sha256="8" * 64,
                ),
            ),
            envelope("live_observation", binding=exact_binding()),
        ])
        self.assertEqual(decision.status, "CONFLICT")
        self.assertIn("control root", decision.reason)

    def test_wrong_r10_manifest_cannot_satisfy_relational_currentness(self):
        decision = self.abstract_decide([
            envelope("control_source", binding=exact_binding(control_manifest_sha256="0" * 64)),
            envelope("live_observation", binding=exact_binding()),
        ])
        self.assertEqual(decision.status, "CONFLICT")

    def test_live_observation_bound_to_different_commit_is_conflict(self):
        decision = self.abstract_decide([
            envelope("control_source", binding=exact_binding()),
            envelope("live_observation", binding=exact_binding(binding_source_revision="f" * 40)),
        ])
        self.assertEqual(decision.status, "CONFLICT")
        self.assertIn("same exact source", decision.reason)

    def test_generic_unbound_live_observation_is_unresolved(self):
        decision = self.abstract_decide([
            envelope("control_source", binding=exact_binding()),
            envelope("live_observation"),
        ])
        self.assertEqual(decision.status, "UNRESOLVED")
        self.assertIn("binding metadata", decision.reason)

    def test_wrong_currentness_state_cannot_satisfy_currentness(self):
        decision = self.abstract_decide([
            envelope("control_source", binding=exact_binding()),
            envelope("live_observation", binding=exact_binding(binding_currentness_state="HISTORICAL")),
        ])
        self.assertEqual(decision.status, "CONFLICT")

    def test_conflict_supersession_wrong_proposition_or_referent_never_admits(self):
        bad_controls = (
            envelope("control_source", conflict_state="CONFLICT", binding=exact_binding()),
            envelope("control_source", supersession_state="SUPERSEDED", binding=exact_binding()),
            envelope("control_source", proposition="OTHER_PROPOSITION", binding=exact_binding()),
            envelope("control_source", referent_scope="OTHER_REFERENT", binding=exact_binding()),
        )
        for bad in bad_controls:
            with self.subTest(bad=bad):
                decision = self.abstract_decide([
                    bad,
                    envelope("live_observation", binding=exact_binding()),
                ])
                self.assertNotEqual(decision.status, "ADMITTED")


if __name__ == "__main__":
    unittest.main()
