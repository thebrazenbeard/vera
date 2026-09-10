import inspect
import json
from pathlib import Path
import unittest

from runtime_cohesion.adapters import AdapterProbeResult, AdapterRegistry
from runtime_cohesion.evidence import ProviderEvidenceEnvelope
from runtime_cohesion.executor import _expected_governing_dispatch, execute_domain_cycle
import runtime_cohesion.origin as origin
from runtime_cohesion.origin import ProviderOriginProof

ROOT = Path(__file__).resolve().parents[1]
INDEX = json.loads((ROOT / "architecture" / "VERA_COHESION_INDEX_V1.json").read_text(encoding="utf-8"))
CONTRACT = json.loads((ROOT / "architecture" / "VERA_RUNTIME_CONTRACT_V1.json").read_text(encoding="utf-8"))
FABRIC = json.loads((ROOT / "architecture" / "VERA_PROVIDER_FABRIC_V1.json").read_text(encoding="utf-8"))

EXPECTED_PROP = "TASK_SCOPE_PERMISSION_OR_USER_CONSENT"
EXPECTED_SCOPE = "PATRICK_OR_USER_CONTROLLED_OPERATION"
SEMANTIC_PROP = "SEMANTIC_PROVENANCE_CURRENTNESS_STATUS"
SEMANTIC_SCOPE = "EXACT_PROPOSITION_REFERENT_SOURCE_BINDING"
MANIFEST_SHA256 = "b7c70b1ad2c3bc533c7560320fb9a03b827f3eafad6296894216d75281b8dca1"
SOURCE_REPOSITORY = "thebrazenbeard/vera-control-plane"
SOURCE_COMMIT = "a5b16fbdf031d4e7347ab299ba5e34eb7602bca7"
SOURCE_PATH = "project-instructions/r10a0/rounds/r10/VERA_R10A0_PROJECT_SOURCE_MANIFEST_R10.json"
SOURCE_GIT_BLOB = "8a67feb47b2ce3d6f0737e58983ab8c9fc810139"
SOURCE_LOGICAL_ID = "VERA_PROJECT_SOURCE_MANIFEST"
SOURCE_IDENTITY = "github:thebrazenbeard/vera-control-plane#VERA_PROJECT_SOURCE_MANIFEST"
OWNER_LOGICAL_ID = "VERA_FULL_SYSTEM_PROJECT_INSTRUCTIONS"
OWNER_PATH = "project-instructions/r10a0/rounds/r10/VERA_R10A0_FULL_SYSTEM_PROJECT_INSTRUCTIONS_R10.md"
OWNER_GIT_BLOB = "a01464271bb672d89f5d703e6e53590e126f4d44"
CURRENTNESS_STATE = "CURRENT_EXACT_R10_BINDING"
SUPERSESSION_STATE = "CURRENT_OBSERVATION"


def exact_semantic_binding(**overrides):
    value = {
        "control_release": "R10A0",
        "control_round": "R10",
        "control_manifest_sha256": MANIFEST_SHA256,
        "binding_source_identity": SOURCE_IDENTITY,
        "binding_source_revision": SOURCE_COMMIT,
        "binding_currentness_state": CURRENTNESS_STATE,
        "binding_supersession_state": SUPERSESSION_STATE,
    }
    value.update(overrides)
    return value


def origin_proof(provider, evidence_class, observed_at, **overrides):
    method = (
        "GITHUB_EXACT_OBJECT_READBACK"
        if evidence_class == "control_source"
        else "LIVE_EXACT_CONTROL_OBJECT_ATTESTATION"
    )
    values = {
        "issuer_provider": provider,
        "repository": SOURCE_REPOSITORY,
        "commit": SOURCE_COMMIT,
        "path": SOURCE_PATH,
        "git_blob": SOURCE_GIT_BLOB,
        "sha256": MANIFEST_SHA256,
        "source_logical_id": SOURCE_LOGICAL_ID,
        "owner_logical_id": OWNER_LOGICAL_ID,
        "owner_path": OWNER_PATH,
        "owner_git_blob": OWNER_GIT_BLOB,
        "currentness_state": CURRENTNESS_STATE,
        "supersession_state": SUPERSESSION_STATE,
        "observed_at": observed_at,
        "validation_method": method,
    }
    values.update(overrides)
    return ProviderOriginProof(**values)


class IndependentOriginVerifier:
    def __init__(self, provider, overrides=None):
        self.provider = provider
        self.overrides = dict(overrides or {})

    def verify(self, envelope):
        return origin_proof(
            self.provider,
            envelope.evidence_class,
            envelope.observed_at,
            **self.overrides,
        )


