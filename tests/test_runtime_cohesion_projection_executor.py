import json
from pathlib import Path
import unittest

from runtime_cohesion.adapters import AdapterProbeResult, AdapterRegistry
from runtime_cohesion.evidence import ProviderEvidenceEnvelope
from runtime_cohesion.executor import execute_projection_cycle

ROOT = Path(__file__).resolve().parents[1]
FABRIC = json.loads((ROOT / "architecture" / "VERA_PROVIDER_FABRIC_V1.json").read_text(encoding="utf-8"))


class ProjectionAdapter:
    def __init__(self, provider, evidence_class, revision, *, probe_state="CURRENTLY_OBSERVED_REACHABLE", digest=None, missing=False, observed_at="2026-09-08T22:50:00Z"):
        self.provider = provider
        self.evidence_class = evidence_class
        self.revision = revision
        self.probe_state = probe_state
        self.digest = digest
        self.missing = missing
        self.observed_at = observed_at
        self.probes = []
        self.reads = []

    def probe(self, request):
        self.probes.append(request)
        return AdapterProbeResult(
            provider=self.provider,
            route_ref=request.route_ref,
            state=self.probe_state,
            observed_at=self.observed_at,
            reason="projection fixture probe",
        )

    def read(self, request):
        self.reads.append(request)
        if self.missing:
            return None
        return ProviderEvidenceEnvelope(
            provider=self.provider,
            locator=f"{self.provider}:{request.source_ref}",
            revision=self.revision,
            observed_at=self.observed_at,
            evidence_class=self.evidence_class,
            referent=request.domain_id,
            scope="PROJECTION_OBJECT",
            privacy_class=request.privacy_class,
            currentness_basis="projection_fixture_readback",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            content_digest=self.digest,
            metadata={"route_ref": request.route_ref, "source_ref": request.source_ref},
        )


class RuntimeCohesionProjectionExecutorTests(unittest.TestCase):
    def _run(self, source, target, *, source_ref="refs/heads/research/cee-always-active-v0.2", source_path="runtime-manifest/current.json", allowlist={"GOVERNED"}):
        return execute_projection_cycle(
            "projection:semanticatlas-github-to-supabase",
            FABRIC,
            AdapterRegistry({"github": source, "supabase": target}),
            source_ref=source_ref,
            source_path=source_path,
            privacy_allowlist=allowlist,
        )

    def test_exact_cross_provider_projection_executes_and_reconciles(self):
        source = ProjectionAdapter("github", "source_provenance", "rev-a", digest="sha256:a")
        target = ProjectionAdapter("supabase", "persisted_provider_record", "rev-a", digest="sha256:a")
        result = self._run(source, target)
        self.assertEqual(result.status, "VERIFIED_EXACT")
        self.assertEqual(result.audit.status, "VERIFIED_EXACT")
        self.assertEqual(len(result.probes), 2)
        self.assertEqual(len(source.reads), 1)
        self.assertEqual(len(target.reads), 1)
        self.assertTrue(result.checkpoint["non_promotion_flag"])

    def test_newer_target_with_wrong_revision_is_stale_not_newest_wins(self):
        source = ProjectionAdapter("github", "source_provenance", "rev-new", observed_at="2026-09-08T22:50:00Z")
        target = ProjectionAdapter("supabase", "persisted_provider_record", "rev-old", observed_at="2026-09-08T22:59:59Z")
        result = self._run(source, target)
        self.assertEqual(result.status, "STALE_PROJECTION")
        self.assertEqual(result.source_observation.revision, "rev-new")
        self.assertEqual(result.target_observation.revision, "rev-old")

    def test_in_scope_source_with_missing_target_is_absent(self):
        source = ProjectionAdapter("github", "source_provenance", "rev-a")
        target = ProjectionAdapter("supabase", "persisted_provider_record", "rev-a", missing=True)
        result = self._run(source, target)
        self.assertEqual(result.status, "ABSENT")
        self.assertIsNone(result.target_observation)

    def test_out_of_scope_source_is_not_applicable_and_does_not_probe(self):
        source = ProjectionAdapter("github", "source_provenance", "rev-a")
        target = ProjectionAdapter("supabase", "persisted_provider_record", "rev-a")
        result = self._run(source, target, source_ref="refs/heads/main", source_path="README.md")
        self.assertEqual(result.status, "NOT_APPLICABLE")
        self.assertEqual(source.probes, [])
        self.assertEqual(target.probes, [])

    def test_target_route_unavailable_is_unavailable_not_absent(self):
        source = ProjectionAdapter("github", "source_provenance", "rev-a")
        target = ProjectionAdapter("supabase", "persisted_provider_record", "rev-a", probe_state="UNAVAILABLE")
        result = self._run(source, target)
        self.assertEqual(result.status, "UNAVAILABLE")
        self.assertEqual(len(source.reads), 1)
        self.assertEqual(target.reads, [])

    def test_projection_privacy_denial_happens_before_probe(self):
        source = ProjectionAdapter("github", "source_provenance", "rev-a")
        target = ProjectionAdapter("supabase", "persisted_provider_record", "rev-a")
        result = self._run(source, target, allowlist={"WORKING_PROJECT"})
        self.assertEqual(result.status, "UNRESOLVED")
        self.assertTrue(any(item.startswith("PRIVACY_NOT_ELIGIBLE") for item in result.unresolved))
        self.assertEqual(source.probes, [])
        self.assertEqual(target.probes, [])


if __name__ == "__main__":
    unittest.main()
