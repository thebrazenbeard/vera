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


class FakeAdapter:
    def __init__(self, provider, route_states=None, read_revision="rev-1", evidence_class="representation"):
        self.provider = provider
        self.route_states = route_states or {}
        self.read_revision = read_revision
        self.evidence_class = evidence_class
        self.probes = []
        self.reads = []

    def probe(self, request):
        self.probes.append(request)
        return AdapterProbeResult(
            provider=self.provider,
            route_ref=request.route_ref,
            state=self.route_states.get(request.route_ref, "CURRENTLY_OBSERVED_REACHABLE"),
            observed_at="2026-09-09T00:00:00Z",
            reason="fixture probe",
        )

    def evidence_class_for(self, request):
        return self.evidence_class

    def read(self, request):
        self.reads.append(request)
        return ProviderEvidenceEnvelope(
            provider=self.provider,
            locator=f"{self.provider}:{request.source_ref}",
            revision=self.read_revision,
            observed_at="2026-09-09T00:00:01Z",
            evidence_class=self.evidence_class_for(request),
            referent=request.domain_id,
            scope="RETRIEVED_ITEM",
            privacy_class=request.privacy_class,
            currentness_basis="adapter_exact_readback",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            metadata={"route_ref": request.route_ref, "source_ref": request.source_ref},
        )


class ControlGitHubAdapter(FakeAdapter):
    def evidence_class_for(self, request):
        return {
            "vera-control-plane": "control_source",
            "vera": "source_provenance",
        }.get(request.source_ref, "source_provenance")