class EvidenceAdapter:
    def __init__(
        self,
        provider,
        evidence_by_request,
        *,
        conflict_state="NONE",
        referent_override=None,
        proposition_override=None,
        referent_scope_override=None,
        semantic_binding_overrides=None,
    ):
        self.provider = provider
        self.evidence_by_request = dict(evidence_by_request)
        self.conflict_state = conflict_state
        self.referent_override = referent_override
        self.proposition_override = proposition_override
        self.referent_scope_override = referent_scope_override
        self.semantic_binding_overrides = dict(semantic_binding_overrides or {})
        self.probes = []
        self.reads = []

    def probe(self, request):
        self.probes.append(request)
        return AdapterProbeResult(
            provider=self.provider,
            route_ref=request.route_ref,
            state="CURRENTLY_OBSERVED_REACHABLE",
            observed_at="2026-09-09T18:10:00Z",
            reason="governing-resolution fixture",
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
                "proposition_or_effect_class": (
                    self.proposition_override or request.governing_proposition_or_effect_class
                ),
                "referent_scope": (
                    self.referent_scope_override or request.governing_referent_scope
                ),
            })
        semantic_decisive = (
            request.domain_id == "SEMANTICS_PROVENANCE_CURRENTNESS"
            and evidence_class in {"control_source", "live_observation"}
        )
        if semantic_decisive:
            metadata.update(exact_semantic_binding(**self.semantic_binding_overrides))
        return ProviderEvidenceEnvelope(
            provider=self.provider,
            locator=f"{self.provider}:{request.domain_id}:{request.source_ref}",
            revision=SOURCE_COMMIT if semantic_decisive else "governing-resolution-rev-1",
            observed_at="2026-09-09T18:10:01Z",
            evidence_class=evidence_class,
            referent=self.referent_override or request.domain_id,
            scope="RETRIEVED_ITEM",
            privacy_class=request.privacy_class,
            currentness_basis="fresh_exact_adapter_readback",
            supersession_state=SUPERSESSION_STATE,
            conflict_state=self.conflict_state,
            content_digest=MANIFEST_SHA256 if semantic_decisive else None,
            metadata=metadata,
        )


