import inspect
import json
from pathlib import Path
import unittest

from runtime_cohesion.adapters import AdapterProbeResult, AdapterRegistry
from runtime_cohesion.evidence import ProviderEvidenceEnvelope
from runtime_cohesion.executor import _expected_governing_dispatch, execute_domain_cycle

ROOT = Path(__file__).resolve().parents[1]
INDEX = json.loads((ROOT / "architecture" / "VERA_COHESION_INDEX_V1.json").read_text(encoding="utf-8"))
CONTRACT = json.loads((ROOT / "architecture" / "VERA_RUNTIME_CONTRACT_V1.json").read_text(encoding="utf-8"))
FABRIC = json.loads((ROOT / "architecture" / "VERA_PROVIDER_FABRIC_V1.json").read_text(encoding="utf-8"))

EXPECTED_PROP = "TASK_SCOPE_PERMISSION_OR_USER_CONSENT"
EXPECTED_SCOPE = "PATRICK_OR_USER_CONTROLLED_OPERATION"
SEMANTIC_PROP = "SEMANTIC_PROVENANCE_CURRENTNESS_STATUS"
SEMANTIC_SCOPE = "EXACT_PROPOSITION_REFERENT_SOURCE_BINDING"
MANIFEST_SHA256 = "b7c70b1ad2c3bc533c7560320fb9a03b827f3eafad6296894216d75281b8dca1"
SOURCE_IDENTITY = "github:thebrazenbeard/vera-control-plane#VERA_PROJECT_SOURCE_MANIFEST"


def exact_semantic_binding(**overrides):
    value = {
        "control_release": "R10A0",
        "control_round": "R10",
        "control_manifest_sha256": MANIFEST_SHA256,
        "binding_source_identity": SOURCE_IDENTITY,
        "binding_source_revision": MANIFEST_SHA256,
        "binding_currentness_state": "CURRENT_EXACT_R10_BINDING",
        "binding_supersession_state": "CURRENT_OBSERVATION",
    }
    value.update(overrides)
    return value


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
        if (
            request.domain_id == "SEMANTICS_PROVENANCE_CURRENTNESS"
            and evidence_class in {"control_source", "live_observation"}
        ):
            metadata.update(exact_semantic_binding(**self.semantic_binding_overrides))
        return ProviderEvidenceEnvelope(
            provider=self.provider,
            locator=f"{self.provider}:{request.domain_id}:{request.source_ref}",
            revision="governing-resolution-rev-1",
            observed_at="2026-09-09T18:10:01Z",
            evidence_class=evidence_class,
            referent=self.referent_override or request.domain_id,
            scope="RETRIEVED_ITEM",
            privacy_class=request.privacy_class,
            currentness_basis="fresh_exact_adapter_readback",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state=self.conflict_state,
            metadata=metadata,
        )


class GoverningResolutionBoundaryTests(unittest.TestCase):
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

    def test_executor_api_does_not_accept_naked_governing_status_map(self):
        self.assertNotIn("governing_dependency_states", inspect.signature(execute_domain_cycle).parameters)

    def test_exact_current_authority_is_resolved_inside_executor_before_dependent_io(self):
        live, github, registry = self.adapters()
        result = execute_domain_cycle(
            "CONTROL_AND_GOVERNANCE",
            INDEX,
            CONTRACT,
            FABRIC,
            registry,
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
        self.assertTrue(any(record.status == "UNRESOLVED" for record in result.governing_resolutions))

    def test_wrong_referent_scope_cannot_release_dependent_io(self):
        _live, github, registry = self.adapters(referent_scope_override="VERA")
        result = execute_domain_cycle(
            "CONTROL_AND_GOVERNANCE", INDEX, CONTRACT, FABRIC, registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED"},
        )
        self.assertFalse(any(request.route_ref == "route:vera-control-plane" for request in github.probes))
        self.assertFalse(any(record.status == "SATISFIED" for record in result.governing_resolutions))
        self.assertTrue(any(record.status == "UNRESOLVED" for record in result.governing_resolutions))

    def test_semantic_currentness_dispatch_derives_exact_governing_pair(self):
        dispatch, reason = _expected_governing_dispatch(
            "SEMANTICS_PROVENANCE_CURRENTNESS",
            INDEX,
            CONTRACT,
        )
        self.assertIsNotNone(dispatch)
        self.assertEqual(dispatch["id"], "dispatch:semantic-currentness")
        self.assertEqual(dispatch["proposition_or_effect_class"], SEMANTIC_PROP)
        self.assertEqual(dispatch["referent_scope"], SEMANTIC_SCOPE)
        self.assertEqual(dispatch["resolver_ref"], "semantic_currentness")
        self.assertIn("Exact governing proposition", reason)

    def test_exact_relational_r10_semantic_currentness_releases_private_history_io(self):
        live, github, registry = self.adapters()
        result = execute_domain_cycle(
            "AUTOBIOGRAPHICAL_HISTORY",
            INDEX,
            CONTRACT,
            FABRIC,
            registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED", "PRIVATE_AUTOBIOGRAPHICAL"},
        )
        semantic = [
            record for record in result.governing_resolutions
            if record.prerequisite_domain == "SEMANTICS_PROVENANCE_CURRENTNESS"
        ]
        self.assertEqual(len(semantic), 1)
        self.assertEqual(semantic[0].status, "SATISFIED")
        all_reads = [*live.reads, *github.reads]
        self.assertTrue(any(request.domain_id == "AUTOBIOGRAPHICAL_HISTORY" for request in all_reads))

    def test_fresh_r8a2_control_source_cannot_release_private_history_io(self):
        live, github, registry = self.adapters(
            semantic_control_binding_overrides={
                "control_release": "R8A2",
                "control_round": "R8",
                "control_manifest_sha256": "8" * 64,
                "binding_source_revision": "8" * 64,
            }
        )
        result = execute_domain_cycle(
            "AUTOBIOGRAPHICAL_HISTORY",
            INDEX,
            CONTRACT,
            FABRIC,
            registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED", "PRIVATE_AUTOBIOGRAPHICAL"},
        )
        semantic = [
            record for record in result.governing_resolutions
            if record.prerequisite_domain == "SEMANTICS_PROVENANCE_CURRENTNESS"
        ]
        self.assertEqual(len(semantic), 1)
        self.assertEqual(semantic[0].status, "CONFLICT")
        all_reads = [*live.reads, *github.reads]
        self.assertFalse(any(request.domain_id == "AUTOBIOGRAPHICAL_HISTORY" for request in all_reads))

    def test_live_semantic_attestation_for_different_source_cannot_release_private_history_io(self):
        live, github, registry = self.adapters(
            semantic_live_binding_overrides={"binding_source_revision": "f" * 64}
        )
        result = execute_domain_cycle(
            "AUTOBIOGRAPHICAL_HISTORY",
            INDEX,
            CONTRACT,
            FABRIC,
            registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED", "PRIVATE_AUTOBIOGRAPHICAL"},
        )
        semantic = [
            record for record in result.governing_resolutions
            if record.prerequisite_domain == "SEMANTICS_PROVENANCE_CURRENTNESS"
        ]
        self.assertEqual(len(semantic), 1)
        self.assertEqual(semantic[0].status, "CONFLICT")
        all_reads = [*live.reads, *github.reads]
        self.assertFalse(any(request.domain_id == "AUTOBIOGRAPHICAL_HISTORY" for request in all_reads))


if __name__ == "__main__":
    unittest.main()