class RuntimeCohesionExecutorTests(unittest.TestCase):
    def test_executor_probes_then_reads_currently_reachable_target(self):
        adapter = FakeAdapter("github")
        registry = AdapterRegistry({"github": adapter})
        result = execute_domain_cycle(
            "VISUAL_SELF_REPRESENTATION",
            INDEX,
            CONTRACT,
            FABRIC,
            registry,
            privacy_allowlist={"PRIVATE_REPRESENTATION"},
        )
        self.assertEqual(result.status, "EXECUTED")
        self.assertEqual(len(adapter.probes), 1)
        self.assertEqual(len(adapter.reads), 1)
        self.assertEqual(len(result.observations), 1)
        self.assertEqual(result.observations[0].evidence_class, "representation")

    def test_privacy_denial_happens_before_adapter_probe(self):
        adapter = FakeAdapter("github")
        registry = AdapterRegistry({"github": adapter})
        result = execute_domain_cycle(
            "AUTOBIOGRAPHICAL_HISTORY",
            INDEX,
            CONTRACT,
            FABRIC,
            registry,
            privacy_allowlist={"GOVERNED"},
        )
        self.assertEqual(result.status, "UNRESOLVED")
        self.assertEqual(adapter.probes, [])
        self.assertEqual(adapter.reads, [])

    def test_unreachable_probe_prevents_read(self):
        adapter = FakeAdapter("github", {"route:selfimage": "UNAVAILABLE"})
        registry = AdapterRegistry({"github": adapter})
        result = execute_domain_cycle(
            "VISUAL_SELF_REPRESENTATION",
            INDEX,
            CONTRACT,
            FABRIC,
            registry,
            privacy_allowlist={"PRIVATE_REPRESENTATION"},
        )
        self.assertEqual(result.status, "UNRESOLVED")
        self.assertEqual(len(adapter.probes), 1)
        self.assertEqual(adapter.reads, [])

    def test_unresolved_governing_prerequisite_does_not_probe_dependent_providers(self):
        live = FakeAdapter("live_conversation", evidence_class="current_user_authority")
        github = ControlGitHubAdapter("github")
        result = execute_domain_cycle(
            "CONTROL_AND_GOVERNANCE",
            INDEX,
            CONTRACT,
            FABRIC,
            AdapterRegistry({"live_conversation": live, "github": github}),
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED"},
            governing_dependency_states={},
        )
        self.assertEqual(github.probes, [])
        self.assertGreaterEqual(len(live.probes), 1)
        self.assertEqual(result.status, "EXECUTED_WITH_UNRESOLVED")
        self.assertTrue(any("HARD_PREREQUISITE_UNRESOLVED" in item for item in result.unresolved))

    def test_satisfied_governing_prerequisite_releases_dependent_providers(self):
        live = FakeAdapter("live_conversation", evidence_class="current_user_authority")
        github = ControlGitHubAdapter("github")
        result = execute_domain_cycle(
            "CONTROL_AND_GOVERNANCE",
            INDEX,
            CONTRACT,
            FABRIC,
            AdapterRegistry({"live_conversation": live, "github": github}),
            privacy_allowlist={"CONVERSATION_SCOPED", "GOVERNED"},
            governing_dependency_states={"CURRENT_TASK_CORRECTION_PERMISSION_CONSENT": "SATISFIED"},
        )
        self.assertTrue(any(request.route_ref == "route:vera-control-plane" for request in github.probes))
        self.assertTrue(any(request.route_ref == "route:vera" for request in github.probes))
        self.assertTrue(any(request.route_ref == "route:vera-control-plane" for request in github.reads))
        self.assertIn(result.status, {"EXECUTED", "EXECUTED_WITH_UNRESOLVED"})

    def test_adapter_provider_must_match_registered_route_provider(self):
        bad = FakeAdapter("supabase", evidence_class="representation")
        registry = AdapterRegistry({"github": bad})
        with self.assertRaises(ValueError):
            execute_domain_cycle(
                "VISUAL_SELF_REPRESENTATION",
                INDEX,
                CONTRACT,
                FABRIC,
                registry,
                privacy_allowlist={"PRIVATE_REPRESENTATION"},
            )

    def test_returned_item_evidence_class_must_be_within_target_capability(self):
        adapter = FakeAdapter("github", evidence_class="current_user_authority")
        registry = AdapterRegistry({"github": adapter})
        with self.assertRaises(ValueError):
            execute_domain_cycle(
                "VISUAL_SELF_REPRESENTATION",
                INDEX,
                CONTRACT,
                FABRIC,
                registry,
                privacy_allowlist={"PRIVATE_REPRESENTATION"},
            )

    def test_adapter_cannot_change_route_in_returned_metadata(self):
        class RouteSpoofAdapter(FakeAdapter):
            def read(self, request):
                envelope = super().read(request)
                return ProviderEvidenceEnvelope(
                    **{**envelope.__dict__, "metadata": {"route_ref": "route:supabase", "source_ref": request.source_ref}}
                )

        registry = AdapterRegistry({"github": RouteSpoofAdapter("github")})
        with self.assertRaises(ValueError):
            execute_domain_cycle(
                "VISUAL_SELF_REPRESENTATION",
                INDEX,
                CONTRACT,
                FABRIC,
                registry,
                privacy_allowlist={"PRIVATE_REPRESENTATION"},
            )

    def test_checkpoint_remains_pointer_only_after_execution(self):
        registry = AdapterRegistry({"github": FakeAdapter("github")})
        result = execute_domain_cycle(
            "VISUAL_SELF_REPRESENTATION",
            INDEX,
            CONTRACT,
            FABRIC,
            registry,
            privacy_allowlist={"PRIVATE_REPRESENTATION"},
        )
        checkpoint = result.checkpoint
        self.assertTrue(checkpoint["non_promotion_flag"])
        self.assertNotIn("payload", checkpoint)
        self.assertNotIn("observations", checkpoint["minimum_necessary_payload_or_pointer"])

    def test_missing_adapter_is_explicit_unresolved_not_silent_skip(self):
        result = execute_domain_cycle(
            "VISUAL_SELF_REPRESENTATION",
            INDEX,
            CONTRACT,
            FABRIC,
            AdapterRegistry({}),
            privacy_allowlist={"PRIVATE_REPRESENTATION"},
        )
        self.assertEqual(result.status, "UNRESOLVED")
        self.assertTrue(any("MISSING_ADAPTER" in item for item in result.unresolved))


if __name__ == "__main__":
    unittest.main()