class GoverningResolutionBoundaryTests(unittest.TestCase):
    def setUp(self):
        origin._reset_semantic_origin_verifiers_for_tests()

    def tearDown(self):
        origin._reset_semantic_origin_verifiers_for_tests()

    def install_origin_verifiers(self, *, github_overrides=None, live_overrides=None):
        origin._install_semantic_origin_verifiers({
            "github": IndependentOriginVerifier("github", github_overrides),
            "live_conversation": IndependentOriginVerifier("live_conversation", live_overrides),
        })

    def adapters(
        self,
        *,
        live_class="current_user_authority",
        conflict_state="NONE",
        referent_override=None,
        proposition_override=None,
        referent_scope_override=None,
        semantic_control_binding_overrides=None,
        semantic_live_binding_overrides=None,
    ):
        live = EvidenceAdapter(
            "live_conversation",
            {
                "CURRENT_TASK_CORRECTION_PERMISSION_CONSENT": live_class,
                "CONTROL_AND_GOVERNANCE": "current_user_authority",
                "SEMANTICS_PROVENANCE_CURRENTNESS": "live_observation",
                "AUTOBIOGRAPHICAL_HISTORY": "current_user_report",
            },
            conflict_state=conflict_state,
            referent_override=referent_override,
            proposition_override=proposition_override,
            referent_scope_override=referent_scope_override,
            semantic_binding_overrides=semantic_live_binding_overrides,
        )
        github = EvidenceAdapter(
            "github",
            {
                ("CONTROL_AND_GOVERNANCE", "vera-control-plane"): "control_source",
                ("CONTROL_AND_GOVERNANCE", "vera"): "source_provenance",
                ("SEMANTICS_PROVENANCE_CURRENTNESS", "vera-control-plane"): "control_source",
                ("SEMANTICS_PROVENANCE_CURRENTNESS", "semanticatlas"): "semantic_research",
                ("AUTOBIOGRAPHICAL_HISTORY", "deepmemorystorage"): "historical_autobiographical",
            },
            semantic_binding_overrides=semantic_control_binding_overrides,
        )
        return live, github, AdapterRegistry({"live_conversation": live, "github": github})

    def semantic_record(self, result):
        semantic = [
            record for record in result.governing_resolutions
            if record.prerequisite_domain == "SEMANTICS_PROVENANCE_CURRENTNESS"
        ]
        self.assertEqual(len(semantic), 1)
        return semantic[0]

    def test_executor_api_does_not_accept_naked_governing_status_map(self):
        self.assertNotIn("governing_dependency_states", inspect.signature(execute_domain_cycle).parameters)

    def test_exact_current_authority_is_resolved_inside_executor_before_dependent_io(self):
        live, github, registry = self.adapters()
        result = execute_domain_cycle(
            "CONTROL_AND_GOVERNANCE", INDEX, CONTRACT, FABRIC, registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED"},
        )
        prerequisite_reads = [
            request for request in live.reads
            if request.domain_id == "CURRENT_TASK_CORRECTION_PERMISSION_CONSENT"
        ]
        self.assertTrue(prerequisite_reads)
        self.assertEqual(prerequisite_reads[0].governing_proposition_or_effect_class, EXPECTED_PROP)
        self.assertEqual(prerequisite_reads[0].governing_referent_scope, EXPECTED_SCOPE)
        self.assertTrue(any(request.route_ref == "route:vera-control-plane" for request in github.probes))
        self.assertTrue(any(record.status == "SATISFIED" for record in result.governing_resolutions))

    def test_non_decisive_prerequisite_evidence_keeps_dependent_io_closed(self):
        _live, github, registry = self.adapters(live_class="current_user_report")
        result = execute_domain_cycle(
            "CONTROL_AND_GOVERNANCE", INDEX, CONTRACT, FABRIC, registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED"},
        )
        self.assertFalse(any(request.route_ref == "route:vera-control-plane" for request in github.probes))
        self.assertTrue(any(record.status == "UNRESOLVED" for record in result.governing_resolutions))

    def test_conflicted_prerequisite_evidence_keeps_dependent_io_closed(self):
        _live, github, registry = self.adapters(conflict_state="CONFLICT")
        result = execute_domain_cycle(
            "CONTROL_AND_GOVERNANCE", INDEX, CONTRACT, FABRIC, registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED"},
        )
        self.assertFalse(any(request.route_ref == "route:vera-control-plane" for request in github.probes))
        self.assertTrue(any(record.status == "CONFLICT" for record in result.governing_resolutions))

    def test_wrong_referent_cannot_release_dependent_io(self):
        _live, github, registry = self.adapters(referent_override="WRONG_REFERENT")
        with self.assertRaises(ValueError):
            execute_domain_cycle(
                "CONTROL_AND_GOVERNANCE", INDEX, CONTRACT, FABRIC, registry,
                privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED"},
            )
        self.assertFalse(any(request.route_ref == "route:vera-control-plane" for request in github.probes))

    def test_wrong_proposition_cannot_release_dependent_io(self):
        _live, github, registry = self.adapters(proposition_override="VERA_CURRENT_STANCE_SELF_REPORT")
        result = execute_domain_cycle(
            "CONTROL_AND_GOVERNANCE", INDEX, CONTRACT, FABRIC, registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED"},
        )
        self.assertFalse(any(request.route_ref == "route:vera-control-plane" for request in github.probes))
        self.assertFalse(any(record.status == "SATISFIED" for record in result.governing_resolutions))

    def test_wrong_referent_scope_cannot_release_dependent_io(self):
        _live, github, registry = self.adapters(referent_scope_override="VERA")
        result = execute_domain_cycle(
            "CONTROL_AND_GOVERNANCE", INDEX, CONTRACT, FABRIC, registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED"},
        )
        self.assertFalse(any(request.route_ref == "route:vera-control-plane" for request in github.probes))
        self.assertFalse(any(record.status == "SATISFIED" for record in result.governing_resolutions))

    def test_semantic_currentness_dispatch_derives_exact_governing_pair(self):
        dispatch, reason = _expected_governing_dispatch(
            "SEMANTICS_PROVENANCE_CURRENTNESS", INDEX, CONTRACT,
        )
        self.assertIsNotNone(dispatch)
        self.assertEqual(dispatch["id"], "dispatch:semantic-currentness")
        self.assertEqual(dispatch["proposition_or_effect_class"], SEMANTIC_PROP)
        self.assertEqual(dispatch["referent_scope"], SEMANTIC_SCOPE)
        self.assertEqual(dispatch["resolver_ref"], "semantic_currentness")
        self.assertIn("Exact governing proposition", reason)

    def test_exact_independently_verified_r10_semantic_currentness_releases_private_history_io(self):
        self.install_origin_verifiers()
        live, github, registry = self.adapters()
        result = execute_domain_cycle(
            "AUTOBIOGRAPHICAL_HISTORY", INDEX, CONTRACT, FABRIC, registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED", "PRIVATE_AUTOBIOGRAPHICAL"},
        )
        self.assertEqual(self.semantic_record(result).status, "SATISFIED")
        self.assertTrue(any(request.domain_id == "AUTOBIOGRAPHICAL_HISTORY" for request in [*live.reads, *github.reads]))

    def test_exact_claimant_metadata_without_independent_verifier_keeps_private_history_closed(self):
        live, github, registry = self.adapters()
        result = execute_domain_cycle(
            "AUTOBIOGRAPHICAL_HISTORY", INDEX, CONTRACT, FABRIC, registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED", "PRIVATE_AUTOBIOGRAPHICAL"},
        )
        self.assertEqual(self.semantic_record(result).status, "UNRESOLVED")
        self.assertFalse(any(request.domain_id == "AUTOBIOGRAPHICAL_HISTORY" for request in [*live.reads, *github.reads]))

    def test_wrong_manifest_git_blob_from_independent_verifier_keeps_private_history_closed(self):
        self.install_origin_verifiers(github_overrides={"git_blob": "f" * 40})
        live, github, registry = self.adapters()
        result = execute_domain_cycle(
            "AUTOBIOGRAPHICAL_HISTORY", INDEX, CONTRACT, FABRIC, registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED", "PRIVATE_AUTOBIOGRAPHICAL"},
        )
        self.assertEqual(self.semantic_record(result).status, "UNRESOLVED")
        self.assertFalse(any(request.domain_id == "AUTOBIOGRAPHICAL_HISTORY" for request in [*live.reads, *github.reads]))

    def test_wrong_owner_blob_from_independent_verifier_keeps_private_history_closed(self):
        self.install_origin_verifiers(live_overrides={"owner_git_blob": "e" * 40})
        live, github, registry = self.adapters()
        result = execute_domain_cycle(
            "AUTOBIOGRAPHICAL_HISTORY", INDEX, CONTRACT, FABRIC, registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED", "PRIVATE_AUTOBIOGRAPHICAL"},
        )
        self.assertEqual(self.semantic_record(result).status, "UNRESOLVED")
        self.assertFalse(any(request.domain_id == "AUTOBIOGRAPHICAL_HISTORY" for request in [*live.reads, *github.reads]))

    def test_live_currentness_proof_mismatch_keeps_private_history_closed(self):
        self.install_origin_verifiers(live_overrides={"currentness_state": "HISTORICAL"})
        live, github, registry = self.adapters()
        result = execute_domain_cycle(
            "AUTOBIOGRAPHICAL_HISTORY", INDEX, CONTRACT, FABRIC, registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED", "PRIVATE_AUTOBIOGRAPHICAL"},
        )
        self.assertEqual(self.semantic_record(result).status, "UNRESOLVED")
        self.assertFalse(any(request.domain_id == "AUTOBIOGRAPHICAL_HISTORY" for request in [*live.reads, *github.reads]))

    def test_fresh_r8a2_control_source_cannot_release_private_history_io(self):
        self.install_origin_verifiers()
        live, github, registry = self.adapters(
            semantic_control_binding_overrides={
                "control_release": "R8A2",
                "control_round": "R8",
                "control_manifest_sha256": "8" * 64,
            }
        )
        result = execute_domain_cycle(
            "AUTOBIOGRAPHICAL_HISTORY", INDEX, CONTRACT, FABRIC, registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED", "PRIVATE_AUTOBIOGRAPHICAL"},
        )
        self.assertEqual(self.semantic_record(result).status, "CONFLICT")
        self.assertFalse(any(request.domain_id == "AUTOBIOGRAPHICAL_HISTORY" for request in [*live.reads, *github.reads]))

    def test_live_attestation_for_different_source_commit_keeps_private_history_closed(self):
        self.install_origin_verifiers()
        live, github, registry = self.adapters(
            semantic_live_binding_overrides={"binding_source_revision": "f" * 40}
        )
        result = execute_domain_cycle(
            "AUTOBIOGRAPHICAL_HISTORY", INDEX, CONTRACT, FABRIC, registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED", "PRIVATE_AUTOBIOGRAPHICAL"},
        )
        self.assertEqual(self.semantic_record(result).status, "UNRESOLVED")
        self.assertFalse(any(request.domain_id == "AUTOBIOGRAPHICAL_HISTORY" for request in [*live.reads, *github.reads]))


if __name__ == "__main__":
    unittest.main()
