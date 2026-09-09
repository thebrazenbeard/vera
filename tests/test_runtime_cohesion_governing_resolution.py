import inspect
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

EXPECTED_PROP = "TASK_SCOPE_PERMISSION_OR_USER_CONSENT"
EXPECTED_SCOPE = "PATRICK_OR_USER_CONTROLLED_OPERATION"


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
    ):
        self.provider = provider
        self.evidence_by_request = dict(evidence_by_request)
        self.conflict_state = conflict_state
        self.referent_override = referent_override
        self.proposition_override = proposition_override
        self.referent_scope_override = referent_scope_override
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
        if request.domain_id == "CURRENT_TASK_CORRECTION_PERMISSION_CONSENT":
            metadata.update({
                "proposition_or_effect_class": self.proposition_override or EXPECTED_PROP,
                "referent_scope": self.referent_scope_override or EXPECTED_SCOPE,
            })
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
    ):
        live = EvidenceAdapter(
            "live_conversation",
            {
                "CURRENT_TASK_CORRECTION_PERMISSION_CONSENT": live_class,
                "CONTROL_AND_GOVERNANCE": "current_user_authority",
            },
            conflict_state=conflict_state,
            referent_override=referent_override,
            proposition_override=proposition_override,
            referent_scope_override=referent_scope_override,
        )
        github = EvidenceAdapter(
            "github",
            {
                ("CONTROL_AND_GOVERNANCE", "vera-control-plane"): "control_source",
                ("CONTROL_AND_GOVERNANCE", "vera"): "source_provenance",
            },
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
        self.assertTrue(any(request.domain_id == "CURRENT_TASK_CORRECTION_PERMISSION_CONSENT" for request in live.reads))
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
        self.assertTrue(any(record.status == "CONFLICT" for record in result.governing_resolutions))

    def test_wrong_referent_scope_cannot_release_dependent_io(self):
        _live, github, registry = self.adapters(referent_scope_override="VERA")
        result = execute_domain_cycle(
            "CONTROL_AND_GOVERNANCE", INDEX, CONTRACT, FABRIC, registry,
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED"},
        )
        self.assertFalse(any(request.route_ref == "route:vera-control-plane" for request in github.probes))
        self.assertTrue(any(record.status == "CONFLICT" for record in result.governing_resolutions))


if __name__ == "__main__":
    unittest.main()
